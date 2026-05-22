#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT_DIR/.env.local"
SCAN_PAYLOAD='{"useSample":true,"notes":"Automated test run"}'

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

wait_for_health() {
  local attempts=20
  local delay=1
  local response=""

  for ((i = 1; i <= attempts; i++)); do
    if response=$(curl -fsS http://127.0.0.1:8001/health 2>/dev/null); then
      echo "$response"
      return 0
    fi
    sleep "$delay"
  done

  echo "Analyzer did not become ready on http://127.0.0.1:8001/health" >&2
  return 1
}

echo "Health check"
wait_for_health
echo

echo "Start scan"
SCAN_RESPONSE=$(curl -fsS -X POST http://127.0.0.1:8001/scan \
  -H 'Content-Type: application/json' \
  -d "$SCAN_PAYLOAD")
echo "$SCAN_RESPONSE"

SCAN_ID=$(echo "$SCAN_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["scan_id"])')

echo "Fetch summary"
curl -fsS "http://127.0.0.1:8001/scan/$SCAN_ID"
echo

echo "Fetch findings"
curl -fsS "http://127.0.0.1:8001/scan/$SCAN_ID/findings"
echo
