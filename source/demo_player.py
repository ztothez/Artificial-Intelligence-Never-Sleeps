#!/usr/bin/env python3
"""Artificial Intelligence Never Sleeps - Vibe Demo engine (Assembly Summer 2026)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "source"))

from engine.audio_fft import AudioSpectrum  # noqa: E402
from engine.assets import AssetCache  # noqa: E402
from engine.packaging import ffmpeg_assemble_command  # noqa: E402
from engine.post_process import PostProcessor  # noqa: E402
from engine.renderer import SceneRenderer  # noqa: E402
from timeline import AUDIO_DIR, FPS, locate, total_duration  # noqa: E402

MUSIC_PATH = AUDIO_DIR / "music.wav"
PLAYBACK_PATH = (ROOT / "source" / "audio" / "playback.wav").resolve()
SHAKE_SEGMENTS = frozenset({"ui_access_denied", "scene05_denied_bg", "scene06_datacenter", "ui_tagline"})
DEFAULT_HD = (1920, 1080)
NATIVE_4K = (3840, 2160)
DEFAULT_DURATION = float(total_duration())
DEFAULT_FRAME_COUNT = int(round(DEFAULT_DURATION * FPS))


def compute_frame_count(duration: float | None) -> int:
    if duration is not None:
        return int(round(duration * FPS))
    return DEFAULT_FRAME_COUNT


def shake_active(seg_name: str, global_t: float) -> bool:
    if seg_name in SHAKE_SEGMENTS:
        return True
    return 44.0 <= global_t < 101.0


class FrameRenderer:
    """Deterministic single-frame renderer — shared by live player and parallel dump."""

    def __init__(self, size: tuple[int, int], frame_count: int) -> None:
        self.size = size
        self.width, self.height = size
        self.frame_count = frame_count
        self.frame_ms = 1000.0 / FPS
        self.spectrum = AudioSpectrum(MUSIC_PATH, frame_count, FPS)
        self.assets = AssetCache(size)
        self.renderer = SceneRenderer(self.assets, size)
        self.post = PostProcessor(size)

    def warm_static_assets(self) -> None:
        self.assets.warm_static_assets()

    def render_frame_at(self, frame_idx: int) -> pygame.Surface:
        global_t = frame_idx / FPS
        time_ms = frame_idx * self.frame_ms
        seg, local_t, _ = locate(global_t)
        bass = self.spectrum.bass_at_ms(time_ms)
        treble = self.spectrum.treble_at_ms(time_ms)

        base = self.renderer.render(seg, local_t, global_t, time_ms, bass, treble)
        return self.post.apply(
            base,
            time_ms=time_ms,
            sub_bass_energy=bass,
            tear_active=shake_active(seg.name, global_t) or seg.name == "ui_access_denied",
            frame_idx=frame_idx,
            global_t=global_t,
            segment_kind=seg.kind,
            segment_name=seg.name,
        )


def parse_resolution(value: str) -> tuple[int, int]:
    cleaned = value.lower().replace(",", "x").replace(" ", "")
    parts = cleaned.split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("resolution must be WIDTHxHEIGHT, for example 3840x2160")
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("resolution must contain integer dimensions") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("resolution dimensions must be positive")
    return width, height


class DemoEngine:
    """Deterministic real-time player with audio-clock synchronization."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.size = args.resolution
        self.width, self.height = self.size
        self.duration = args.duration if args.duration is not None else DEFAULT_DURATION
        self.frame_count = compute_frame_count(args.duration)
        self.frame_ms = 1000.0 / FPS
        self._frame_renderer = FrameRenderer(self.size, self.frame_count)
        self.frame_idx = 0
        self._audio_clock_enabled = False
        self._skipped_frames = 0
        self._prof: dict[str, list[float]] = defaultdict(list)

    def _time_ms(self) -> float:
        return self.frame_idx * self.frame_ms

    def _global_t(self) -> float:
        return self.frame_idx / FPS

    def render_frame(self) -> pygame.Surface:
        t0 = time.perf_counter()
        composed = self._frame_renderer.render_frame_at(self.frame_idx)
        render_ms = (time.perf_counter() - t0) * 1000.0

        if self.args.profile:
            global_t = self._global_t()
            seg, _, _ = locate(global_t)
            self._prof[f"{seg.kind}/{seg.name}"].append(render_ms)
        return composed

    def start_audio(self) -> None:
        if self.args.no_audio:
            return
        if not PLAYBACK_PATH.is_file():
            raise FileNotFoundError(
                "Required live audio master is missing: "
                f"{PLAYBACK_PATH}\n"
                "Re-extract the complete submission package; separate source-master "
                "fallback playback is intentionally disabled."
            )

        pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=2048)
        try:
            pygame.mixer.music.load(str(PLAYBACK_PATH))
        except pygame.error as exc:
            raise RuntimeError(
                f"Could not load required live audio master: {PLAYBACK_PATH}"
            ) from exc

        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(0)
        self._audio_clock_enabled = True
        print("Audio master: source/audio/playback.wav (final mix, unity gain)")
        print(f"Audio master path: {PLAYBACK_PATH}")

    def sync_to_audio(self) -> bool:
        """Return whether the current visual frame is due on the audio timeline."""
        if not self._audio_clock_enabled:
            return True
        position_ms = pygame.mixer.music.get_pos()
        if position_ms < 0:
            return True
        target_frame = min(int(position_ms * FPS / 1000.0), self.frame_count)
        if target_frame < self.frame_idx:
            return False
        if target_frame > self.frame_idx:
            self._skipped_frames += target_frame - self.frame_idx
            self.frame_idx = target_frame
        return True

    def run(self) -> int:
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        headless = self.args.headless or self.args.dump_frames
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        pygame.display.set_caption("Artificial Intelligence Never Sleeps")
        if headless:
            flags = pygame.HIDDEN
        elif self.args.fullscreen:
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
        else:
            flags = pygame.DOUBLEBUF
        screen = pygame.display.set_mode(self.size, flags)
        pygame.mouse.set_visible(False)
        self._frame_renderer.warm_static_assets()

        dump_dir = self.args.dump_dir
        if self.args.dump_frames:
            dump_dir.mkdir(parents=True, exist_ok=True)
            print(f"Frame dump → {dump_dir}/frame_%06d.png @ {FPS}fps")

        if not self.args.dump_frames:
            self.start_audio()

        clock = pygame.time.Clock()
        running = True
        screenshot_done = False
        wall_start = time.perf_counter()

        mode = "headless" if headless else ("fullscreen" if self.args.fullscreen else "windowed")
        print(
            f"Playing {self.frame_count} frames / {self.duration:.1f}s @ {FPS}fps deterministic timeline "
            f"on {self.width}x{self.height} ({mode}) - ESC to quit"
        )

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

            if not self.sync_to_audio():
                clock.tick(1000)
                continue
            if self.frame_idx >= self.frame_count:
                break

            surf = self.render_frame()

            if self.args.dump_frames:
                pygame.image.save(surf, str(dump_dir / f"frame_{self.frame_idx:06d}.png"))
            else:
                screen.blit(surf, (0, 0))
                pygame.display.flip()

            if not screenshot_done and self._global_t() >= self.args.screenshot_at:
                pygame.image.save(surf, str(self.args.screenshot))
                print(f"Screenshot → {self.args.screenshot}")
                screenshot_done = True

            if self.args.profile and self.frame_idx % FPS == 0:
                wall = time.perf_counter() - wall_start
                achieved = self.frame_idx / wall if wall > 0 else 0.0
                seg, _, _ = locate(self._global_t())
                key = f"{seg.kind}/{seg.name}"
                ms = self._prof[key][-1] if self._prof.get(key) else 0.0
                print(
                    f"  [{self._global_t():5.1f}s] {key:28s} "
                    f"render {ms:5.1f}ms  achieved {achieved:4.1f}fps  "
                    f"drift {wall - self._global_t():+.2f}s"
                )

            self.frame_idx += 1
            clock.tick(FPS)

        if self.args.dump_frames:
            out_mp4 = ROOT / "capture" / "compo.mp4"
            cmd = ffmpeg_assemble_command(dump_dir, out_mp4)
            print(f"\nAssemble 1080p60 capture:\n  {cmd}\n")

        if self.args.profile and self._prof:
            wall = time.perf_counter() - wall_start
            frames = max(self.frame_idx, 1)
            print(f"\n--- profile ({frames} frames, wall {wall:.1f}s, {frames / wall:.1f} fps) ---")
            for key in sorted(self._prof, key=lambda k: max(self._prof[k])):
                times = self._prof[key]
                over = sum(1 for t in times if t > 1000.0 / FPS)
                print(
                    f"  {key:28s} n={len(times):4d}  "
                    f"avg={sum(times) / len(times):5.1f}ms  max={max(times):5.1f}ms  "
                    f">{1000/FPS:.0f}ms: {over}"
                )

        pygame.quit()
        if self._audio_clock_enabled:
            print(f"Audio sync: {self._skipped_frames} late visual frame(s) skipped")
        print("Done.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Artificial Intelligence Never Sleeps - Vibe Demo")
    parser.add_argument("--duration", type=float, help="Stop after N seconds for smoke tests")
    parser.add_argument(
        "--resolution",
        type=parse_resolution,
        default=DEFAULT_HD,
        help="Active render/display canvas as WIDTHxHEIGHT (default: 1920x1080)",
    )
    parser.add_argument("--width", type=int, help="Override active canvas width")
    parser.add_argument("--height", type=int, help="Override active canvas height")
    parser.add_argument("--native-4k", action="store_true", help="Use 3840x2160 event-scale canvas")
    parser.add_argument("--fullscreen", dest="fullscreen", action="store_true", default=True)
    parser.add_argument("--windowed", dest="fullscreen", action="store_false")
    parser.add_argument(
        "--audio",
        dest="no_audio",
        action="store_false",
        default=True,
        help="Enable in-player audio (off by default; final mix lives in the capture video)",
    )
    parser.add_argument("--screenshot", type=Path, default=ROOT / "entry" / "screenshot.png")
    parser.add_argument("--screenshot-at", type=float, default=118.5)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument(
        "--dump-frames",
        action="store_true",
        help="Write PNG sequence to capture/raw_frames/ (deterministic 16.666ms steps)",
    )
    parser.add_argument(
        "--dump-dir",
        type=Path,
        default=ROOT / "capture" / "raw_frames",
    )
    args = parser.parse_args()
    if args.native_4k:
        args.resolution = NATIVE_4K
    if args.width is not None or args.height is not None:
        width, height = args.resolution
        width = args.width if args.width is not None else width
        height = args.height if args.height is not None else height
        if width <= 0 or height <= 0:
            parser.error("--width and --height must be positive")
        args.resolution = (width, height)
    return DemoEngine(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
