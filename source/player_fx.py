"""Real-time demoscene post-FX (plasma, rotozoom, vignette, scanlines)."""

from __future__ import annotations

import math

import numpy as np
import pygame

# Match effects.py presets — optional vignette_strength, darken (multiply <1)
FX_PRESETS = {
    "inference": {
        "plasma_opacity": 0.72,
        "rotozoom": False,
        "vignette": True,
        "scanlines": True,
        "vignette_strength": 0.55,
    },
    "graph": {
        "plasma_opacity": 0.60,
        "rotozoom": True,
        "vignette": True,
        "scanlines": False,
        "vignette_strength": 0.53,
    },
    "evolution": {
        "plasma_opacity": 0.0,
        "rotozoom": True,
        "vignette": True,
        "scanlines": False,
        "vignette_strength": 0.70,
        "darken": 0.68,
    },
    "archive": {
        "plasma_opacity": 0.0,
        "rotozoom": False,
        "vignette": True,
        "scanlines": False,
        "vignette_strength": 0.63,
        "darken": 0.76,
    },
    "ui": {"plasma_opacity": 0.0, "rotozoom": False, "vignette": True, "scanlines": True},
}

Size = tuple[int, int]

_VIGNETTE_MASKS: dict[tuple[int, int, float], np.ndarray] = {}
_PLASMA_CACHE: dict[tuple[int, int, int], pygame.Surface] = {}


def _vignette_mask(width: int, height: int, strength: float = 0.50) -> np.ndarray:
    key = (width, height, strength)
    cached = _VIGNETTE_MASKS.get(key)
    if cached is not None:
        return cached
    xx, yy = np.mgrid[0:width, 0:height]
    cx, cy = width / 2, height / 2
    dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    floor = max(0.22, 0.35 - (strength - 0.45) * 0.25)
    mask = np.clip(1.0 - strength * (dist ** 1.6), floor, 1.0)[:, :, np.newaxis]
    _VIGNETTE_MASKS[key] = mask.astype(np.float32)
    return _VIGNETTE_MASKS[key]


def _darken(surf: pygame.Surface, factor: float) -> pygame.Surface:
    if factor >= 1.0:
        return surf
    arr = pygame.surfarray.pixels3d(surf).astype(np.float32)
    arr *= factor
    out = surf.copy()
    pygame.surfarray.blit_array(out, np.clip(arr, 0, 255).astype(np.uint8))
    del arr
    return out


def _plasma_surface(t: float, pw: int = 400, ph: int = 225) -> pygame.Surface:
    key = (int(t * 60) % 3600, pw, ph)
    cached = _PLASMA_CACHE.get(key)
    if cached is not None:
        return cached

    xs = np.linspace(0, 4 * math.pi, pw, dtype=np.float32)
    ys = np.linspace(0, 4 * math.pi, ph, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys)
    wave = (
        np.sin(X + t * 2.1)
        + np.sin(Y + t * 1.7)
        + np.sin(X + Y + t * 2.8)
        + np.sin(np.sqrt(X * X + Y * Y) + t * 1.3)
    )
    wave = (wave - wave.min()) / (wave.max() - wave.min() + 1e-6)

    hue_shift = 0.55 + 0.16 * math.sin(t * 2.0)
    r = (wave * (180 + 70 * hue_shift)).astype(np.uint8)
    g = (wave * (175 + 90 * (1 - hue_shift))).astype(np.uint8)
    b = (36 + wave * 219).astype(np.uint8)
    rgb = np.dstack([r, g, b])

    surf = pygame.image.frombuffer(rgb.tobytes(), (pw, ph), "RGB")
    _PLASMA_CACHE[key] = surf
    if len(_PLASMA_CACHE) > 120:
        _PLASMA_CACHE.pop(next(iter(_PLASMA_CACHE)))
    return surf


def _screen_blend(base: pygame.Surface, overlay: pygame.Surface, alpha: float) -> pygame.Surface:
    if alpha <= 0:
        return base
    b = pygame.surfarray.pixels3d(base)
    o = pygame.surfarray.pixels3d(overlay)
    a = np.float32(alpha)
    base_f = b.astype(np.float32)
    overlay_f = o.astype(np.float32)
    screen = 255.0 - (255.0 - base_f) * (255.0 - overlay_f) / 255.0
    out = base_f + (screen - base_f) * a
    result = base.copy()
    pygame.surfarray.blit_array(result, np.clip(out, 0, 255).astype(np.uint8))
    del b, o
    return result


def _vignette(surf: pygame.Surface, strength: float = 0.50) -> pygame.Surface:
    arr = pygame.surfarray.pixels3d(surf).astype(np.float32)
    arr *= _vignette_mask(surf.get_width(), surf.get_height(), strength)
    out = surf.copy()
    pygame.surfarray.blit_array(out, np.clip(arr, 0, 255).astype(np.uint8))
    del arr
    return out


def _scanlines(surf: pygame.Surface, step: int = 4, alpha: int = 36) -> pygame.Surface:
    out = surf.copy()
    arr = pygame.surfarray.pixels3d(out)
    rows = np.arange(0, surf.get_height(), step)
    arr[:, rows, :] = (arr[:, rows, :].astype(np.uint16) * (255 - alpha) // 255).astype(np.uint8)
    del arr
    return out


def apply_fx(base: pygame.Surface, preset: str, t: float, size: Size | None = None) -> pygame.Surface:
    if preset not in FX_PRESETS:
        return base
    cfg = FX_PRESETS[preset]
    out = base
    width, height = size or base.get_size()

    if cfg["rotozoom"]:
        # scale (not smoothscale) — fast enough for 60fps on compo hardware
        big = pygame.transform.scale(out, (int(width * 1.15), int(height * 1.15)))
        ox = int(width * 0.025 * math.sin(2 * math.pi * t / 2.8) + (big.get_width() - width) / 2)
        oy = int(height * 0.033 * math.cos(2 * math.pi * t / 3.5) + (big.get_height() - height) / 2)
        ox = max(0, min(ox, big.get_width() - width))
        oy = max(0, min(oy, big.get_height() - height))
        out = big.subsurface(pygame.Rect(ox, oy, width, height)).copy()

    if cfg["plasma_opacity"] > 0:
        plasma = _plasma_surface(t)
        plasma = pygame.transform.scale(plasma, (width, height))
        out = _screen_blend(out, plasma, cfg["plasma_opacity"])

    if cfg["vignette"]:
        out = _vignette(out, cfg.get("vignette_strength", 0.50))
    darken = cfg.get("darken", 1.0)
    if darken < 1.0:
        out = _darken(out, darken)
    if cfg["scanlines"]:
        out = _scanlines(out)
    return out
