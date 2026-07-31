"""Scene composition - evolution, raw, tunnel, terminal."""

from __future__ import annotations

import numpy as np
import pygame

from animate_raw import ASSET_MOTIONS
from engine.assets import AssetCache
from engine.palette import VOID
from engine.terminal import TerminalRenderer
from engine.tunnel import TokenStreamRenderer, TunnelRenderer
from phase4_candidate_fx import apply_archive_reconstruction
from player_fx import apply_fx
from player_motions import crop_rect
from timeline import H, W

Size = tuple[int, int]

TUNNEL_TEXTURES = ("scene08a_inference", "scene08b_graph")


class SceneRenderer:
    def __init__(self, assets: AssetCache, size: Size = (W, H)) -> None:
        self.assets = assets
        self.size = size
        self.width, self.height = size
        self.terminal = TerminalRenderer(size)
        self._tunnel: TunnelRenderer | None = None
        self._token_stream: TokenStreamRenderer | None = None

    def _tunnel_renderer(self) -> TunnelRenderer:
        if self._tunnel is None:
            self._tunnel = TunnelRenderer(
                self.assets.png_array(TUNNEL_TEXTURES[0]),
                self.assets.png_array(TUNNEL_TEXTURES[1]),
                size=self.size,
            )
        return self._tunnel

    def _token_renderer(self) -> TokenStreamRenderer:
        if self._token_stream is None:
            self._token_stream = TokenStreamRenderer(self.size)
        return self._token_stream

    def render(
        self,
        seg,
        local_t: float,
        global_t: float,
        time_ms: float,
        bass: float,
        treble: float,
    ) -> pygame.Surface:
        if seg.kind == "black":
            surf = pygame.Surface(self.size)
            surf.fill(VOID)
            return surf

        if seg.kind == "terminal":
            return self.terminal.render(seg.name, local_t, seg.duration, time_ms, treble)

        if seg.kind == "evolution":
            return self._render_evolution(seg, local_t, global_t)

        if seg.kind == "tunnel":
            mix = min(1.0, local_t / max(seg.duration, 0.01))
            frame = self._tunnel_renderer().render(global_t, bass, mix)
            if seg.fx:
                frame = apply_fx(frame, seg.fx, global_t, self.size)
            return frame

        if seg.kind == "raw":
            return self._render_raw(seg, local_t, global_t)

        if seg.kind == "clip":
            # Legacy fallback — prefer terminal/tunnel in live player
            surf = pygame.Surface(self.size)
            surf.fill(VOID)
            return surf

        raise ValueError(f"Unknown segment kind: {seg.kind}")

    def _render_evolution(self, seg, local_t: float, global_t: float) -> pygame.Surface:
        names = seg.names or []
        n = len(names) - 1
        seg_dur = seg.duration / n
        i = min(int(local_t // seg_dur), n - 1)
        t = (local_t - i * seg_dur) / seg_dur
        a = self.assets.png_scaled(names[i], self.size)
        b = self.assets.png_scaled(names[i + 1], self.size)
        frame = a.copy()
        eased = t * t * (3.0 - 2.0 * t)
        b.set_alpha(int(255 * eased))
        frame.blit(b, (0, 0))
        if seg.fx:
            frame = apply_fx(frame, seg.fx, global_t, self.size)
        return frame

    def _render_raw(self, seg, local_t: float, global_t: float) -> pygame.Surface:
        motion = seg.motion or ASSET_MOTIONS.get(seg.name, "zoom_in")
        if motion == "static_full_frame":
            frame = self.assets.png_scaled(seg.name, self.size).copy()
            if seg.fx:
                frame = apply_fx(frame, seg.fx, global_t, self.size)
            return frame

        # Ken Burns on a 2× working surface so 1344×768 FLUX stills stay sharper at 1080p.
        hi = (self.width * 2, self.height * 2)
        src = self.assets.png_scaled(seg.name, hi)
        x, y, w, h = crop_rect(
            src.get_width(),
            src.get_height(),
            motion,
            local_t,
            seg.duration,
            out_w=self.width,
            out_h=self.height,
        )
        crop = src.subsurface(pygame.Rect(x, y, w, h))
        frame = pygame.transform.smoothscale(crop, self.size)
        if motion == "pan_glitch" and int(local_t * 24) % 7 == 0:
            arr = pygame.surfarray.pixels3d(frame)
            seed = int(local_t * 1000) % 9973
            rng = np.random.default_rng(seed)
            noise = rng.integers(-18, 18, arr.shape, dtype=np.int16)
            arr[:] = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            del arr
        if seg.fx:
            frame = apply_fx(frame, seg.fx, global_t, self.size)
        if seg.name == "scene03_archive":
            frame = apply_archive_reconstruction(frame, global_t)
        return frame
