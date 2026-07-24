#!/usr/bin/env bash
set -euo pipefail

POC_DIR="${VLLM_POC_DIR:-$HOME/knowledgechat-vllm-poc}"
PID_FILE="$POC_DIR/vllm.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Experimental vLLM is not running (PID file not found)."
  exit 0
fi

pid="$(cat "$PID_FILE")"
if [[ ! "$pid" =~ ^[0-9]+$ ]]; then
  echo "ERROR: invalid experimental PID file: $PID_FILE" >&2
  exit 1
fi

if ! kill -0 "$pid" 2>/dev/null; then
  echo "Experimental vLLM process $pid is not active."
  rm -f "$PID_FILE"
  exit 0
fi

command_line="$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null || true)"
if [[ "$command_line" != *"vllm"*"serve"* ]]; then
  echo "ERROR: PID $pid does not appear to be the experimental vLLM server." >&2
  exit 1
fi

kill -TERM "$pid"
for _ in {1..30}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "Stopped experimental vLLM process $pid."
    exit 0
  fi
  sleep 1
done

echo "ERROR: process $pid did not stop after SIGTERM; no unrelated process was killed." >&2
exit 1
