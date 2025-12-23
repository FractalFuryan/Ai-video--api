#!/bin/bash
# Export video to H4MK container
# Usage: ./scripts/export_video.sh <video_file> <output_file> [master_key]

VIDEO_FILE=${1:-input.raw}
OUTPUT_FILE=${2:-output.h4mk}
MASTER_KEY=${3:-$(python3 -c "import secrets; print(secrets.token_hex(32))")}

echo "📹 Exporting video to H4MK..."
echo "   Input:  $VIDEO_FILE"
echo "   Output: $OUTPUT_FILE"
echo "   Key:    ${MASTER_KEY:0:32}..."
echo ""

curl -X POST http://localhost:8000/video/export \
  -F "file=@$VIDEO_FILE" \
  -F "block_size=524288" \
  -F "fps_hint=30" \
  -F "gop=30" \
  -F "mask=true" \
  -F "master_key_hex=$MASTER_KEY" \
  -o "$OUTPUT_FILE" \
  --progress-bar

if [ -f "$OUTPUT_FILE" ]; then
  SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
  echo "✅ Exported: $OUTPUT_FILE ($SIZE)"
else
  echo "❌ Export failed"
  exit 1
fi
