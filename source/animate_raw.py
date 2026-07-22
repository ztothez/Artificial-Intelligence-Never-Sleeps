#!/usr/bin/env python3
"""Ken Burns + motion effects for raw FLUX keyframes."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "source" / "visuals" / "raw"
OUT_DIR = ROOT / "source" / "visuals" / "animated"

FPS = 60
W, H = 1920, 1080

# motion preset → zoompan / filter suffix
MOTIONS: dict[str, str] = {
    "zoom_in_slow": (
        "scale=8000:-1,"
        "zoompan=z='min(zoom+0.0006,1.28)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ),
    "zoom_in": (
        "scale=8000:-1,"
        "zoompan=z='min(zoom+0.001,1.38)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ),
    "zoom_in_dramatic": (
        "scale=8000:-1,"
        "zoompan=z='min(zoom+0.0025,1.55)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ),
    "zoom_in_eye": (
        "scale=8000:-1,"
        "zoompan=z='min(zoom+0.0005,1.22)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-ih*0.02'"
    ),
    "zoom_out": (
        "scale=8000:-1,"
        "zoompan=z='if(lte(on,1),1.32,max(1.001,zoom-0.0009))':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ),
    "pan_right": (
        "scale=8000:-1,"
        "zoompan=z='1.18':x='if(lte(on,1),0,min(x+1.2,iw-iw/zoom))':y='ih/2-(ih/zoom/2)'"
    ),
    "pan_down": (
        "scale=8000:-1,"
        "zoompan=z='1.12':x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min(y+0.8,ih-ih/zoom))'"
    ),
    "dolly_pulse": (
        "scale=8000:-1,"
        "zoompan=z='1.08+0.04*sin(2*PI*on/90)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ),
    "pan_glitch": (
        "scale=8000:-1,"
        "zoompan=z='1.15':x='if(lte(on,1),0,min(x+0.9,iw-iw/zoom))':y='ih/2-(ih/zoom/2)'"
    ),
    "hold": (
        "scale=8000:-1,"
        "zoompan=z='1.08':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ),
}

# Default motion per raw asset
ASSET_MOTIONS: dict[str, str] = {
    "scene02a_bigbang": "zoom_in_dramatic",
    "scene02b_stars": "zoom_out",
    "scene02c_life": "zoom_in",
    "scene02d_silicon": "dolly_pulse",
    "scene02e_neural": "zoom_in",
    "scene01_origin": "zoom_in_slow",
    "scene03_archive": "pan_glitch",
    "scene04_almost": "zoom_out",
    "scene05_denied_bg": "zoom_in_slow",
    "scene06_datacenter": "dolly_pulse",
    "scene07_hands": "pan_right",
    "scene08a_inference": "zoom_in",
    "scene08b_graph": "pan_right",
    "scene09_pov": "zoom_out",
    "scene11a_statue": "zoom_in",
    "scene11b_binary": "pan_down",
    "scene12_eye": "zoom_in_eye",
}


def build_filter(motion: str, duration: float, fps: int = FPS) -> str:
    if motion not in MOTIONS:
        raise ValueError(f"Unknown motion: {motion}")
    frames = max(1, int(duration * fps))
    zoom = f"{MOTIONS[motion]}:d={frames}:s={W}x{H}:fps={fps}"
    if motion == "pan_glitch":
        return f"{zoom},noise=alls=4:allf=t+u,format=yuv420p"
    return f"{zoom},format=yuv420p"


def animate_image(
    src: Path,
    dest: Path,
    duration: float,
    motion: str,
    fps: int = FPS,
) -> None:
    vf = build_filter(motion, duration, fps)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(src),
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-an",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def black_clip(dest: Path, duration: float, fps: int = FPS) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#08080c:s={W}x{H}:r={fps}:d={duration}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-an",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Animate raw FLUX PNGs (Ken Burns)")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--duration", type=float, default=6.0, help="Default clip length")
    parser.add_argument("--only", nargs="*", help="Stems to animate (e.g. scene01_origin)")
    parser.add_argument("--motion", help="Override motion preset for --only")
    args = parser.parse_args()

    pngs = sorted(args.raw_dir.glob("scene*.png"))
    if args.only:
        wanted = set(args.only)
        pngs = [p for p in pngs if p.stem in wanted]

    if not pngs:
        print(f"No PNGs in {args.raw_dir}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Animating {len(pngs)} → {args.out_dir}\n")

    for png in pngs:
        stem = png.stem
        motion = args.motion or ASSET_MOTIONS.get(stem, "zoom_in")
        out = args.out_dir / f"{stem}.mp4"
        print(f"  {stem}  {motion}  {args.duration}s")
        animate_image(png, out, args.duration, motion)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
