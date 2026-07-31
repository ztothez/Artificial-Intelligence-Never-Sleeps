"""Approved Phase 4 candidate effects.

The functions here operate only on already-rendered base frames or crop
rectangles during their explicitly authorized windows.
"""

from __future__ import annotations

import pygame

FPS = 60

ARCHIVE_CUE_CENTERS = (22.375, 24.125)
ARCHIVE_BAND_OFFSETS = (0, -10, 7, -6, 12, -8, 5, -11, 9, -4)
ARCHIVE_SETTLE_SECONDS = 0.32


def _smoothstep(t: float) -> float:
    t = max(0.0, min(t, 1.0))
    return t * t * (3.0 - 2.0 * t)


def _archive_offset_for(base_offset: int, band_idx: int, dt: float) -> int:
    extra = (1.0 / FPS) if band_idx in (3, 7) else 0.0
    duration = ARCHIVE_SETTLE_SECONDS + extra
    if dt < 0.0 or dt > duration:
        return 0
    return int(round(base_offset * (1.0 - _smoothstep(dt / duration))))


def apply_archive_reconstruction(base: pygame.Surface, global_t: float) -> pygame.Surface:
    offsets: list[int] | None = None
    for center in ARCHIVE_CUE_CENTERS:
        dt = global_t - center
        if 0.0 <= dt <= ARCHIVE_SETTLE_SECONDS + (1.0 / FPS):
            offsets = [
                _archive_offset_for(offset, idx, dt)
                for idx, offset in enumerate(ARCHIVE_BAND_OFFSETS)
            ]
            break

    if offsets is None or not any(offsets):
        return base

    width, height = base.get_size()
    out = pygame.Surface((width, height)).convert()
    band_count = len(offsets)
    for idx, offset in enumerate(offsets):
        y0 = int(round(idx * height / band_count))
        y1 = int(round((idx + 1) * height / band_count))
        rect = pygame.Rect(0, y0, width, max(1, y1 - y0))
        out.blit(base, (offset, y0), rect)
        if offset:
            wrap_x = offset - width if offset > 0 else offset + width
            out.blit(base, (wrap_x, y0), rect)
    return out
