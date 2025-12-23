#!/bin/bash
# HarmonyØ4 Development Server Launcher
# Usage: ./scripts/run_dev.sh [port]

PORT=${1:-8000}
echo "🌀 Starting HarmonyØ4 Media API on port $PORT..."
echo "📚 Docs: http://localhost:$PORT/docs"
echo ""

uvicorn api.main:app --reload --port $PORT --log-level info
