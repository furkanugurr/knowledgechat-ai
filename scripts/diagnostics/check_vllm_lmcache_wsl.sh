#!/usr/bin/env bash
set -u

status() {
  local level="$1"
  shift
  printf '[%s] %s\n' "$level" "$*"
}

run_optional() {
  local label="$1"
  local command_name="$2"
  shift 2

  printf '\n--- %s ---\n' "$label"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    status WARNING "'$command_name' is not available."
    return 0
  fi

  if "$command_name" "$@"; then
    status PASS "$label completed."
  else
    status WARNING "$label returned a non-zero exit status."
  fi
}

printf '%s\n' 'KnowledgeChat AI - vLLM + LMCache WSL diagnostics'
printf '%s\n' 'Read-only collection; no packages or settings are changed.'

run_optional "Distribution" cat /etc/os-release
run_optional "Kernel" uname -a
run_optional "Python version" python3 --version
run_optional "pip version" python3 -m pip --version
run_optional "NVIDIA GPU" nvidia-smi \
  --query-gpu=name,driver_version,memory.total,memory.free,utilization.gpu \
  --format=csv,noheader
run_optional "CUDA compiler" nvcc --version
run_optional "System memory" free -h
run_optional "Disk capacity" df -h /
run_optional "Docker client" docker --version
run_optional "Docker daemon" docker info --format \
  'Server={{.ServerVersion}}; OS={{.OperatingSystem}}'

if [[ -e /usr/lib/wsl/lib/libcuda.so.1 ]]; then
  status PASS "WSL CUDA runtime bridge is visible."
else
  status WARNING "WSL CUDA runtime bridge was not found at the usual path."
fi

printf '\n%s\n' 'Diagnostics complete.'
