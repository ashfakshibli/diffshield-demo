#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT_DIR/.env.local"
DB_PATH="$ROOT_DIR/infra/diffshield_demo.sqlite3"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

if [[ "${RESET_DB:-0}" == "1" && -f "$DB_PATH" ]]; then
  rm -f "$DB_PATH"
fi

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
