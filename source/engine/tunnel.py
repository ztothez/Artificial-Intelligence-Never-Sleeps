"""Vectorized tunnel and perspective token-stream renderers."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pygame

from timeline import H, W

Size = tuple[int, int]

TEXTURE_SIZE = 1024
TOKEN_PARTICLE_COUNT = 5_000
TOKEN_NEAR_Z = 0.42
TOKEN_FAR_Z = 18.0

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
    "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


class TunnelRenderer:
    """Full-resolution polar tunnel using flattened NumPy grids and np.take."""

    def __init__(self, tex_a: np.ndarray, tex_b: np.ndarray, size: Size = (W, H)) -> None:
        self.output_size = size
        self.width = max(2, size[0] // 2)
        self.height = max(2, size[1] // 2)
        self.size = (self.width, self.height)
        self.pixel_count = self.width * self.height

        self._tex_a = self._resample_rgb(tex_a, TEXTURE_SIZE, TEXTURE_SIZE)
        self._tex_b = self._resample_rgb(tex_b, TEXTURE_SIZE, TEXTURE_SIZE)
        self._tex_h, self._tex_w = self._tex_a.shape[:2]
        self._tex_a_flat = np.ascontiguousarray(self._tex_a.reshape(-1, 3))
        self._tex_b_flat = np.ascontiguousarray(self._tex_b.reshape(-1, 3))

        aspect = self.width / self.height
        xs = np.linspace(-aspect, aspect, self.width, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, self.height, dtype=np.float32)
        xx, yy = np.meshgrid(xs, ys, indexing="xy")
        self._x = xx.reshape(-1).astype(np.float32)
        self._y = yy.reshape(-1).astype(np.float32)
        self._base_radius = np.sqrt(self._x * self._x + self._y * self._y).astype(np.float32)
        self._base_theta = np.arctan2(self._y, self._x).astype(np.float32)

        self._idx_a = np.empty(self.pixel_count, dtype=np.intp)
        self._idx_b = np.empty(self.pixel_count, dtype=np.intp)
        self._frame_float = np.empty((self.pixel_count, 3), dtype=np.float32)
        self._frame_rgb = np.empty((self.pixel_count, 3), dtype=np.uint8)

    @staticmethod
    def _resample_rgb(arr: np.ndarray, width: int, height: int) -> np.ndarray:
        src_h, src_w = arr.shape[:2]
        ys = np.linspace(0, src_h - 1, height, dtype=np.int32)
        xs = np.linspace(0, src_w - 1, width, dtype=np.int32)
        return np.ascontiguousarray(arr[ys[:, np.newaxis], xs[np.newaxis, :], :3], dtype=np.uint8)

    def render(self, t: float, sub_bass_energy: float, texture_mix: float = 0.0) -> pygame.Surface:
        bass = np.float32(np.clip(sub_bass_energy, 0.0, 1.0))
        t32 = np.float32(t)

        melt = np.cos(
            self._base_radius * np.float32(9.0 + bass * 16.0)
            - t32 * np.float32(2.8 + bass * 7.5)
        ).astype(np.float32)
        rotation = np.float32(0.34) + bass * (np.float32(0.82) + melt * np.float32(0.18))
        speed = np.float32(1.85) + bass * (np.float32(5.15) + melt * np.float32(1.35))
        z = self._base_radius * np.float32(4.25) + np.float32(0.85)
        wrapped_depth = np.mod(z - speed * t32, np.float32(4.75)) + np.float32(0.18)
        r = np.float32(0.92) / wrapped_depth
        theta = self._base_theta + rotation * t32 + bass * melt * np.float32(0.22)

        u_float = (
            theta * np.float32(self._tex_w / (2.0 * math.pi))
            + t32 * np.float32(54.0) * speed
            + melt * bass * np.float32(66.0)
        )
        v_float = (
            r * np.float32(118.0 + bass * 76.0)
            + t32 * np.float32(self._tex_h * 0.11) * speed
            + melt * np.float32(38.0)
        )

        u_a = np.mod(u_float, self._tex_w).astype(np.int32)
        v_a = np.mod(v_float, self._tex_h).astype(np.int32)
        u_b = np.mod(u_float + melt * np.float32(31.0) + bass * np.float32(97.0), self._tex_w).astype(np.int32)
        v_b = np.mod(v_float * np.float32(1.17 + 0.16 * bass), self._tex_h).astype(np.int32)

        np.multiply(v_a, self._tex_w, out=self._idx_a, casting="unsafe")
        self._idx_a += u_a
        np.multiply(v_b, self._tex_w, out=self._idx_b, casting="unsafe")
        self._idx_b += u_b

        samples_a = np.take(self._tex_a_flat, self._idx_a, axis=0)
        samples_b = np.take(self._tex_b_flat, self._idx_b, axis=0)
        mix = np.float32(np.clip(texture_mix + 0.28 * math.sin(t * 0.67) + 0.22 * bass, 0.0, 1.0))

        self._frame_float[:] = samples_a
        self._frame_float *= np.float32(1.0) - mix
        self._frame_float += samples_b.astype(np.float32) * mix

        shade = np.clip(
            np.float32(1.18) - self._base_radius * np.float32(0.54) + r * np.float32(0.12)
            + (melt * np.float32(0.5) + np.float32(0.5)) * bass * np.float32(0.52),
            0.0,
            1.35,
        ).astype(np.float32)
        self._frame_float *= shade[:, np.newaxis]
        np.clip(self._frame_float, 0.0, 255.0, out=self._frame_float)
        self._frame_rgb[:] = self._frame_float.astype(np.uint8)

        rgb = self._frame_rgb.reshape((self.height, self.width, 3))
        small = pygame.image.frombuffer(rgb.tobytes(), self.size, "RGB")
        return pygame.transform.scale(small, self.output_size)

    @classmethod
    def from_pngs(cls, path_a: str, path_b: str, size: Size = (W, H)) -> TunnelRenderer:
        def load(path: str) -> np.ndarray:
            surf = pygame.image.load(path).convert()
            return pygame.surfarray.array3d(surf).swapaxes(0, 1)

        return cls(load(path_a), load(path_b), size=size)


class TokenStreamRenderer:
    """Vectorized 3D particle field of live monospace model tokens."""

    def __init__(self, size: Size = (W, H), particle_count: int = TOKEN_PARTICLE_COUNT) -> None:
        self.width, self.height = size
        self.size = size
        self.particle_count = particle_count
        self.center_x = self.width * 0.5
        self.center_y = self.height * 0.5
        self.focal = self.height * 0.86
        self.near_z = np.float32(TOKEN_NEAR_Z)
        self.far_z = np.float32(TOKEN_FAR_Z)
        self.depth_span = np.float32(TOKEN_FAR_Z - TOKEN_NEAR_Z)
        self.scale = max(0.62, min(self.width / 1920.0, self.height / 1080.0))

        rng = np.random.default_rng(0xA15E_EE90)
        self._base_x = rng.uniform(-7.5, 7.5, particle_count).astype(np.float32)
        self._base_y = rng.uniform(-4.2, 4.2, particle_count).astype(np.float32)
        self._base_z = rng.uniform(TOKEN_NEAR_Z, TOKEN_FAR_Z, particle_count).astype(np.float32)
        self._speed = rng.uniform(4.5, 15.5, particle_count).astype(np.float32)
        self._phase = rng.uniform(0.0, 2.0 * math.pi, particle_count).astype(np.float32)
        self._burst = rng.uniform(0.25, 1.35, particle_count).astype(np.float32)
        self._color_lane = rng.integers(0, 4, particle_count, dtype=np.int16)

        self._tokens = self._build_tokens()
        self._token_idx = rng.integers(0, len(self._tokens), particle_count, dtype=np.int16)
        self._font_sizes = [max(8, int(v * self.scale)) for v in (13, 17, 23, 31, 43)]
        self._alpha_levels = np.linspace(28, 255, 18, dtype=np.uint8)
        self._fonts: dict[int, pygame.font.Font] = {}
        self._glyph_cache: dict[tuple[int, int, int, int], pygame.Surface] = {}
        self._palette = [
            (70, 255, 170),
            (100, 220, 255),
            (230, 245, 255),
            (255, 80, 96),
        ]

    @staticmethod
    def _build_tokens() -> list[str]:
        control = ["[CLS]", "[SEP]", "[MASK]", "[PAD]", "[OVERRIDE]", "#", "##", "::", "NULL", "ptr", "tok"]
        hex_bytes = [f"0x{i:02X}" for i in range(256)]
        addresses = [f"&{i:04X}" for i in range(0x1000, 0x1100, 0x11)]
        return control + hex_bytes + addresses

    def _font(self, size: int) -> pygame.font.Font:
        cached = self._fonts.get(size)
        if cached is not None:
            return cached
        for path in FONT_CANDIDATES:
            if Path(path).exists():
                self._fonts[size] = pygame.font.Font(path, size)
                return self._fonts[size]
        self._fonts[size] = pygame.font.SysFont("monospace", size)
        return self._fonts[size]

    def _glyph(self, token_idx: int, size_idx: int, alpha_idx: int, color_idx: int) -> pygame.Surface:
        key = (token_idx, size_idx, alpha_idx, color_idx)
        cached = self._glyph_cache.get(key)
        if cached is not None:
            return cached

        token = self._tokens[token_idx]
        font = self._font(self._font_sizes[size_idx])
        surf = font.render(token, True, self._palette[color_idx]).convert_alpha()
        surf.set_alpha(int(self._alpha_levels[alpha_idx]))
        self._glyph_cache[key] = surf
        if len(self._glyph_cache) > 12_000:
            self._glyph_cache.clear()
        return surf

    def render(self, t: float, treble_transient: float) -> pygame.Surface:
        treble = np.float32(np.clip(treble_transient, 0.0, 1.0))
        t32 = np.float32(t)
        speed = self._speed * (np.float32(1.0) + treble * (np.float32(1.05) + self._burst))
        z = self.near_z + np.mod(self._base_z - t32 * speed - self.near_z, self.depth_span)
        depth_norm = np.clip((z - self.near_z) / self.depth_span, 0.0, 1.0)
        inv_z = np.reciprocal(z)

        warp = treble * np.float32(0.38)
        x = self._base_x + warp * np.sin(t32 * (np.float32(1.2) + self._burst) + self._phase)
        y = self._base_y + warp * np.cos(t32 * (np.float32(0.9) + self._burst * np.float32(0.55)) + self._phase * 1.7)

        screen_x = self.center_x + x * self.focal * inv_z
        screen_y = self.center_y + y * self.focal * inv_z
        closeness = np.float32(1.0) - depth_norm
        alpha = np.clip(
            (np.float32(26.0) + np.float32(229.0) * (closeness ** np.float32(1.65)))
            * (np.float32(0.62) + treble * (np.float32(0.95) + self._burst * np.float32(0.35))),
            0.0,
            255.0,
        )
        alpha_idx = np.clip(
            (alpha / np.float32(255.0) * np.float32(len(self._alpha_levels) - 1)).astype(np.int16),
            0,
            len(self._alpha_levels) - 1,
        )
        size_idx = np.clip((closeness * np.float32(len(self._font_sizes))).astype(np.int16), 0, len(self._font_sizes) - 1)
        color_idx = np.mod(self._color_lane + (closeness * 3.0).astype(np.int16) + int(treble * 3.0), len(self._palette))
        if 75.0 <= t < 100.0:
            red_drive = closeness + treble * self._burst * np.float32(0.35)
            color_idx = np.where(red_drive > np.float32(0.48), 3, color_idx).astype(np.int16)

        margin = int(180 * self.scale)
        visible = (
            (screen_x > -margin)
            & (screen_x < self.width + margin)
            & (screen_y > -margin)
            & (screen_y < self.height + margin)
            & (alpha > 22.0)
        )
        visible_idx = np.flatnonzero(visible)
        draw_order = visible_idx[np.argsort(z[visible_idx])[::-1]]

        surf = pygame.Surface(self.size)
        surf.fill((2, 4, 7))
        for idx in draw_order:
            glyph = self._glyph(
                int(self._token_idx[idx]),
                int(size_idx[idx]),
                int(alpha_idx[idx]),
                int(color_idx[idx]),
            )
            surf.blit(glyph, (int(screen_x[idx]), int(screen_y[idx])))
        return surf
