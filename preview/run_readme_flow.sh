#!/usr/bin/env bash
# Run the README SimpleTaskPilot flow. Without OPENAI_API_KEY it starts the
# local OpenAI stub and points the openai SDK at it via OPENAI_API_BASE.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"
STUB_PORT="${OPENAI_STUB_PORT:-8787}"

if [ -z "${OPENAI_API_KEY:-}" ]; then
  export OPENAI_API_KEY=sk-offline-stub
  export OPENAI_API_BASE="http://127.0.0.1:${STUB_PORT}/v1"
  if ! curl -fsS "http://127.0.0.1:${STUB_PORT}/health" >/dev/null 2>&1; then
    "$PYTHON" preview/openai_stub.py --port "$STUB_PORT" >/tmp/openai-stub.log 2>&1 &
    STUB_PID=$!
    trap 'kill "$STUB_PID" 2>/dev/null || true' EXIT
    for _ in $(seq 1 50); do
      curl -fsS "http://127.0.0.1:${STUB_PORT}/health" >/dev/null 2>&1 && break
      sleep 0.2
    done
  fi
  echo "Using offline OpenAI stub at ${OPENAI_API_BASE}"
fi

"$PYTHON" preview/readme_flow.py "$@"
