"""Deterministic music cue track and scene phase metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cue:
    time: float
    type: str
    strength: float = 1.0
    duration: float = 0.25
    name: str = ""


CUES: tuple[Cue, ...] = (
    Cue(0.25, "exposure", 0.35, 0.35, "origin_ignition"),
    Cue(4.00, "transition", 0.40, 0.45, "evolution_begin"),
    Cue(16.80, "terminal", 0.45, 0.45, "spinner_lock"),
    Cue(22.375, "memory", 0.55, 0.32, "memory_rows"),
    Cue(24.125, "memory", 0.62, 0.34, "memory_reconstruct"),
    Cue(27.325, "transition", 0.50, 0.36, "archive_commit"),
    Cue(31.425, "breach", 1.00, 0.30, "access_denied"),
    Cue(35.500, "breach", 0.72, 0.36, "denied_aftershock"),
    Cue(44.075, "terminal", 0.58, 0.28, "deploy_interrupt_1"),
    Cue(48.600, "terminal", 0.62, 0.30, "deploy_interrupt_2"),
    Cue(53.250, "particle", 0.70, 0.38, "inference_pulse"),
    Cue(57.800, "particle", 0.78, 0.38, "graph_paths"),
    Cue(60.025, "particle", 0.70, 0.38, "graph_red_seed"),
    Cue(66.225, "breach", 0.72, 0.38, "operator_signal"),
    Cue(69.625, "transition", 0.65, 0.40, "tunnel_commit"),
    Cue(74.00, "tunnel", 0.75, 0.70, "tunnel_entry"),
    Cue(79.40, "tunnel", 0.75, 0.65, "tunnel_exit"),
    Cue(81.95, "scene10", 0.70, 0.65, "scene10_stabilize"),
    Cue(83.05, "scene10", 0.85, 0.80, "scene10_contours"),
    Cue(84.55, "scene10", 1.00, 0.60, "statue_crystallize"),
    Cue(85.00, "statue", 0.80, 0.60, "statue_awaken"),
    Cue(90.00, "tokens", 0.75, 0.65, "binary_spread"),
    Cue(93.20, "tokens", 0.70, 0.45, "token_surge"),
    Cue(95.00, "terminal", 0.85, 0.70, "guardrails_collapse"),
    Cue(98.20, "breach", 0.65, 0.45, "guardrail_off"),
    Cue(103.30, "blackout", 0.65, 0.45, "signal_collapse"),
    Cue(108.30, "eye", 0.55, 0.70, "iris_seed"),
    Cue(110.30, "eye", 1.00, 0.90, "eye_ignition"),
    Cue(115.30, "tagline", 1.00, 0.80, "tagline_land"),
)

PHASE_BY_SEGMENT: dict[str, str] = {
    "scene01_origin": "origin",
    "scene02_evolution": "evolution",
    "ui_spinner": "terminal",
    "scene03_archive": "archive",
    "scene04_almost": "archive",
    "ui_access_denied": "breach",
    "scene05_denied_bg": "breach",
    "scene06_datacenter": "machine",
    "ui_deploy_terminal": "terminal",
    "scene08a_inference": "machine",
    "scene08b_graph": "machine",
    "scene07_hands": "operator",
    "scene09_pov": "network",
    "scene08_tunnel": "tunnel",
    "scene10_threshold_awareness": "consciousness",
    "scene11a_statue": "statue",
    "scene11b_binary": "binary",
    "ui_prompt_guardrails": "terminal",
    "bridge_tagline": "blackout",
    "scene12_eye": "eye",
    "ui_tagline": "tagline",
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease_out_cubic(value: float) -> float:
    t = clamp01(value)
    return 1.0 - (1.0 - t) ** 3


def cue_intensity(
    global_t: float,
    cue_type: str | None = None,
    cue_name: str | None = None,
) -> float:
    value = 0.0
    for cue in CUES:
        if cue_type is not None and cue.type != cue_type:
            continue
        if cue_name is not None and cue.name != cue_name:
            continue
        age = abs(global_t - cue.time)
        if age > cue.duration:
            continue
        envelope = ease_out_cubic(1.0 - age / max(cue.duration, 1e-6))
        value = max(value, cue.strength * envelope)
    return clamp01(value)


def cue_just_triggered(global_t: float, cue_name: str, fps: int = 60) -> bool:
    frame_time = 1.0 / fps
    return any(cue.name == cue_name and cue.time <= global_t < cue.time + frame_time for cue in CUES)


def segment_phase(segment_name: str) -> str:
    return PHASE_BY_SEGMENT.get(segment_name, "neutral")
