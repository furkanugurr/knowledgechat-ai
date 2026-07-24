#!/usr/bin/env bash
set -euo pipefail

POC_DIR="${VLLM_POC_DIR:-$HOME/knowledgechat-vllm-poc}"
VENV_DIR="${VLLM_VENV_DIR:-$POC_DIR/.venv}"
MODEL="${VLLM_MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
HOST="${VLLM_HOST:-0.0.0.0}"
PORT="${VLLM_PORT:-8001}"
PID_FILE="$POC_DIR/vllm.pid"
LOG_FILE="$POC_DIR/vllm.log"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi is unavailable; GPU visibility is required." >&2
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/vllm" ]]; then
  echo "ERROR: vLLM is not installed at $VENV_DIR." >&2
  exit 1
fi

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE")"
  if kill -0 "$existing_pid" 2>/dev/null; then
    echo "ERROR: experimental vLLM is already running (PID $existing_pid)." >&2
    exit 1
  fi
fi

mkdir -p "$POC_DIR"
: >"$LOG_FILE"
rm -f "$PID_FILE"
echo "Model: $MODEL"
echo "API: http://localhost:$PORT"
echo "Log: $LOG_FILE"
echo "Keep this WSL terminal/process open while the server is in use."

echo "$$" >"$PID_FILE"
export VLLM_USE_V2_MODEL_RUNNER=0
export VLLM_USE_FLASHINFER_SAMPLER=0
exec "$VENV_DIR/bin/vllm" serve "$MODEL" \
  --host "$HOST" \
  --port "$PORT" \
  --dtype half \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.70 \
  --max-num-seqs 1 \
  >>"$LOG_FILE" 2>&1
