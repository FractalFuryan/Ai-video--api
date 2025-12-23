"""HarmonyØ4 Audio API Tests

Tests for /audio/* endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from tokenizers.audio_fft import AudioFFTTokenizer, AudioToken


def test_audio_token():
    """AudioToken creation and serialization."""
    token = AudioToken(bin_hz=440.0, magnitude=0.5, phase=0.0)
    
    assert token.bin_hz == 440.0
    assert token.magnitude == 0.5
    assert token.phase == 0.0
    
    serialized = token.serialize()
    assert len(serialized) == 8


def test_audio_fft_tokenizer():
    """Audio FFT tokenization."""
    # Generate simple sine wave
    sr = 48000
    duration = 0.5  # 0.5 seconds
    num_samples = int(sr * duration)
    
    t = np.arange(num_samples) / sr
    sine = 0.5 * np.sin(2 * np.pi * 440 * t)
    pcm = (sine * 32767).astype(np.int16).tobytes()
    
    tok = AudioFFTTokenizer(sample_rate=sr, frame_size=2048, top_k=16)
    tokens = list(tok.encode_pcm16le_mono(pcm))
    
    assert len(tokens) > 0


def test_audio_fft_harmonic_detection():
    """Detect fundamental frequency."""
    # Pure 440 Hz sine
    sr = 48000
    duration = 1.0
    num_samples = int(sr * duration)
    
    t = np.arange(num_samples) / sr
    sine = 0.5 * np.sin(2 * np.pi * 440 * t)
    pcm = (sine * 32767).astype(np.int16).tobytes()
    
    tok = AudioFFTTokenizer(sample_rate=sr, frame_size=2048, top_k=1)
    tokens = list(tok.encode_pcm16le_mono(pcm))
    
    # Highest magnitude bin should be near 440 Hz
    if tokens:
        first_token = tokens[0]
        assert 420 < first_token.bin_hz < 460  # 440 Hz ± 20


if __name__ == "__main__":
    test_audio_token()
    test_audio_fft_tokenizer()
    test_audio_fft_harmonic_detection()
    print("✅ All audio API tests passed")
