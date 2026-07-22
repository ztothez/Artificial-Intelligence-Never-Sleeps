"""Pre-calculated STFT audio analysis — deterministic bass/treble curves."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import wavfile

SUB_BASS = (20, 150)
TREBLE = (2000, 5000)
HOP_MS = 16.666  # 60fps frame step


class AudioSpectrum:
    """Windowed rFFT STFT mapped to per-frame energy arrays."""

    def __init__(self, wav_path: Path, frame_count: int, fps: int = 60) -> None:
        self.fps = fps
        self.frame_count = frame_count
        self.sub_bass_energy = np.zeros(frame_count, dtype=np.float32)
        self.treble_transients = np.zeros(frame_count, dtype=np.float32)
        if not wav_path.exists():
            return
        self._analyze(wav_path)

    def _analyze(self, wav_path: Path) -> None:
        sr, data = wavfile.read(str(wav_path))
        if data.ndim > 1:
            data = data.mean(axis=1)
        data = data.astype(np.float32)
        peak = float(np.max(np.abs(data))) or 1.0
        data /= peak

        win = max(1024, int(sr * 0.046))  # ~46ms window
        hop = max(256, int(sr * HOP_MS / 1000.0))
        n_fft = 1 << (win - 1).bit_length()
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

        sub_mask = (freqs >= SUB_BASS[0]) & (freqs <= SUB_BASS[1])
        tre_mask = (freqs >= TREBLE[0]) & (freqs <= TREBLE[1])

        bass_curve: list[float] = []
        treble_curve: list[float] = []
        times_ms: list[float] = []

        for start in range(0, len(data) - win, hop):
            chunk = data[start : start + win]
            if len(chunk) < win:
                chunk = np.pad(chunk, (0, win - len(chunk)))
            windowed = chunk * np.hanning(win)
            spec = np.abs(np.fft.rfft(windowed, n=n_fft))
            bass_curve.append(float(spec[sub_mask].mean()) if sub_mask.any() else 0.0)
            treble_curve.append(float(spec[tre_mask].mean()) if tre_mask.any() else 0.0)
            times_ms.append(start / sr * 1000.0)

        if not bass_curve:
            return

        bass = np.array(bass_curve, dtype=np.float32)
        treble = np.array(treble_curve, dtype=np.float32)
        times = np.array(times_ms, dtype=np.float32)

        bass = self._normalize(bass)
        treble = self._normalize(treble)

        frame_ms = np.arange(self.frame_count, dtype=np.float32) * (1000.0 / self.fps)
        self.sub_bass_energy = np.interp(frame_ms, times, bass).astype(np.float32)
        self.treble_transients = np.interp(frame_ms, times, treble).astype(np.float32)

    @staticmethod
    def _normalize(arr: np.ndarray) -> np.ndarray:
        lo, hi = float(arr.min()), float(arr.max())
        if hi - lo < 1e-6:
            return np.zeros_like(arr)
        return (arr - lo) / (hi - lo)

    def bass_at_ms(self, time_ms: float) -> float:
        idx = int(time_ms / 1000.0 * self.fps)
        idx = max(0, min(idx, len(self.sub_bass_energy) - 1))
        return float(self.sub_bass_energy[idx])

    def treble_at_ms(self, time_ms: float) -> float:
        idx = int(time_ms / 1000.0 * self.fps)
        idx = max(0, min(idx, len(self.treble_transients) - 1))
        return float(self.treble_transients[idx])
