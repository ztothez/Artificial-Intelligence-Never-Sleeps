"""Ken Burns motion — crop rect from still image at time t."""

from __future__ import annotations

import math

from timeline import H, W


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def crop_rect(
    iw: int,
    ih: int,
    motion: str,
    t: float,
    duration: float,
    out_w: int = W,
    out_h: int = H,
) -> tuple[int, int, int, int]:
    """Return pygame subsurface rect (x, y, w, h) on cover-scaled source."""
    p = _clamp(t / max(duration, 1e-6), 0.0, 1.0)

    if motion == "zoom_in_slow":
        z = 1.0 + 0.28 * p
        cx, cy = 0.5, 0.5
    elif motion == "static_full_frame":
        z = 1.0
        cx, cy = 0.5, 0.5
    elif motion == "zoom_in":
        z = 1.0 + 0.38 * p
        cx, cy = 0.5, 0.5
    elif motion == "zoom_in_dramatic":
        z = 1.0 + 0.55 * p
        cx, cy = 0.5, 0.5
    elif motion == "zoom_in_eye":
        # Gentle push — eye PNG is 1344×768; hard zoom reads soft at 1080p
        z = 1.0 + 0.22 * p
        cx, cy = 0.5, 0.48
    elif motion == "zoom_out":
        z = 1.32 - 0.32 * p
        cx, cy = 0.5, 0.5
    elif motion == "pan_right":
        z = 1.18
        cx = 0.32 + 0.36 * p
        cy = 0.5
    elif motion == "pan_down":
        z = 1.12
        cx = 0.5
        cy = 0.32 + 0.36 * p
    elif motion == "dolly_pulse":
        z = 1.08 + 0.04 * math.sin(2 * math.pi * p * 2.5)
        cx, cy = 0.5, 0.5
    elif motion == "pan_glitch":
        z = 1.15
        cx = 0.30 + 0.40 * p
        cy = 0.5
    else:
        z = 1.08
        cx, cy = 0.5, 0.5

    cover = max(out_w / iw, out_h / ih) * z
    sw = int(iw * cover)
    sh = int(ih * cover)
    scaled_x = int(cx * sw - out_w / 2)
    scaled_y = int(cy * sh - out_h / 2)

    # Map to original image coords before scale
    x = int(scaled_x / cover)
    y = int(scaled_y / cover)
    w = int(out_w / cover)
    h = int(out_h / cover)

    x = _clamp(x, 0, max(0, iw - w))
    y = _clamp(y, 0, max(0, ih - h))
    w = min(w, iw - x)
    h = min(h, ih - y)
    return x, y, w, h
