"""Resolution-aware raw PNG cache with RAM outpainting."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pygame

from timeline import H, RAW_DIR, W

Size = tuple[int, int]

BLACK_MEAN_FLOOR = 18.0
BLACK_STD_FLOOR = 7.5
MAX_SIDE_CROP_FRACTION = 0.36


class AssetCache:
    """Caches raw and processed PNGs for the live renderer.

    Raw assets are normalized in RAM before they reach camera moves or tunnel
    sampling: side letterbox bars are cropped, then narrow images are extended
    with reflected horizontal borders to match the active target aspect.
    """

    def __init__(self, size: Size = (W, H), raw_dir: Path = RAW_DIR) -> None:
        self.size = size
        self.width, self.height = size
        self.target_aspect = self.width / self.height
        self.raw_dir = raw_dir
        self._paths = self._scan_raw_pngs(raw_dir)
        self._raw_surfaces: dict[str, pygame.Surface] = {}
        self._processed_arrays: dict[str, np.ndarray] = {}
        self._processed_surfaces: dict[str, pygame.Surface] = {}
        self._scaled: dict[tuple[str, Size], pygame.Surface] = {}

    @staticmethod
    def _scan_raw_pngs(raw_dir: Path) -> dict[str, Path]:
        if not raw_dir.exists():
            return {}
        return {path.stem: path for path in sorted(raw_dir.glob("*.png"))}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._paths)

    def _path_for(self, name: str) -> Path:
        path = self._paths.get(name)
        if path is None:
            path = self.raw_dir / f"{name}.png"
            if path.exists():
                self._paths[name] = path
            else:
                raise FileNotFoundError(f"Missing raw PNG asset: {path}")
        return path

    def _raw_surface(self, name: str) -> pygame.Surface:
        if name not in self._raw_surfaces:
            self._raw_surfaces[name] = pygame.image.load(str(self._path_for(name))).convert()
        return self._raw_surfaces[name]

    @staticmethod
    def _surface_to_rgb_array(surface: pygame.Surface) -> np.ndarray:
        arr = pygame.surfarray.array3d(surface)
        return np.ascontiguousarray(arr.swapaxes(0, 1)[:, :, :3])

    @staticmethod
    def _rgb_array_to_surface(arr: np.ndarray) -> pygame.Surface:
        contiguous = np.ascontiguousarray(arr[:, :, :3], dtype=np.uint8)
        return pygame.image.frombuffer(contiguous.tobytes(), (contiguous.shape[1], contiguous.shape[0]), "RGB")

    @staticmethod
    def _detect_content_columns(arr: np.ndarray) -> tuple[int, int]:
        height, width = arr.shape[:2]
        if width < 8:
            return 0, width

        rgb = arr.astype(np.float32)
        luma = rgb[:, :, 0] * 0.2126 + rgb[:, :, 1] * 0.7152 + rgb[:, :, 2] * 0.0722
        col_mean = luma.mean(axis=0)
        col_std = luma.std(axis=0)

        low_mean = max(BLACK_MEAN_FLOOR, float(np.percentile(col_mean, 2.0)) + 4.0)
        low_std = max(BLACK_STD_FLOOR, float(np.percentile(col_std, 15.0)) + 2.0)
        blackish = (col_mean <= low_mean) & (col_std <= low_std)

        max_side = int(width * MAX_SIDE_CROP_FRACTION)
        left_candidates = np.flatnonzero(~blackish[:max_side])
        right_candidates = np.flatnonzero(~blackish[width - max_side :])

        left = int(left_candidates[0]) if left_candidates.size else 0
        right = width - max_side + int(right_candidates[-1]) + 1 if right_candidates.size else width

        min_width = max(8, int(width * (1.0 - 2.0 * MAX_SIDE_CROP_FRACTION)))
        if right - left < min_width:
            return 0, width
        return max(0, left), min(width, right)

    def _crop_letterbox_bars(self, arr: np.ndarray) -> np.ndarray:
        left, right = self._detect_content_columns(arr)
        if left == 0 and right == arr.shape[1]:
            return arr
        return np.ascontiguousarray(arr[:, left:right, :])

    def _mirror_outpaint_to_aspect(self, arr: np.ndarray) -> np.ndarray:
        height, width = arr.shape[:2]
        if height <= 0 or width <= 0:
            return arr

        current_aspect = width / height
        if current_aspect >= self.target_aspect:
            return arr

        required_width = int(math.ceil(height * self.target_aspect))
        pad_total = max(0, required_width - width)
        if pad_total == 0:
            return arr

        left_pad = pad_total // 2
        right_pad = pad_total - left_pad
        pad_width = ((0, 0), (left_pad, right_pad), (0, 0))
        if width <= 1:
            return np.pad(arr, pad_width, mode="edge")
        return np.pad(arr, pad_width, mode="reflect")

    def processed_array(self, name: str) -> np.ndarray:
        if name not in self._processed_arrays:
            raw = self._surface_to_rgb_array(self._raw_surface(name))
            cropped = self._crop_letterbox_bars(raw)
            outpainted = self._mirror_outpaint_to_aspect(cropped)
            self._processed_arrays[name] = np.ascontiguousarray(outpainted, dtype=np.uint8)
        return self._processed_arrays[name]

    def png(self, name: str) -> pygame.Surface:
        if name not in self._processed_surfaces:
            self._processed_surfaces[name] = self._rgb_array_to_surface(self.processed_array(name)).convert()
        return self._processed_surfaces[name]

    def png_scaled(self, name: str, size: Size | None = None) -> pygame.Surface:
        target_size = size or self.size
        key = (name, target_size)
        if key not in self._scaled:
            self._scaled[key] = pygame.transform.smoothscale(self.png(name), target_size)
        return self._scaled[key]

    def png_array(self, name: str) -> np.ndarray:
        return self.processed_array(name)

    def warm_static_assets(self) -> None:
        for name in self._paths:
            self.processed_array(name)
