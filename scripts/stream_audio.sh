#!/bin/bash
# Stream audio tokenization (FFT)
# Usage: ./scripts/stream_audio.sh <audio_file>

AUDIO_FILE=${1:-input.pcm}

echo "🎵 Streaming audio FFT tokenization..."
echo "   Input: $AUDIO_FILE"
echo ""

curl -X POST http://localhost:8000/audio/stream \
  -F "file=@$AUDIO_FILE" \
  -F "sample_rate=48000" \
  -F "frame_size=2048" \
  -F "top_k=32" \
  --no-progress-meter | \
  grep -E "event:|data:" | \
  head -20

echo ""
echo "✅ Stream started (showing first 20 lines)"
