"""HarmonyØ4 Real Audio Tokenizer: FFT Harmonic Bins

Structure-first audio tokenization via FFT magnitude/phase extraction.
NOT identity preserving. NOT synthesis-ready. Transport + structure only.

Each frame yields top-K harmonic bins as (frequency, magnitude, phase) tokens.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Iterable, Dict, Any, List


@dataclass(frozen=True)
class AudioToken:
    """Single harmonic bin token: frequency + magnitude + phase.
    
    Transport format: 8 bytes (Hz quantized + normalized mag + phase).
    """
    bin_hz: float  # Center frequency in Hz
    magnitude: float  # Normalized magnitude [0, 1]
    phase: float  # Phase in radians [-pi, pi]

    def serialize(self) -> bytes:
        """Pack to 8 bytes: freq(4) + magnitude(2) + phase(2).
        
        Format:
          - Hz: quantized to 0.1 Hz steps, clamped [0, 20000] → u32
          - Magnitude: normalized [0, 1] → u16
          - Phase: [-π, π] mapped to [0, 1] → u16
        """
        bhz = int(max(0.0, min(self.bin_hz, 20000.0)) * 10)  # 0.1 Hz steps
        mag = int(max(0.0, min(self.magnitude, 1.0)) * 65535)
        ph = int(((self.phase + np.pi) / (2 * np.pi)) * 65535)  # [-π,π] → [0,1]

        return (
            bhz.to_bytes(4, "big") +
            mag.to_bytes(2, "big") +
            ph.to_bytes(2, "big")
        )

    def metadata(self) -> Dict[str, Any]:
        """Token metadata (domain, type, structure-only assertion)."""
        return {
            "domain": "audio",
            "type": "fft-bin",
            "structure_only": True,
            "no_identity": True,
        }


class AudioFFTTokenizer:
    """FFT-based audio tokenizer (real harmonics, structure-first).
    
    Args:
        sample_rate: PCM sample rate (Hz)
        frame_size: FFT window size (samples, power of 2)
        top_k: Number of highest-magnitude bins to yield per frame
    """

    def __init__(self, sample_rate: int = 48000, frame_size: int = 2048, top_k: int = 32):
        self.sr = int(sample_rate)
        self.n = int(frame_size)
        self.top_k = int(top_k)

    def encode_pcm16le_mono(self, pcm: bytes) -> Iterable[AudioToken]:
        """Tokenize mono PCM16LE audio.
        
        Args:
            pcm: Raw PCM16LE mono bytes (2 bytes per sample, little-endian)
        
        Yields:
            AudioToken for each harmonic bin in each frame
        """
        # Unpack PCM16LE to float32 [-1, 1]
        x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

        hop = self.n // 2  # 50% overlap
        win = np.hanning(self.n).astype(np.float32)

        # Frame-by-frame STFT
        for start in range(0, max(0, len(x) - self.n + 1), hop):
            frame = x[start : start + self.n] * win
            spec = np.fft.rfft(frame)
            mags = np.abs(spec)
            phases = np.angle(spec)

            # Normalize magnitudes per-frame (structure-first, not identity)
            if mags.max() > 0:
                mags = mags / mags.max()

            # Select top-K bins by magnitude
            if len(mags) > self.top_k:
                idxs = np.argpartition(mags, -self.top_k)[-self.top_k :]
                idxs = idxs[np.argsort(mags[idxs])[::-1]]
            else:
                idxs = np.arange(len(mags))[np.argsort(mags)[::-1]]

            # Emit AudioToken for each selected bin
            for k in idxs:
                hz = float((k * self.sr) / self.n)
                mag = float(mags[k])
                ph = float(phases[k])
                yield AudioToken(bin_hz=hz, magnitude=mag, phase=ph)
