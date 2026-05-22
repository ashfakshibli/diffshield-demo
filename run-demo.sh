#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting DiffShield analyzer on :8001"
(
  cd "$ROOT_DIR/services/analyzer"
  python3 -m app.main
) &
ANALYZER_PID=$!

cleanup() {
  kill "$ANALYZER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting DiffShield web app on :3007"
cd "$ROOT_DIR/apps/web"
npm run dev

