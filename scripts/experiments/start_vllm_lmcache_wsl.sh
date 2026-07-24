#!/usr/bin/env bash
set -euo pipefail

POC_DIR="${VLLM_POC_DIR:-$HOME/knowledgechat-vllm-poc}"
MODE="${LMCACHE_BENCHMARK_MODE:-lmcache}"
MODEL="${VLLM_MODEL:-Qwen/Qwen2.5-3B-Instruct-AWQ}"
MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.70}"
MAX_NUM_SEQS="${VLLM_MAX_NUM_SEQS:-1}"
QUANTIZATION="${VLLM_QUANTIZATION:-awq}"
CACHE_SIZE_GB="${LMCACHE_SIZE_GB:-1.0}"
VLLM_PORT="${VLLM_PORT:-8001}"
DOWNLOAD_DIR="${VLLM_DOWNLOAD_DIR:-$HOME/.cache/huggingface}"

usage() {
  cat <<'EOF'
Usage: start_vllm_lmcache_wsl.sh [options]

  --mode baseline|lmcache   Benchmark condition (default: lmcache)
  --model ID                Model identifier
  --max-model-len TOKENS    Context limit (default: 8192)
  --gpu-memory-utilization N
  --cache-size-gb N         LMCache CPU-memory limit (default: 1.0)
  --port PORT               vLLM API port (default: 8001)
  --help

The baseline and LMCache commands differ only in LMCache environment variables
and the --kv-transfer-config argument. LMCache uses the single-node in-process
connector because WSL2 does not reliably support MP CUDA IPC registration.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="${2:?missing mode}"; shift 2 ;;
    --model) MODEL="${2:?missing model}"; shift 2 ;;
    --max-model-len) MAX_MODEL_LEN="${2:?missing tokens}"; shift 2 ;;
    --gpu-memory-utilization) GPU_MEMORY_UTILIZATION="${2:?missing value}"; shift 2 ;;
    --cache-size-gb) CACHE_SIZE_GB="${2:?missing size}"; shift 2 ;;
    --port) VLLM_PORT="${2:?missing port}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ "$MODE" == "baseline" || "$MODE" == "lmcache" ]] || {
  echo "ERROR: mode must be baseline or lmcache." >&2; exit 2;
}
VLLM_PID_FILE="$POC_DIR/sprint4-vllm.pid"
LMCACHE_PID_FILE="$POC_DIR/sprint4-lmcache.pid"
VLLM_LOG="$POC_DIR/sprint4-vllm-${MODE}.log"
LMCACHE_LOG="$POC_DIR/sprint4-lmcache.log"
command -v nvidia-smi >/dev/null || {
  echo "ERROR: nvidia-smi is unavailable." >&2; exit 1;
}

VENV_DIR="$POC_DIR/.venv"
if [[ "$MODE" == "lmcache" ]]; then
  VENV_DIR="$POC_DIR/.venv-lmcache"
fi
[[ -x "$VENV_DIR/bin/vllm" ]] || {
  echo "ERROR: vLLM is unavailable at $VENV_DIR." >&2; exit 1;
}
if [[ "$MODE" == "lmcache" && ! -x "$VENV_DIR/bin/lmcache" ]]; then
  echo "ERROR: LMCache is unavailable at $VENV_DIR." >&2
  exit 1
fi

for pid_file in "$VLLM_PID_FILE" "$LMCACHE_PID_FILE"; do
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "ERROR: experimental process already runs with PID $(cat "$pid_file")." >&2
    exit 1
  fi
  rm -f "$pid_file"
done

mkdir -p "$POC_DIR" "$DOWNLOAD_DIR"
: >"$VLLM_LOG"
export VLLM_USE_V2_MODEL_RUNNER=0
export VLLM_USE_FLASHINFER_SAMPLER=0

vllm_command=(
  "$VENV_DIR/bin/python" -m vllm.entrypoints.cli.main serve "$MODEL"
  --host 0.0.0.0 --port "$VLLM_PORT"
  --dtype half --quantization "$QUANTIZATION"
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
  --max-num-seqs "$MAX_NUM_SEQS"
  --download-dir "$DOWNLOAD_DIR"
)

if [[ "$MODE" == "lmcache" ]]; then
  export LMCACHE_LOCAL_CPU=True
  export LMCACHE_MAX_LOCAL_CPU_SIZE="$CACHE_SIZE_GB"
  export LMCACHE_CHUNK_SIZE=256
  export LMCACHE_DISABLE_BANNER=1
  kv_config='{"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}'
  vllm_command+=(--kv-transfer-config "$kv_config")
fi

printf 'vLLM command:'; printf ' %q' "${vllm_command[@]}"; printf '\n'
echo "Mode: $MODE"
echo "LMCache enabled: $([[ "$MODE" == "lmcache" ]] && echo 'yes (in-process LMCacheConnectorV1)' || echo no)"
echo "LMCache CPU cache: $([[ "$MODE" == "lmcache" ]] && echo "${CACHE_SIZE_GB} GiB L1/LRU" || echo disabled)"
echo "vLLM log: $VLLM_LOG"
nohup "${vllm_command[@]}" >>"$VLLM_LOG" 2>&1 &
echo "$!" >"$VLLM_PID_FILE"
echo "vLLM PID: $(cat "$VLLM_PID_FILE")"
[[ "$MODE" == "lmcache" ]] && echo "LMCache process: embedded in vLLM PID $(cat "$VLLM_PID_FILE")"
