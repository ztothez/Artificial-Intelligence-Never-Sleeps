#!/usr/bin/env python3
"""Shared compo timeline — used by assembler and real-time player."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "source" / "visuals" / "raw"
UI_DIR = ROOT / "source" / "visuals" / "ui"
ANIMATED_DIR = ROOT / "source" / "visuals" / "animated"
AUDIO_DIR = ROOT / "source" / "audio"

FPS = 60
W, H = 1920, 1080
VOID = (8, 8, 12)


@dataclass
class Segment:
    kind: str  # raw | terminal | black | clip | evolution | tunnel
    name: str
    duration: float
    motion: str | None = None
    loop: bool = False
    fx: str | None = None  # inference | graph | evolution | archive | ui
    names: list[str] | None = None  # evolution keyframe stems (raw/*.png)


# Timeline v3 — 2:00 compo arc (docs/compo_strategy.md)
TIMELINE: list[Segment] = [
    Segment("raw", "scene01_origin", 4.000, "zoom_in_slow"),
    Segment(
        "evolution",
        "scene02_evolution",
        12.800,
        names=[
            "scene02a_bigbang",
            "scene02b_stars",
            "scene02c_life",
            "scene02d_silicon",
            "scene02e_neural",
        ],
        fx="evolution",
    ),
    Segment("terminal", "ui_spinner", 1.600),
    Segment("black", "bridge_01", 0.400),
    Segment("raw", "scene03_archive", 6.000, "pan_glitch", fx="archive"),
    Segment("raw", "scene04_almost", 5.200, "zoom_out"),
    Segment("terminal", "ui_access_denied", 3.000),
    Segment("raw", "scene05_denied_bg", 4.000, "zoom_in_slow"),
    Segment("raw", "scene06_datacenter", 6.000, "dolly_pulse"),
    Segment("terminal", "ui_deploy_terminal", 9.000),
    Segment("raw", "scene08a_inference", 5.000, "zoom_in", fx="inference"),
    Segment("raw", "scene08b_graph", 7.000, "pan_right", fx="graph"),
    Segment("raw", "scene07_hands", 5.000, "pan_right"),
    Segment("tunnel", "scene08_tunnel", 6.000),
    Segment("raw", "scene11b_binary", 5.000, "pan_down"),
    Segment("raw", "scene11a_statue", 5.000, "zoom_in"),
    Segment("raw", "scene09_pov", 5.000, "zoom_out"),
    Segment("terminal", "ui_prompt_guardrails", 8.300),
    Segment("black", "bridge_tagline", 12.000),
    Segment("raw", "scene12_eye", 5.000, "zoom_in_eye"),
    Segment("terminal", "ui_tagline", 7.200),  # typewriter + hold after spoken tagline ends
]


def total_duration() -> float:
    return sum(s.duration for s in TIMELINE)


def segment_starts() -> list[tuple[Segment, float]]:
    out: list[tuple[Segment, float]] = []
    t = 0.0
    for seg in TIMELINE:
        out.append((seg, t))
        t += seg.duration
    return out


def locate(time_sec: float) -> tuple[Segment, float, int]:
    """Return (segment, local_time, index) for global timeline time."""
    t = max(0.0, time_sec)
    for i, (seg, start) in enumerate(segment_starts()):
        if t < start + seg.duration:
            return seg, t - start, i
    last = TIMELINE[-1]
    return last, last.duration, len(TIMELINE) - 1


def export_json(dest: Path) -> None:
    payload = {
        "fps": FPS,
        "width": W,
        "height": H,
        "duration": total_duration(),
        "segments": [asdict(s) for s in TIMELINE],
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    export_json(ROOT / "entry" / "timeline.json")
    print(f"Wrote {ROOT / 'entry' / 'timeline.json'} ({total_duration():.1f}s)")
