"""Subtle global post-process and cue-triggered signal damage."""

from __future__ import annotations

import os

import numpy as np
import pygame

from engine.cues import cue_intensity, segment_phase
from timeline import H, W

Size = tuple[int, int]

SCANLINE_BAND_HEIGHT = 2
SCANLINE_DIM = 0.040
TEAR_THRESHOLD = 0.70
TEAR_COOLDOWN_FRAMES = 10
TEAR_MIN_BANDS = 5
TEAR_MAX_BANDS = 14
CHROMA_MAX_OFFSET_1080P = 7

PHASE5_TUNNEL_AWARENESS_FRAMES = (
    (4796, 1.00),
    (4797, 0.9066666667),
    (4798, 0.8133333333),
    (4799, 0.72),
    (4800, 0.72),
    (4801, 0.776),
    (4802, 0.832),
    (4803, 0.888),
    (4804, 0.944),
    (4805, 1.00),
)
PHASE5_EXPOSURE_BY_FRAME = dict(PHASE5_TUNNEL_AWARENESS_FRAMES)


def _scanline_dim() -> float:
    value = os.environ.get("ZTTZ_SCANLINE_DIM")
    if value is None:
        return SCANLINE_DIM
    try:
        return max(0.0, min(1.0, float(value)))
    except ValueError:
        return SCANLINE_DIM


def _scanlines_enabled() -> bool:
    return os.environ.get("ZTTZ_DISABLE_SCANLINES", "").strip().lower() not in {"1", "true", "yes", "on"}


def _phase5_transition_exposure_scale(frame_idx: int) -> float:
    return PHASE5_EXPOSURE_BY_FRAME.get(frame_idx, 1.0)


class PostProcessor:
    """Global grade plus short cue-triggered memory/chroma accents."""

    def __init__(self, size: Size = (W, H)) -> None:
        self.width, self.height = size
        self.size = size
        self.scanline_dim = _scanline_dim()
        self.scanlines_enabled = _scanlines_enabled()
        self._scanline_surface = self._build_scanline_surface(size, self.scanline_dim, self.scanlines_enabled)
        self._vignette_surface = self._build_vignette_surface(size)
        self._solid_surfaces: dict[tuple[int, int, int], pygame.Surface] = {}
        self._x_indices = np.arange(self.width, dtype=np.int32)[:, np.newaxis]
        self._tear_frames_remaining = 0
        self._tear_age = 0
        self._tear_seed = 0
        self._last_tear_frame = -TEAR_COOLDOWN_FRAMES

    @staticmethod
    def _build_scanline_surface(size: Size, dim: float = SCANLINE_DIM, enabled: bool = True) -> pygame.Surface:
        width, height = size
        mask = np.full((height, width, 3), 255, dtype=np.uint8)
        rows = np.arange(height, dtype=np.int32)
        if enabled and dim > 0.0:
            dim_rows = (rows // SCANLINE_BAND_HEIGHT) % 2 == 0
            mask[dim_rows, :, :] = int(round(255 * (1.0 - dim)))
        return pygame.image.frombuffer(np.ascontiguousarray(mask).tobytes(), size, "RGB").copy()

    @staticmethod
    def _build_vignette_surface(size: Size) -> pygame.Surface:
        width, height = size
        yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
        cx, cy = width / 2.0, height / 2.0
        dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
        # Keep projector shadows readable; this is the only global vignette.
        mask = np.clip(1.0 - 0.38 * (dist ** 1.55), 0.42, 1.0)
        rgb = np.repeat((mask[:, :, np.newaxis] * 255.0).astype(np.uint8), 3, axis=2)
        return pygame.image.frombuffer(np.ascontiguousarray(rgb).tobytes(), size, "RGB").copy()

    def _solid_surface(self, color: tuple[int, int, int]) -> pygame.Surface:
        rgb = tuple(max(0, min(255, int(channel))) for channel in color)
        if rgb not in self._solid_surfaces:
            surface = pygame.Surface(self.size)
            surface.fill(rgb)
            self._solid_surfaces[rgb] = surface
        return self._solid_surfaces[rgb]

    def _phase_grade(
        self,
        surface: pygame.Surface,
        phase: str,
        bass: float,
        exposure: float,
        exposure_scale: float = 1.0,
    ) -> None:
        mult = (255, 255, 255)
        add = (0, 0, 0)
        if phase in {"origin", "evolution", "archive"}:
            mult = (238, 246, 255)
        elif phase in {"breach", "binary"}:
            heat = min(32, int(18 + 24 * bass + 22 * exposure))
            mult = (255, 246, 240)
            add = (heat, 6, 8)
        elif phase in {"machine", "network", "tunnel", "consciousness", "statue"}:
            mult = (238, 250, 255)
        elif phase == "eye":
            mult = (255, 242, 246)
            add = (12 + int(22 * exposure), 0, 0)
        elif phase == "tagline":
            mult = (246, 246, 250)

        lift = 5 + int(10 * exposure)
        add = (
            min(255, add[0] + lift),
            min(255, add[1] + lift),
            min(255, add[2] + lift + 1),
        )
        if exposure_scale < 1.0:
            mult = tuple(max(0, min(255, int(round(channel * exposure_scale)))) for channel in mult)
            add = tuple(max(0, min(255, int(round(channel * exposure_scale)))) for channel in add)
        if mult != (255, 255, 255):
            surface.blit(self._solid_surface(mult), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if add != (0, 0, 0):
            surface.blit(self._solid_surface(add), (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def _update_tear_state(self, time_ms: float, bass: float, active: bool, frame_idx: int, cue: float) -> bool:
        if (
            active
            and (bass >= TEAR_THRESHOLD or cue > 0.35)
            and self._tear_frames_remaining <= 0
            and frame_idx - self._last_tear_frame >= TEAR_COOLDOWN_FRAMES
        ):
            seed = (frame_idx * 9973 + int(time_ms)) & 0xFFFFFFFF
            self._tear_seed = seed
            self._tear_frames_remaining = 1 + int(cue > 0.65)
            self._tear_age = 0
            self._last_tear_frame = frame_idx

        return self._tear_frames_remaining > 0

    def _apply_memory_tearing(self, surface: pygame.Surface, bass: float, cue: float) -> pygame.Surface:
        arr = pygame.surfarray.pixels3d(surface).copy()
        rng = np.random.default_rng((self._tear_seed + self._tear_age * 0x9E3779B9) & 0xFFFFFFFF)
        band_count = int(TEAR_MIN_BANDS + (TEAR_MAX_BANDS - TEAR_MIN_BANDS) * np.clip(max(bass, cue), 0.0, 1.0))
        min_band_h = max(2, self.height // 720)
        max_band_h = max(min_band_h + 1, self.height // 72)

        starts = rng.integers(0, self.height, size=band_count, dtype=np.int32)
        heights = rng.integers(min_band_h, max_band_h + 1, size=band_count, dtype=np.int32)
        max_shift = max(3, int(self.width * 0.035 * (0.45 + cue)))
        shifts = rng.integers(-max_shift, max_shift + 1, size=band_count, dtype=np.int32)

        for start, height, shift in zip(starts, heights, shifts, strict=False):
            end = min(self.height, int(start + height))
            if end <= start:
                continue
            rows = np.arange(int(start), end, dtype=np.int32)
            row_indices = rows[np.newaxis, :]
            arr[:, rows, :] = arr[(self._x_indices + int(shift)) % self.width, row_indices, :]

        self._tear_frames_remaining -= 1
        self._tear_age += 1
        out = pygame.Surface(self.size)
        pygame.surfarray.blit_array(out, arr)
        return out

    def _apply_chromatic_aberration(self, surface: pygame.Surface, strength: float) -> pygame.Surface:
        if strength <= 0.02:
            return surface
        offset = int(round(CHROMA_MAX_OFFSET_1080P * (self.height / 1080.0) * strength))
        if offset <= 0:
            return surface
        src = pygame.surfarray.pixels3d(surface).copy()
        arr = src.copy()
        arr[:, :, 0] = np.roll(src[:, :, 0], offset, axis=0)
        arr[:, :, 2] = np.roll(src[:, :, 2], -offset, axis=0)
        out = pygame.Surface(self.size)
        pygame.surfarray.blit_array(out, arr)
        return out

    def apply(
        self,
        frame: pygame.Surface,
        time_ms: float = 0.0,
        sub_bass_energy: float = 0.0,
        tear_active: bool = False,
        frame_idx: int = 0,
        global_t: float = 0.0,
        segment_kind: str = "",
        segment_name: str = "",
    ) -> pygame.Surface:
        if frame.get_size() != self.size:
            frame = pygame.transform.scale(frame, self.size)

        out = frame.copy()
        phase = segment_phase(segment_name)
        exposure = max(
            cue_intensity(global_t, "exposure"),
            cue_intensity(global_t, "transition") * 0.35,
            cue_intensity(global_t, "eye") * 0.45,
            cue_intensity(global_t, "tagline") * 0.40,
        )
        self._phase_grade(
            out,
            phase,
            np.clip(sub_bass_energy, 0.0, 1.0),
            exposure,
            _phase5_transition_exposure_scale(frame_idx),
        )
        out.blit(self._scanline_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        out.blit(self._vignette_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        tear_cue = max(cue_intensity(global_t, "breach"), cue_intensity(global_t, "terminal") * 0.5)
        if self._update_tear_state(time_ms, sub_bass_energy, tear_active, frame_idx, tear_cue):
            out = self._apply_memory_tearing(out, sub_bass_energy, tear_cue)

        chroma = max(cue_intensity(global_t, "breach"), cue_intensity(global_t, "eye") * 0.5)
        out = self._apply_chromatic_aberration(out, chroma)
        return out
