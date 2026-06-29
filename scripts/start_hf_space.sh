#!/usr/bin/env bash
set -euo pipefail

cd /app

uvicorn api.main:app --host 0.0.0.0 --port 8000 &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health >/dev/null; then
    break
  fi
  sleep 1
done

streamlit run src/ui/app.py \
  --server.port 7860 \
  --server.address 0.0.0.0 \
  --browser.gatherUsageStats false
