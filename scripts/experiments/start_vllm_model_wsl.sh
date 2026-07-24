#!/usr/bin/env bash
set -euo pipefail

POC_DIR="${VLLM_POC_DIR:-$HOME/knowledgechat-vllm-poc}"
VENV_DIR="${VLLM_VENV_DIR:-$POC_DIR/.venv}"
MODEL="${VLLM_MODEL:-}"
HOST="${VLLM_HOST:-0.0.0.0}"
PORT="${VLLM_PORT:-8001}"
MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.70}"
MAX_NUM_SEQS="${VLLM_MAX_NUM_SEQS:-1}"
QUANTIZATION="${VLLM_QUANTIZATION:-}"
DOWNLOAD_DIR="${VLLM_DOWNLOAD_DIR:-$HOME/.cache/huggingface}"
PID_FILE="$POC_DIR/vllm-model.pid"
LOG_FILE="$POC_DIR/vllm-model.log"

usage() {
  cat <<'EOF'
Usage: start_vllm_model_wsl.sh [options]

  --model ID                 Hugging Face model identifier (required)
  --max-model-len TOKENS     Context limit (default: 8192)
  --gpu-memory-utilization N GPU memory fraction (default: 0.70)
  --quantization FORMAT      Optional format such as awq
  --port PORT                API port (default: 8001)
  --help                     Show this help

Equivalent VLLM_* environment variables are also supported. CLI wins.
LMCache is not enabled by this helper.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="${2:?missing model identifier}"; shift 2 ;;
    --max-model-len) MAX_MODEL_LEN="${2:?missing token count}"; shift 2 ;;
    --gpu-memory-utilization)
      GPU_MEMORY_UTILIZATION="${2:?missing utilization}"; shift 2 ;;
    --quantization) QUANTIZATION="${2:?missing format}"; shift 2 ;;
    --port) PORT="${2:?missing port}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$MODEL" ]]; then
  echo "ERROR: --model or VLLM_MODEL is required." >&2
  exit 2
fi
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

mkdir -p "$POC_DIR" "$DOWNLOAD_DIR"
: >"$LOG_FILE"
rm -f "$PID_FILE"

command=(
  "$VENV_DIR/bin/vllm" serve "$MODEL"
  --host "$HOST"
  --port "$PORT"
  --dtype half
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
  --max-num-seqs "$MAX_NUM_SEQS"
  --download-dir "$DOWNLOAD_DIR"
)
if [[ -n "$QUANTIZATION" ]]; then
  command+=(--quantization "$QUANTIZATION")
fi

printf 'Command:'
printf ' %q' "${command[@]}"
printf '\n'
echo "Log: $LOG_FILE"
echo "PID file: $PID_FILE"
echo "$$" >"$PID_FILE"

export VLLM_USE_V2_MODEL_RUNNER=0
export VLLM_USE_FLASHINFER_SAMPLER=0
exec "${command[@]}" >>"$LOG_FILE" 2>&1
