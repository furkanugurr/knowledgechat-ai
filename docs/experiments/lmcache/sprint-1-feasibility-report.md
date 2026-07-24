# Experimental Sprint 1: vLLM + LMCache Feasibility

Access date for external documentation: 2026-07-24.

## Executive summary

**Decision: CONDITIONAL GO.**

The machine can expose its RTX 4060 Laptop GPU to Linux containers through
Docker Desktop and WSL2. This is a sound basis for an isolated vLLM experiment.
The current `gemma3:12b` workload is not a realistic vLLM target on 8 GB VRAM:
its unquantized weights alone need roughly 24 GB, and even 4-bit weights consume
about 6 GB before KV cache and runtime allocations. The 16 GB host RAM also
makes heavy CPU offload unsuitable for a fair latency comparison.

Sprint 2 should use a separately downloaded Hugging Face model. The recommended
smoke-test model is `Qwen/Qwen2.5-0.5B-Instruct` (988 MB BF16 weight file); a
larger, quality-oriented comparison model should only be selected after measuring
the remaining VRAM and context-length budget. Ollama remains unchanged.

## Machine specifications

| Component | Observed value |
| --- | --- |
| Host | Microsoft Windows 11 Pro, build 26200 |
| CPU | AMD Ryzen 7 7840HS, 8 cores / 16 threads |
| RAM | 15.29 GB total; 6.93 GB free before, 1.69 GB during the large image pull |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| VRAM | 8,188 MiB |
| NVIDIA driver | 610.74 |
| CUDA reported by Windows driver | 13.3 |
| System disk | 261.38 GB free |
| Windows Python | 3.12.2 |

## Windows diagnostics

- PowerShell: 5.1.26100.8875.
- WSL is installed; default version is WSL2.
- WSL package: 2.6.1.0; Linux kernel: 6.6.87.2-1.
- The only registered distribution is `docker-desktop`; no Ubuntu distribution
  is installed.
- Docker client and server: 29.6.2; Compose: 5.3.1.
- Docker Desktop was initially stopped and started without changing project
  configuration.

## WSL2 diagnostics

An ordinary Ubuntu WSL distribution is **not available**, so a native Ubuntu
virtual environment was not created and distribution-specific Python, pip,
`nvcc`, disk, and Docker checks could not be performed. The Docker-managed WSL2
environment is functional. Installing Ubuntu is a prerequisite for the proposed
non-container alternative, but it was intentionally not performed because it is
a system-level change outside a read-only feasibility check.

## GPU and CUDA diagnostics

Windows `nvidia-smi` reported the RTX 4060 Laptop GPU, driver 610.74, 8,188 MiB
VRAM, and no active VRAM usage at collection time. A disposable
`nvidia/cuda:12.9.1-base-ubuntu22.04` container also reported the same GPU,
VRAM, and driver. This directly confirms CUDA device passthrough into the
Docker/WSL2 Linux environment.

The GPU is Ada generation and exceeds the compute capability 7.0 minimum stated
by LMCache and older/current vLLM compatibility guidance. NVIDIA's WSL guide
states that the Windows NVIDIA driver is exposed inside WSL and warns against
installing a separate Linux display driver.

## Docker diagnostics

Docker Desktop uses the Linux/WSL2 engine and accepts `--gpus all`. No production
Compose file was edited. The CUDA test container exited cleanly after
`nvidia-smi`.

## vLLM compatibility findings

| Source | Organization | Relevant conclusion |
| --- | --- | --- |
| [GPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/) | vLLM | Current CUDA wheels and containers target Linux; isolated container use avoids changing the project Python environment. |
| [Docker deployment](https://docs.vllm.ai/en/v0.20.0/deployment/docker/) | vLLM | `vllm/vllm-openai` provides an OpenAI-compatible server and supports NVIDIA GPU passthrough. |
| [OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/) | vLLM | `/v1/models`, completions, and chat completions can be used for a smoke test. |
| [Supported models](https://docs.vllm.ai/en/v0.25.1/models/supported_models/) | vLLM | `Gemma3ForConditionalGeneration` is listed, including Gemma 3 instruction checkpoints. |
| [Quantization](https://docs.vllm.ai/en/v0.15.0/features/quantization/) | vLLM | Ada supports relevant GPTQ/AWQ/Marlin paths; exact support remains checkpoint- and kernel-dependent. |
| [Qwen2.5 0.5B model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Qwen / Hugging Face | The ungated 0.49B instruction model is appropriate for a sub-3-GB infrastructure smoke test. |

Native Windows is not the target execution environment. Docker Desktop on WSL2
or a dedicated Ubuntu WSL2 distribution is required.

## LMCache compatibility findings

| Source | Organization | Relevant conclusion |
| --- | --- | --- |
| [Installation](https://docs.lmcache.ai/getting_started/installation.html) | LMCache | Requires Linux, Python 3.9-3.13, NVIDIA compute capability 7.0+, and CUDA 12.1+; integrated Docker images are available. |
| [Quickstart](https://docs.lmcache.ai/getting_started/quickstart.html) | LMCache | Multiprocess mode is recommended; in-process `LMCacheConnectorV1` is suitable for a simple single-node experiment. |
| [Dynamic connector](https://docs.lmcache.ai/api_reference/dynamic_connector.html) | LMCache | Modern vLLM can dynamically load the LMCache connector; version alignment matters. |
| [CUDA on WSL guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) | NVIDIA | WSL2 GPU compute and Docker Desktop are supported, but managed-memory, pinned-memory, and NVML limitations remain. |

LMCache itself is compatible with the GPU and Linux container path. The main
constraint is memory: CPU-backed KV cache competes with only 16 GB of host RAM.
Begin with a 1-2 GB cache and a short context; do not copy the documentation's
large server-cache examples to this laptop.

## Gemma 3 12B feasibility

- FP16/BF16 weights: approximately 24 GB before KV cache and runtime overhead.
- 8-bit weights: approximately 12 GB before overhead.
- 4-bit weights: approximately 6 GB before scale metadata, KV cache, CUDA graphs,
  activations, and allocator overhead.
- Result: 8 GB VRAM is insufficient for the normal 12B vLLM configuration and
  extremely constrained for a 4-bit checkpoint.
- CPU offload would be required for non-4-bit variants. The host has only 16 GB
  RAM, so it cannot comfortably hold the unquantized model plus Windows, WSL,
  vLLM, and application processes. Heavy PCIe offload would also make latency
  comparisons against Ollama misleading.
- AWQ/GPTQ are the preferred vLLM-native quantized checkpoint families to
  investigate. GGUF support is documented as experimental/under-optimized and
  may require the base tokenizer.
- The exact Ollama artifact is not directly reusable as a normal vLLM model
  repository. vLLM expects a Hugging Face-compatible model configuration,
  tokenizer, and weights (or a specifically supported quantized checkpoint).

**Classification: Feasible only with a smaller model.**

## Smoke test commands

The exact commands and outputs are in
[`sprint-1-command-log.md`](sprint-1-command-log.md). The test uses port 8001
to avoid colliding with KnowledgeChat's backend, an isolated cache volume, and
`Qwen/Qwen2.5-0.5B-Instruct`. No token is needed for this public model.

## Smoke test results

- CUDA passthrough: **PASS**.
- vLLM server and short completion: **NOT RUN**. The integrated LMCache/vLLM
  image has approximately 11.87 GB of compressed layers. Its two largest layers
  (approximately 5.96 GB and 4.91 GB) did not finish within the bounded
  feasibility window, while free host RAM fell to 1.69 GB.
- Clean shutdown: the pull client was stopped cleanly; no model server or
  application container remained running.
- LMCache repeated-prefix test: **NOT RUN**, because the integrated image was
  unavailable. The test was not forced in accordance with the sprint's safety
  rule.

No claim is made that vLLM or LMCache served a model on this machine. The
successful result is limited to CUDA container passthrough and compatibility
evidence. Sprint 2 must complete a pinned-image pull before measuring inference.

## Observed errors

- Docker daemon was initially unavailable because Docker Desktop was stopped.
- No Ubuntu WSL distribution exists.
- Direct execution of the PowerShell script was blocked by the local execution
  policy; syntax validation passed and a one-process `-ExecutionPolicy Bypass`
  invocation completed without changing the machine-wide policy.
- A WSL-routed `bash.exe` command failed because no ordinary Linux distribution
  exists; the Bash script subsequently passed `bash -n` with Git Bash.
- The integrated image pull was bounded and stopped before model startup due to
  its download size and observed host-memory pressure.

## Risks

1. Eight GB VRAM sharply limits model size, context length, concurrency, and KV
   cache.
2. Sixteen GB RAM limits LMCache capacity and makes CPU offload unattractive.
3. WSL2 memory and NVML behavior differs from native Linux.
4. vLLM and LMCache connector APIs change quickly; pin compatible versions.
5. A 0.5B smoke model proves infrastructure only, not answer quality parity.
6. Hugging Face Gemma checkpoints may require license acceptance and separate
   credentials; no gated checkpoint was downloaded.
7. Docker images consume significant disk space even when the test model is
   small.

## Recommended model for Sprint 2

Start with `Qwen/Qwen2.5-0.5B-Instruct` to reproduce the infrastructure test.
For an application-quality comparison, benchmark the smallest Hugging
Face-compatible instruct checkpoint that fits with at least 1-2 GB VRAM headroom
at the intended context length. A Gemma-family comparison should start with a
small Gemma 3 checkpoint only after access and exact checkpoint size are verified.
Do not begin with Gemma 3 12B.

## Decision and exact next steps

**CONDITIONAL GO** — proceed only with a smaller model and an isolated Linux
container or newly installed Ubuntu WSL2 distribution.

1. Keep Ollama as the production provider.
2. Pin a compatible vLLM/LMCache container tag rather than `latest`.
3. Reserve port 8001 for the experiment.
4. Use a public sub-3-GB model, `--max-model-len 2048`, one request at a time,
   and conservative GPU utilization.
5. Start LMCache in-process with a 1-2 GB CPU cache; compare repeated-prefix
   latency and validate cache-hit logs.
6. Measure cold latency, warm latency, peak VRAM, host RAM, and answer validity.
7. Only after a stable isolated benchmark, design a provider interface change in
   a separate sprint.
