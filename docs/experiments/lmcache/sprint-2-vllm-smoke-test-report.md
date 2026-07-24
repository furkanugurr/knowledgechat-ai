# Experimental Sprint 2: WSL Ubuntu + vLLM Smoke Test

Access date for external documentation: 2026-07-24.

## Executive summary

**Decision: GO.**

Ubuntu 24.04.4 LTS was installed as a WSL2 distribution. The RTX 4060 Laptop
GPU is visible from Ubuntu, PyTorch can use CUDA, and vLLM 0.25.1 successfully
served `Qwen/Qwen2.5-0.5B-Instruct` on port 8001. The OpenAI-compatible models
and chat-completions endpoints returned valid JSON. Three sequential requests
succeeded, the experimental process stopped cleanly, and GPU memory returned to
zero.

No KnowledgeChat application, provider, retrieval, ChromaDB, Ollama, embedding,
benchmark, knowledge-base, or production Compose behavior was changed.

## Previous Sprint 1 decision

Sprint 1 ended with **CONDITIONAL GO** because WSL2 GPU passthrough worked but
Ubuntu was absent and the integrated vLLM/LMCache image was too large for the
bounded test. Sprint 2 resolves the Ubuntu prerequisite and tests vLLM directly.
LMCache remains deliberately out of scope.

## Official compatibility sources

| Source | Organization | Relevant conclusion |
| --- | --- | --- |
| [Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install) | Microsoft | `wsl --install -d <distribution>` is the supported distribution installation path; first launch requires user-created Linux credentials. |
| [Basic commands for WSL](https://learn.microsoft.com/en-us/windows/wsl/basic-commands) | Microsoft | `wsl --list --online` and `wsl --list --verbose` are the supported availability/version checks. |
| [CUDA on WSL User Guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) | NVIDIA | WSL2 exposes the Windows NVIDIA driver to Linux; a separate Linux display driver must not be installed. |
| [GPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/) | vLLM | Linux CUDA wheels and isolated Python environments are supported; current guidance recommends `uv`. |
| [OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/) | vLLM | vLLM exposes `/v1/models` and `/v1/chat/completions`. |
| [Qwen2.5 0.5B model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Qwen / Hugging Face | The public 0.49B instruction model uses BF16 safetensors and is small enough for the sub-3-GB test limit. |

## Ubuntu WSL installation result

- Distribution: `Ubuntu-24.04`
- Version: Ubuntu 24.04.4 LTS (Noble Numbat)
- WSL generation: 2
- Kernel: `6.6.87.2-microsoft-standard-WSL2`
- Internet: HTTPS request to PyPI returned HTTP 200.
- DNS: `pypi.org` resolved successfully.
- WSL-visible RAM: 7.4 GiB total, approximately 6.9 GiB available immediately
  after first-run setup.
- WSL root filesystem: approximately 955 GiB free before package installation.
- Required Ubuntu packages: `python3.12-venv` and `python3-pip`.
- No restart was requested.

The Linux username and password were created interactively by the user. No
credential was guessed, captured, or stored.

## GPU validation

| Item | Result |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| Driver | 610.74 |
| Total VRAM | 8,188 MiB |
| Free VRAM before startup | 7,956 MiB |
| PyTorch CUDA available | `True` |
| PyTorch CUDA build | 13.0 |
| Linux NVIDIA display driver installed | No |

## Selected installation approach

A Python virtual environment at `~/knowledgechat-vllm-poc/.venv` was selected
instead of modifying KnowledgeChat's environment or production containers. This
is the smallest direct proof of the target WSL architecture, keeps packages
isolated, and avoids coupling the experiment to Docker Desktop.

`uv` 0.11.32 was installed under `~/.local/bin` because vLLM's official
installation guidance recommends it and its parallel downloader was materially
faster than the initial single-connection pip attempt.

## Installed versions

| Component | Version |
| --- | --- |
| Python | 3.12.3 |
| pip | 24.0 |
| uv | 0.11.32 |
| vLLM | 0.25.1 |
| PyTorch | 2.11.0+cu130 |
| PyTorch CUDA | 13.0 |

Installation commands:

```bash
sudo apt update
sudo apt install -y python3.12-venv python3-pip
mkdir -p ~/knowledgechat-vllm-poc
python3 -m venv ~/knowledgechat-vllm-poc/.venv
curl -LsSf https://astral.sh/uv/install.sh | sh
~/.local/bin/uv pip install \
  --python ~/knowledgechat-vllm-poc/.venv/bin/python \
  vllm
```

The initial `pip install vllm` was stopped before completion when its sequential
download proved very slow. `uv` completed the installation in the same isolated
environment.

## Model

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Parameters: 0.49B
- Safetensors checkpoint reported by vLLM: 0.92 GiB
- Published weight file size: 988 MB
- Authentication: none; the public repository was downloaded anonymously
- Safety threshold: below the 3 GB model limit

No Gemma model and no LMCache package was downloaded.

## Exact server configuration

The startup helper applies:

```bash
export VLLM_USE_V2_MODEL_RUNNER=0
export VLLM_USE_FLASHINFER_SAMPLER=0

vllm serve Qwen/Qwen2.5-0.5B-Instruct \
  --host 0.0.0.0 \
  --port 8001 \
  --dtype half \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.70 \
  --max-num-seqs 1
```

Both environment switches are present in vLLM 0.25.1:

- V2 model runner was disabled because it requires UVA pinned-memory behavior
  unavailable in this WSL environment.
- FlashInfer sampling was disabled because its local JIT path requested `nvcc`;
  installing the full CUDA toolkit merely for the sampler was unnecessary.

Attention continued to use the packaged FlashAttention backend. No CPU offload,
tensor parallelism, or LMCache was enabled.

## API endpoint results

### `GET /v1/models`

- HTTP status: 200
- Model ID: `Qwen/Qwen2.5-0.5B-Instruct`
- Reported maximum model length: 2048
- Valid JSON: yes

### `POST /v1/chat/completions`

All three requests returned:

- HTTP status: 200
- valid JSON: yes
- non-empty generated text: yes
- returned model: `Qwen/Qwen2.5-0.5B-Instruct`

The generated factual content was not scored; this sprint validates serving,
not KnowledgeChat answer quality.

## Request timing results

The committed smoke-test script uses `time.perf_counter`. Raw results are stored
locally at
`work/experiments/lmcache/sprint_2/vllm_smoke_results.json` and ignored by Git.

| Request | Duration | Text length |
| --- | ---: | ---: |
| Very short Turkish request | 2.509125 s | 40 |
| Medium Turkish request | 2.604935 s | 205 |
| Repeat of request 2 | 2.579370 s | 205 |

`/v1/models` took 2.087133 seconds in the same run. These numbers are smoke-test
observations, not a performance benchmark and not evidence of LMCache behavior.

## GPU memory observation

- Before server startup: 0 MiB used.
- Highest observed sample: 5,678 MiB used.
- During the final request sample: 5,678 MiB used and 93% GPU utilization.
- After clean shutdown: 0 MiB used; 7,956 MiB free.

The measurement is sampled with `nvidia-smi`, so it is an observed peak rather
than a continuous profiler maximum.

## Errors and warnings

1. Ubuntu first launch required interactive username/password creation as
   expected.
2. Ubuntu's base image lacked `ensurepip`; `python3.12-venv` and `python3-pip`
   were installed from Ubuntu repositories.
3. Sequential pip download was slow; isolated installation was completed with
   `uv`.
4. vLLM's default V2 model runner failed with `RuntimeError: UVA is not
   available`. The installed, documented environment switch selected the V1
   runner.
5. The next attempt failed because FlashInfer sampler JIT could not find `nvcc`.
   The installed vLLM switch disabled only that sampler. Installing a Linux
   NVIDIA display driver or full CUDA toolkit was not necessary.
6. Anonymous Hugging Face access emitted a rate-limit warning but completed.
7. A WSL server must retain an active WSL client/terminal. The startup script
   therefore runs in the foreground by design.

## Reproducibility

From an Ubuntu WSL terminal:

```bash
cd "/mnt/c/Users/Furkan Uğur/Documents/Codex/2026-07-14/git/knowledgechat-ai"
bash scripts/experiments/start_vllm_wsl.sh
```

Keep that terminal open. From Windows PowerShell in the repository:

```powershell
python scripts/experiments/test_vllm_smoke.py
```

To stop from a second Ubuntu terminal:

```bash
cd "/mnt/c/Users/Furkan Uğur/Documents/Codex/2026-07-14/git/knowledgechat-ai"
bash scripts/experiments/stop_vllm_wsl.sh
```

The scripts target only port 8001 and the experimental PID file.

## Cleanup

Stop the server first. Optional experiment cleanup:

```bash
rm -rf ~/knowledgechat-vllm-poc
rm -rf ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct
```

The report does not recommend unregistering Ubuntu or deleting unrelated caches.

## Sprint decision and Sprint 3 readiness

**GO** — the small-model vLLM server works reliably enough for a provider
integration experiment.

Sprint 3 should add an experimental, opt-in vLLM provider behind the existing
provider abstraction while keeping Ollama as the default. It should use port
8001, retain the same API response schema, add health/timeout tests, and run a
small comparative RAG validation. LMCache should remain a later independent
experiment until basic provider behavior is stable.
