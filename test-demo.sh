#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCAN_PAYLOAD='{"useSample":true,"notes":"Automated test run"}'

echo "Health check"
curl -s http://127.0.0.1:8001/health
echo

echo "Start scan"
SCAN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8001/scan \
  -H 'Content-Type: application/json' \
  -d "$SCAN_PAYLOAD")
echo "$SCAN_RESPONSE"

SCAN_ID=$(echo "$SCAN_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["scan_id"])')

echo "Fetch summary"
curl -s "http://127.0.0.1:8001/scan/$SCAN_ID"
echo

echo "Fetch findings"
curl -s "http://127.0.0.1:8001/scan/$SCAN_ID/findings"
echo
