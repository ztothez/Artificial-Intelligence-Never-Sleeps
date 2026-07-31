#!/usr/bin/env python3
"""Validate and render post-process quality approval variants."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pygame

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "source"))

from demo_player import DEFAULT_FRAME_COUNT, FrameRenderer  # noqa: E402
from engine.grid_font import GridFont  # noqa: E402
from engine.post_process import PostProcessor  # noqa: E402
from timeline import FPS  # noqa: E402

SIZE = (1920, 1080)
TIMESTAMPS = [0.000, 11.000, 22.375, 53.250, 83.500]
PREVIEW_WINDOWS = [0.000, 10.500, 21.875, 52.750, 83.000]
PREVIEW_SECONDS_PER_WINDOW = 1.0
CROP_RECT = pygame.Rect(720, 405, 480, 270)


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    scanline_dim: float | None
    disable_scanlines: bool = False


VARIANTS = [
    Variant("A_055", "CORRECTED 0.055", 0.055),
    Variant("B_040", "LLAMA CHAMPIONSHIP 0.040", 0.040),
    Variant("C_OFF", "SCANLINES OFF", None, True),
]


def frame_idx(seconds: float) -> int:
    return int(round(seconds * FPS))


def stamp_label(seconds: float) -> str:
    return f"{seconds:07.3f}".replace(".", "p")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def surface_hash(surface: pygame.Surface) -> str:
    return sha256_bytes(pygame.image.tobytes(surface.convert(), "RGB"))


def set_variant_env(variant: Variant | None) -> None:
    os.environ.pop("ZTTZ_SCANLINE_DIM", None)
    os.environ.pop("ZTTZ_DISABLE_SCANLINES", None)
    if variant is None:
        return
    if variant.disable_scanlines:
        os.environ["ZTTZ_DISABLE_SCANLINES"] = "1"
    elif variant.scanline_dim is not None:
        os.environ["ZTTZ_SCANLINE_DIM"] = f"{variant.scanline_dim:.6f}"


def run_ffmpeg_encode(frames_dir: Path, output: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%06d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "15",
            "-preset",
            "slow",
            str(output),
        ],
        check=True,
    )


def extract_current_frame(current_mp4: Path, idx: int, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(current_mp4),
            "-vf",
            f"select=eq(n\\,{idx})",
            "-frames:v",
            "1",
            "-an",
            str(output),
        ],
        check=True,
    )


def text(surface: pygame.Surface, label: str, pos: tuple[int, int], font: GridFont) -> None:
    shadow = font.render(label, True, (0, 0, 0))
    fg = font.render(label, True, (230, 234, 240))
    surface.blit(shadow, (pos[0] + 2, pos[1] + 2))
    surface.blit(fg, pos)


def validate_masks(out_dir: Path) -> dict[str, str | int | float | bool]:
    set_variant_env(VARIANTS[1])
    pp = PostProcessor(SIZE)

    scan = pygame.surfarray.array3d(pp._scanline_surface)
    scan_luma = scan[:, :, 0]
    row_spread = int((scan_luma.max(axis=0) - scan_luma.min(axis=0)).max())
    vertical_only_delta = int(np.abs(scan_luma.astype(np.int16) - scan_luma[0:1, :].astype(np.int16)).max())
    expected_dim = int(round(255 * (1.0 - 0.040)))
    expected_scanline_values = (
        int(scan_luma[0, 0]) == expected_dim
        and int(scan_luma[0, 1]) == expected_dim
        and int(scan_luma[0, 2]) == 255
        and int(scan_luma[0, 3]) == 255
    )

    vig = pygame.surfarray.array3d(pp._vignette_surface)[:, :, 0]
    max_value = int(vig.max())
    center_value = int(vig[960, 540])
    max_points = np.argwhere(vig == max_value)
    max_at_center = bool(np.any((max_points[:, 0] == 960) & (max_points[:, 1] == 540)))
    brightest_point = tuple(int(v) for v in max_points[0])

    horizontal = vig[1:960, 540].astype(np.int16)
    horizontal_mirror = vig[1919:960:-1, 540].astype(np.int16)
    horizontal_symmetry_max_delta = int(np.abs(horizontal - horizontal_mirror).max())
    vertical = vig[960, 1:540].astype(np.int16)
    vertical_mirror = vig[960, 1079:540:-1].astype(np.int16)
    vertical_symmetry_max_delta = int(np.abs(vertical - vertical_mirror).max())

    renderer_a = FrameRenderer(SIZE, DEFAULT_FRAME_COUNT)
    renderer_a.warm_static_assets()
    frame_a = renderer_a.render_frame_at(frame_idx(83.5))
    renderer_b = FrameRenderer(SIZE, DEFAULT_FRAME_COUNT)
    renderer_b.warm_static_assets()
    frame_b = renderer_b.render_frame_at(frame_idx(83.5))
    deterministic_hash_a = surface_hash(frame_a)
    deterministic_hash_b = surface_hash(frame_b)
    deterministic = deterministic_hash_a == deterministic_hash_b

    results: dict[str, str | int | float | bool] = {
        "scanline_rows_uniform_across_width": row_spread == 0,
        "scanline_max_row_spread": row_spread,
        "scanline_varies_only_vertically": vertical_only_delta == 0,
        "scanline_vertical_only_delta": vertical_only_delta,
        "scanline_expected_two_row_bands": expected_scanline_values,
        "vignette_brightest_point": f"{brightest_point[0]},{brightest_point[1]}",
        "vignette_center_value": center_value,
        "vignette_max_value": max_value,
        "vignette_maximum_at_960_540": max_at_center,
        "vignette_horizontal_symmetry_max_delta": horizontal_symmetry_max_delta,
        "vignette_vertical_symmetry_max_delta": vertical_symmetry_max_delta,
        "render_deterministic": deterministic,
        "deterministic_hash_a": deterministic_hash_a,
        "deterministic_hash_b": deterministic_hash_b,
    }

    failed = [
        key
        for key in (
            "scanline_rows_uniform_across_width",
            "scanline_varies_only_vertically",
            "scanline_expected_two_row_bands",
            "vignette_maximum_at_960_540",
            "render_deterministic",
        )
        if not results[key]
    ]
    if horizontal_symmetry_max_delta > 2:
        failed.append("vignette_horizontal_symmetry")
    if vertical_symmetry_max_delta > 2:
        failed.append("vignette_vertical_symmetry")

    report = out_dir / "postprocess_quality_validation.md"
    lines = ["# Post-Process Quality Validation", ""]
    for key, value in results.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append(f"passed={'true' if not failed else 'false'}")
    if failed:
        lines.append(f"failed={', '.join(failed)}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit(f"post-process validation failed: {', '.join(failed)}")
    return results


def render_variant_frames(out_dir: Path) -> dict[str, dict[float, Path]]:
    rendered: dict[str, dict[float, Path]] = {}
    for variant in VARIANTS:
        set_variant_env(variant)
        renderer = FrameRenderer(SIZE, DEFAULT_FRAME_COUNT)
        renderer.warm_static_assets()
        frame_dir = out_dir / "still_frames" / variant.key
        frame_dir.mkdir(parents=True, exist_ok=True)
        rendered[variant.key] = {}
        for seconds in TIMESTAMPS:
            idx = frame_idx(seconds)
            path = frame_dir / f"{variant.key}_{stamp_label(seconds)}_f{idx:06d}.png"
            pygame.image.save(renderer.render_frame_at(idx), str(path))
            rendered[variant.key][seconds] = path
    set_variant_env(None)
    return rendered


def render_current_frames(current_mp4: Path, out_dir: Path) -> dict[float, Path]:
    paths: dict[float, Path] = {}
    frame_dir = out_dir / "still_frames" / "current_encoded"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for seconds in TIMESTAMPS:
        idx = frame_idx(seconds)
        path = frame_dir / f"current_{stamp_label(seconds)}_f{idx:06d}.png"
        extract_current_frame(current_mp4, idx, path)
        paths[seconds] = path
    return paths


def make_comparison_sheets(
    current: dict[float, Path],
    variants: dict[str, dict[float, Path]],
    out_dir: Path,
) -> None:
    font = GridFont(18, bold=True)
    columns = [("CURRENT ENCODED", current)] + [(variant.label, variants[variant.key]) for variant in VARIANTS]

    thumb = (420, 236)
    pad = 16
    label_h = 32
    full_sheet = pygame.Surface(
        (len(columns) * thumb[0] + (len(columns) + 1) * pad, len(TIMESTAMPS) * (thumb[1] + label_h) + pad),
        pygame.SRCALPHA,
    )
    full_sheet.fill((8, 10, 15, 255))

    crop = (480, 270)
    crop_sheet = pygame.Surface(
        (len(columns) * crop[0] + (len(columns) + 1) * pad, len(TIMESTAMPS) * (crop[1] + label_h) + pad),
        pygame.SRCALPHA,
    )
    crop_sheet.fill((8, 10, 15, 255))

    crop_dir = out_dir / "encoded_1x_crops"
    crop_dir.mkdir(parents=True, exist_ok=True)

    for row, seconds in enumerate(TIMESTAMPS):
        for col, (label, source) in enumerate(columns):
            image = pygame.image.load(str(source[seconds])).convert()
            x_full = pad + col * (thumb[0] + pad)
            y_full = pad + row * (thumb[1] + label_h)
            full_sheet.blit(pygame.transform.smoothscale(image, thumb), (x_full, y_full))
            text(full_sheet, f"{label} {seconds:06.3f}s", (x_full, y_full + thumb[1] + 6), font)

            crop_image = image.subsurface(CROP_RECT).copy()
            crop_name = f"{label.lower().replace(' ', '_')}_{stamp_label(seconds)}_f{frame_idx(seconds):06d}_1x_crop.png"
            pygame.image.save(crop_image, str(crop_dir / crop_name))
            x_crop = pad + col * (crop[0] + pad)
            y_crop = pad + row * (crop[1] + label_h)
            crop_sheet.blit(crop_image, (x_crop, y_crop))
            text(crop_sheet, f"{label} {seconds:06.3f}s", (x_crop, y_crop + crop[1] + 6), font)

    pygame.image.save(full_sheet, str(out_dir / "postprocess_fullframe_comparison.png"))
    pygame.image.save(crop_sheet, str(out_dir / "postprocess_encoded_1x_crop_comparison.png"))


def render_preview_variants(out_dir: Path) -> None:
    for variant in VARIANTS:
        set_variant_env(variant)
        renderer = FrameRenderer(SIZE, DEFAULT_FRAME_COUNT)
        renderer.warm_static_assets()
        frames_dir = out_dir / "preview_frames" / variant.key
        frames_dir.mkdir(parents=True, exist_ok=True)
        output_index = 0
        for start_seconds in PREVIEW_WINDOWS:
            start = frame_idx(start_seconds)
            count = int(round(PREVIEW_SECONDS_PER_WINDOW * FPS))
            for idx in range(start, start + count):
                pygame.image.save(renderer.render_frame_at(idx), str(frames_dir / f"frame_{output_index:06d}.png"))
                output_index += 1
        run_ffmpeg_encode(frames_dir, out_dir / f"postprocess_variant_{variant.key}_preview.mp4")
    set_variant_env(None)


def write_hash_manifest(out_dir: Path) -> None:
    lines: list[str] = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(out_dir)}")
    (out_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--current-mp4", type=Path, default=ROOT / "capture" / "compo.mp4")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    pygame.display.set_mode(SIZE, pygame.HIDDEN)

    validate_masks(args.out_dir)
    if args.validate_only:
        write_hash_manifest(args.out_dir)
        pygame.quit()
        print(f"post-process quality validation artifacts: {args.out_dir}")
        return 0

    current = render_current_frames(args.current_mp4, args.out_dir)
    variants = render_variant_frames(args.out_dir)
    make_comparison_sheets(current, variants, args.out_dir)
    render_preview_variants(args.out_dir)
    write_hash_manifest(args.out_dir)

    pygame.quit()
    print(f"post-process quality approval artifacts: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
