#!/usr/bin/env python3
"""Parallel deterministic frame dump for high-core capture machines."""

from __future__ import annotations

import argparse
import os
import sys
import time
from multiprocessing import Process
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "source"))

from demo_player import DEFAULT_HD, FrameRenderer  # noqa: E402
from engine.packaging import ffmpeg_assemble_command  # noqa: E402
from timeline import FPS, total_duration  # noqa: E402


def split_frame_ranges(frame_count: int, workers: int) -> list[tuple[int, int]]:
    workers = max(1, min(workers, frame_count))
    base, remainder = divmod(frame_count, workers)
    ranges: list[tuple[int, int]] = []
    start = 0
    for worker_idx in range(workers):
        chunk = base + (1 if worker_idx < remainder else 0)
        if chunk == 0:
            continue
        ranges.append((start, start + chunk))
        start += chunk
    return ranges


def dump_worker(
    start_frame: int,
    end_frame: int,
    frame_count: int,
    size: tuple[int, int],
    dump_dir: str,
) -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

    import pygame

    pygame.init()
    pygame.display.set_mode(size, pygame.HIDDEN)

    renderer = FrameRenderer(size, frame_count)
    renderer.warm_static_assets()

    out_dir = Path(dump_dir)
    for frame_idx in range(start_frame, end_frame):
        surf = renderer.render_frame_at(frame_idx)
        pygame.image.save(surf, str(out_dir / f"frame_{frame_idx:06d}.png"))

    pygame.quit()


def missing_frame_indices(dump_dir: Path, frame_count: int) -> list[int]:
    present = {
        int(path.stem.split("_", 1)[1])
        for path in dump_dir.glob("frame_*.png")
        if path.stem.startswith("frame_")
    }
    return [idx for idx in range(frame_count) if idx not in present]


def main() -> int:
    parser = argparse.ArgumentParser(description="Parallel deterministic frame dump")
    parser.add_argument(
        "--workers",
        type=int,
        default=min(16, os.cpu_count() or 1),
        help="Worker processes (default: min(16, cpu_count))",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help=f"Capture length in seconds (default: full timeline, {total_duration():.1f}s)",
    )
    parser.add_argument(
        "--dump-dir",
        type=Path,
        default=ROOT / "capture" / "raw_frames",
    )
    parser.add_argument(
        "--resolution",
        default=f"{DEFAULT_HD[0]}x{DEFAULT_HD[1]}",
        help="Render canvas as WIDTHxHEIGHT (default: 1920x1080)",
    )
    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers must be at least 1")

    cleaned = args.resolution.lower().replace(",", "x").replace(" ", "")
    parts = cleaned.split("x")
    if len(parts) != 2:
        parser.error("--resolution must be WIDTHxHEIGHT")
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise SystemExit("--resolution must contain integer dimensions") from exc
    if width <= 0 or height <= 0:
        parser.error("--resolution dimensions must be positive")
    size = (width, height)

    duration = total_duration() if args.duration is None else args.duration
    frame_count = int(round(duration * FPS))
    dump_dir = args.dump_dir
    dump_dir.mkdir(parents=True, exist_ok=True)

    ranges = split_frame_ranges(frame_count, args.workers)
    print(
        f"Parallel dump: {frame_count} frames / {duration:.1f}s @ {FPS}fps "
        f"on {width}x{height} with {len(ranges)} workers → {dump_dir}/"
    )
    for worker_idx, (start, end) in enumerate(ranges):
        print(f"  worker {worker_idx:2d}: frames {start:6d}..{end - 1:6d} ({end - start} frames)")

    wall_start = time.perf_counter()
    processes = [
        Process(
            target=dump_worker,
            args=(start, end, frame_count, size, str(dump_dir)),
            name=f"dump-{start}-{end}",
        )
        for start, end in ranges
    ]
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join()
        if proc.exitcode != 0:
            raise SystemExit(f"Worker {proc.name} failed with exit code {proc.exitcode}")

    elapsed = time.perf_counter() - wall_start
    written = len(list(dump_dir.glob("frame_*.png")))
    missing = missing_frame_indices(dump_dir, frame_count)

    print(f"\nDone in {elapsed:.1f}s ({frame_count / elapsed:.1f} render-fps effective)")
    print(f"Wrote {written} PNGs (expected {frame_count})")
    if missing:
        preview = ", ".join(f"{idx:06d}" for idx in missing[:20])
        suffix = "..." if len(missing) > 20 else ""
        print(f"Missing {len(missing)} frame(s): {preview}{suffix}")
        return 1

    out_mp4 = ROOT / "capture" / "compo_video.mp4"
    cmd = ffmpeg_assemble_command(dump_dir, out_mp4)
    print(f"\nAssemble 1080p60 capture:\n  {cmd}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
