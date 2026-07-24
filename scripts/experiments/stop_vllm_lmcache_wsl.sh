#!/usr/bin/env bash
set -euo pipefail

POC_DIR="${VLLM_POC_DIR:-$HOME/knowledgechat-vllm-poc}"
stopped=0

stop_pid_file() {
  local label="$1" pid_file="$2"
  if [[ ! -f "$pid_file" ]]; then
    echo "$label: no PID file"
    return
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid"
    for _ in {1..20}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "ERROR: $label PID $pid did not stop cleanly." >&2
      return 1
    fi
    echo "$label: stopped PID $pid"
    stopped=$((stopped + 1))
  else
    echo "$label: stale PID $pid"
  fi
  rm -f "$pid_file"
}

stop_pid_file "vLLM" "$POC_DIR/sprint4-vllm.pid"
stop_pid_file "LMCache" "$POC_DIR/sprint4-lmcache.pid"
echo "Experimental processes stopped: $stopped"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
fi
