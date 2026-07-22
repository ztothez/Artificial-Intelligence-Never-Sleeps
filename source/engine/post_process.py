"""Resolution-aware CRT post-process and bass-triggered memory tearing."""

from __future__ import annotations

import numpy as np
import pygame

from timeline import H, W

Size = tuple[int, int]

SCANLINE_BAND_HEIGHT = 2
SCANLINE_DIM = 0.11
TEAR_THRESHOLD = 0.68
TEAR_COOLDOWN_FRAMES = 5
TEAR_MIN_BANDS = 12
TEAR_MAX_BANDS = 30
CHROMA_MAX_OFFSET = 30


class PostProcessor:
    """Global vectorized scanline/vignette pass plus terminal-collapse tearing."""

    def __init__(self, size: Size = (W, H)) -> None:
        self.width, self.height = size
        self.size = size
        self._scanline_mask = self._build_scanline_mask(size)
        self._vignette_mask = self._build_vignette_mask(size)
        self._x_indices = np.arange(self.width, dtype=np.int32)[:, np.newaxis]
        self._tear_frames_remaining = 0
        self._tear_age = 0
        self._tear_seed = 0
        self._last_tear_frame = -TEAR_COOLDOWN_FRAMES

    @staticmethod
    def _build_scanline_mask(size: Size) -> np.ndarray:
        width, height = size
        mask = np.ones((width, height, 3), dtype=np.float32)
        rows = np.arange(height, dtype=np.int32)
        dim_rows = (rows // SCANLINE_BAND_HEIGHT) % 2 == 0
        mask[:, dim_rows, :] *= 1.0 - SCANLINE_DIM
        return mask

    @staticmethod
    def _build_vignette_mask(size: Size) -> np.ndarray:
        width, height = size
        xx, yy = np.mgrid[0:width, 0:height].astype(np.float32)
        cx, cy = width / 2.0, height / 2.0
        dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
        mask = np.clip(1.0 - 0.54 * (dist ** 1.55), 0.24, 1.0)
        return mask[:, :, np.newaxis].astype(np.float32)

    def shake_offset(
        self,
        time_ms: float,
        bass: float,
        active: bool,
        frame_idx: int,
    ) -> tuple[int, int]:
        """Compatibility shim: viewport shaking was replaced by memory tearing."""
        return 0, 0

    def _update_tear_state(self, time_ms: float, bass: float, active: bool, frame_idx: int) -> bool:
        if (
            active
            and bass >= TEAR_THRESHOLD
            and self._tear_frames_remaining <= 0
            and frame_idx - self._last_tear_frame >= TEAR_COOLDOWN_FRAMES
        ):
            seed = (frame_idx * 9973 + int(time_ms)) & 0xFFFFFFFF
            self._tear_seed = seed
            self._tear_frames_remaining = 2 + (seed & 1)
            self._tear_age = 0
            self._last_tear_frame = frame_idx

        return self._tear_frames_remaining > 0

    def _apply_memory_tearing(self, arr: np.ndarray, bass: float) -> None:
        rng = np.random.default_rng((self._tear_seed + self._tear_age * 0x9E3779B9) & 0xFFFFFFFF)
        band_count = int(TEAR_MIN_BANDS + (TEAR_MAX_BANDS - TEAR_MIN_BANDS) * np.clip(bass, 0.0, 1.0))
        min_band_h = max(2, self.height // 360)
        max_band_h = max(min_band_h + 1, self.height // 34)

        starts = rng.integers(0, self.height, size=band_count, dtype=np.int32)
        heights = rng.integers(min_band_h, max_band_h + 1, size=band_count, dtype=np.int32)
        shifts = rng.integers(
            -max(2, self.width // 10),
            max(3, self.width // 10 + 1),
            size=band_count,
            dtype=np.int32,
        )
        xor_keys = rng.integers(0x18, 0xF0, size=(band_count, 3), dtype=np.uint8)

        row_mask = np.zeros(self.height, dtype=bool)
        row_shift = np.zeros(self.height, dtype=np.int32)
        row_xor = np.zeros((self.height, 3), dtype=np.uint8)

        for start, height, shift, xor_key in zip(starts, heights, shifts, xor_keys, strict=False):
            end = min(self.height, int(start + height))
            if end <= start:
                continue
            row_slice = slice(int(start), end)
            row_mask[row_slice] = True
            row_shift[row_slice] = int(shift)
            row_xor[row_slice] = xor_key

        rows = np.flatnonzero(row_mask)
        if rows.size == 0:
            return

        row_indices = rows[np.newaxis, :]
        shift = row_shift[rows][np.newaxis, :]
        xor = row_xor[rows][np.newaxis, :, :]

        displaced = np.empty((self.width, rows.size, 3), dtype=np.uint8)
        displaced[:, :, 0] = arr[(self._x_indices + shift) % self.width, row_indices, 2]
        displaced[:, :, 1] = arr[(self._x_indices - (shift // 2)) % self.width, row_indices, 0]
        displaced[:, :, 2] = arr[(self._x_indices + (shift * 2)) % self.width, row_indices, 1]

        np.bitwise_xor(displaced, xor, out=displaced)
        luma = (
            (
                displaced[:, :, 0].astype(np.uint16) * 3
                + displaced[:, :, 1].astype(np.uint16) * 5
                + displaced[:, :, 2].astype(np.uint16) * 2
            )
            // 10
        ).astype(np.uint8)
        displaced[:, :, 0] = np.bitwise_xor(displaced[:, :, 0], luma >> 1)
        displaced[:, :, 1] = np.maximum(displaced[:, :, 1], luma)
        displaced[:, :, 2] = np.bitwise_xor(displaced[:, :, 2], np.left_shift(luma, 1))

        arr[:, rows, :] = displaced
        self._tear_frames_remaining -= 1
        self._tear_age += 1

    def _apply_phase_grade(self, arr: np.ndarray, global_t: float, bass: float) -> None:
        if global_t < 45.0:
            arr *= np.array([0.88, 0.96, 1.10], dtype=np.float32)
        elif global_t < 75.0:
            heat = np.float32(np.clip(bass, 0.0, 1.0))
            arr *= np.array([1.08 + heat * 0.32, 0.92 + heat * 0.06, 0.82], dtype=np.float32)
            arr[:, :, 0] += heat * np.float32(22.0)
            arr[:, :, 1] += heat * np.float32(8.0)
        elif global_t < 100.0:
            heat = np.float32(np.clip(bass, 0.0, 1.0))
            arr *= np.array([1.18 + heat * 0.22, 0.82, 0.90], dtype=np.float32)
        else:
            arr *= np.float32(0.62)

    def _apply_chromatic_aberration(self, arr: np.ndarray, global_t: float, bass: float) -> None:
        if not 75.0 <= global_t < 100.0:
            return
        phase = np.clip((global_t - 75.0) / 25.0, 0.0, 1.0)
        offset = int(round(CHROMA_MAX_OFFSET * phase * (0.35 + 0.65 * np.clip(bass, 0.0, 1.0))))
        if offset <= 0:
            return
        src = arr.copy()
        arr[:, :, 0] = np.roll(src[:, :, 0], offset, axis=0)
        arr[:, :, 2] = np.roll(src[:, :, 2], -offset, axis=0)

    def _isolate_terminal_green(self, arr: np.ndarray) -> None:
        gray = (
            arr[:, :, 0].astype(np.uint16) * 3
            + arr[:, :, 1].astype(np.uint16) * 6
            + arr[:, :, 2].astype(np.uint16)
        ) // 10
        green_mask = (
            (arr[:, :, 1] > arr[:, :, 0] * 1.18)
            & (arr[:, :, 1] > arr[:, :, 2] * 1.10)
            & (arr[:, :, 1] > 72)
        )
        desat = np.empty_like(arr)
        desat[:, :, 0] = (gray * 0.18).astype(np.uint8)
        desat[:, :, 1] = (gray * 0.28).astype(np.uint8)
        desat[:, :, 2] = (gray * 0.24).astype(np.uint8)
        arr[~green_mask] = desat[~green_mask]

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
            frame = pygame.transform.smoothscale(frame, self.size)

        screen_array = pygame.surfarray.pixels3d(frame).astype(np.float32, copy=True)
        screen_array *= self._scanline_mask
        screen_array *= self._vignette_mask
        self._apply_phase_grade(screen_array, global_t, sub_bass_energy)
        out_array = np.clip(screen_array, 0.0, 255.0).astype(np.uint8)

        if self._update_tear_state(time_ms, sub_bass_energy, tear_active, frame_idx):
            self._apply_memory_tearing(out_array, sub_bass_energy)
        self._apply_chromatic_aberration(out_array, global_t, sub_bass_energy)
        if global_t >= 100.0 and segment_kind == "raw" and segment_name == "scene12_eye":
            self._isolate_terminal_green(out_array)

        out = pygame.Surface(self.size)
        pygame.surfarray.blit_array(out, out_array)
        return out
