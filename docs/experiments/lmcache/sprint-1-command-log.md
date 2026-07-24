# Experimental Sprint 1 command log

Date: 2026-07-24  
Branch: `experiment/sprint-1-vllm-lmcache-feasibility`

Secret values are intentionally omitted. No production configuration, Ollama
installation, model, or CUDA driver was changed.

## Repository preparation

```text
git status --short --branch
git fetch origin
git pull --ff-only origin main
git rev-parse HEAD
git rev-parse origin/main
git switch -c experiment/sprint-1-vllm-lmcache-feasibility
```

Result: clean `main` matched `origin/main` at
`ca764ea140aa5a6394160d7a0c47a564ebaa8949`; the experiment branch was created.

## Windows and WSL diagnostics

Commands included:

```text
Get-ComputerInfo
$PSVersionTable
wsl --status
wsl --version
wsl --list --verbose
docker --version
docker compose version
nvidia-smi
python --version
Get-CimInstance Win32_ComputerSystem
Get-CimInstance Win32_OperatingSystem
Get-CimInstance Win32_LogicalDisk
```

Relevant results:

```text
Windows build: 26200
PowerShell: 5.1.26100.8875
WSL: 2.6.1.0; default version 2
WSL distributions: docker-desktop (WSL2); Ubuntu absent
Docker client / server: 29.6.2
Docker Compose: 5.3.1
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
VRAM: 8188 MiB
Driver: 610.74
Windows driver CUDA API: 13.3
Python: 3.12.2
RAM: 15.29 GB total; 6.93 GB free
C: 261.38 GB free
```

Failed or unavailable checks:

- Docker daemon initially failed because Docker Desktop was stopped.
- Ubuntu-specific `uname`, Python, pip, `nvcc`, memory, disk, and Docker commands
  were not run because no Ubuntu WSL distribution is installed.
- `nvcc` availability inside an Ubuntu distribution is therefore unknown.

Docker Desktop was started, after which `docker info` succeeded. No settings
were changed.

## CUDA container validation

```text
docker run --rm --gpus all \
  nvidia/cuda:12.9.1-base-ubuntu22.04 \
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
```

Downloaded image:

```text
nvidia/cuda:12.9.1-base-ubuntu22.04
```

Result:

```text
NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 610.74
```

The disposable container exited successfully.

## Isolated vLLM and LMCache preparation

The official integrated image manifest was inspected before downloading:

```text
docker buildx imagetools inspect lmcache/vllm-openai:latest-cu129 --raw
```

Observed compressed layer total: approximately 11.87 GB. This is the runtime
image, not a model. The selected model remains under the 3 GB safety limit:

```text
Qwen/Qwen2.5-0.5B-Instruct
Hugging Face model weight: 988 MB BF16
```

Image command:

```text
docker pull lmcache/vllm-openai:latest-cu129
```

No Hugging Face token was used or logged.

## vLLM smoke test

The isolated server command and measured result are recorded here after the
image pull. Port 8001 is intentionally separate from the KnowledgeChat backend.

```text
docker run --detach --name knowledgechat-vllm-smoke --gpus all \
  --ipc=host -p 8001:8000 \
  -v knowledgechat_hf_smoke:/root/.cache/huggingface \
  lmcache/vllm-openai:latest-cu129 \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --dtype half --max-model-len 2048 \
  --gpu-memory-utilization 0.75

GET http://localhost:8001/v1/models
POST http://localhost:8001/v1/chat/completions
docker exec knowledgechat-vllm-smoke nvidia-smi
docker stop knowledgechat-vllm-smoke
docker rm knowledgechat-vllm-smoke
```

Result:

```text
NOT RUN — the integrated image was not fully available.
```

The image contains two compressed layers of approximately 5.96 GB and 4.91 GB.
The bounded pull did not complete, and free host RAM fell from 6.93 GB before
the pull to 1.69 GB during it. The pull client was stopped; no server container
was created and no model was downloaded. Therefore `/v1/models`, completion,
GPU observation during inference, and server shutdown could not be tested.

## LMCache smoke test

Proposed in-process connector for the isolated container:

```text
--kv-transfer-config \
  {"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}
```

The same long-prefix prompt would be sent twice and connector logs checked for
a store followed by a retrieve.

Result:

```text
NOT RUN — blocked by the incomplete integrated image pull.
```

This was not forced. No assertion of LMCache reuse is made.

## Validation commands

```text
python -m unittest discover -s backend/tests -v
npm run build
PowerShell parser check for check_vllm_lmcache_windows.ps1
bash -n scripts/diagnostics/check_vllm_lmcache_wsl.sh
git diff --check
```

Results:

```text
Backend: 128 tests passed (isolated existing backend image with current tests mounted read-only)
Frontend: production build passed (current source mounted into the existing frontend image)
PowerShell parser: passed
Bash syntax: passed with Git Bash
git diff --check: passed
```

The first direct Windows backend attempt failed because the host Python
environment did not contain the project's dependencies. It did not modify the
environment. A disposable backend container with the current test directory
mounted read-only then passed all 128 tests.

The first whole-directory frontend mount attempt could not use the Windows
`node_modules` tree inside Linux. The current source and configuration files
were then mounted individually over the existing project frontend image, and
that exact source completed the production build.
