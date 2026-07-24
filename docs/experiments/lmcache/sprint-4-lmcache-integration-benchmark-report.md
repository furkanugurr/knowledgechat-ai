# Experimental Sprint 4 — LMCache Integration and Controlled Benchmark

Access and benchmark date: 2026-07-24

## Executive summary

PR #24 was reviewed and merged into `main` as
`7ec2d3561407fbb98b7c3fb24dc252f84a38bd03`. LMCache 0.5.2 was installed in
the isolated WSL environment `.venv-lmcache`; the known-good vLLM-only
`.venv` was preserved.

LMCache worked with the real KnowledgeChat RAG pipeline and produced strong,
direct cache-hit evidence: 27 of 28 generation calls reused cached KV data,
with 45,568 hit tokens out of 57,095 observed prompt tokens (79.8%). However,
the benchmark did not show a latency improvement. Average streaming TTFT
regressed by 7.43%, warm in-domain RAG duration regressed by 0.15%, and warm
p95 regressed by 0.26%. All 32 LMCache RAG answers were byte-identical to
their baseline equivalents, so quality and citations were preserved.

Decision: **CONDITIONAL GO**. Integration is functional and reproducible, but
the current single-user workload does not justify enabling LMCache by
default. LMCache remains experimental and opt-in; Ollama remains the default
provider.

## Scope and unchanged behavior

The benchmark used the same model, quantization, 8,192-token context, eight
questions, retrieval configuration, PromptBuilder, embedding model, Chroma
collection, backend image, and generation parameters in both conditions.
Retrieval, prompts, embeddings, citations, API schema, frontend,
knowledge-base content, and historical benchmark results were not changed.

## Environment

- Windows 11 Pro and WSL2 Ubuntu 24.04.4 LTS
- RTX 4060 Laptop GPU, approximately 8 GB VRAM
- Ryzen 7 7840HS and 16 GB system RAM
- Python 3.12.3
- vLLM 0.25.1
- PyTorch 2.11.0+cu130; CUDA runtime 13.0
- LMCache 0.5.2
- model: `Qwen/Qwen2.5-3B-Instruct-AWQ`
- quantization: AWQ 4-bit
- context: 8,192 tokens
- temperature: 0
- maximum generated tokens: 768
- GPU-memory utilization: 0.70
- maximum sequences: 1
- tensor parallel size: 1
- CPU offload: none
- Chroma collection: `knowledgechat`
- Chroma path in backend: `/workspace/backend/data/chroma`
- embedding model: `nomic-embed-text`, 768 dimensions

## Official integration research

| Source | Organization | Conclusion |
|---|---|---|
| [LMCache Quickstart](https://docs.lmcache.ai/getting_started/quickstart.html) | LMCache | MP mode is recommended for vLLM 0.20+, while in-process mode remains the simple single-node option. |
| [vLLM LMCache Examples](https://docs.vllm.ai/en/latest/examples/others/lmcache/) | vLLM | `LMCacheConnectorV1` supports in-process CPU offload; `LMCacheMPConnector` uses a standalone cache service. |
| [CPU RAM backend](https://docs.lmcache.ai/kv_cache/storage_backends/cpu_ram.html) | LMCache | CPU RAM uses `local_cpu`, `max_local_cpu_size`, and `chunk_size`, connected through `--kv-transfer-config`. |
| [LMCache releases](https://github.com/LMCache/LMCache/releases) | LMCache | Current releases include connector snapshots and observability improvements for recent vLLM versions. |

All sources were accessed on 2026-07-24. The installed vLLM help confirmed
`--kv-transfer-config` and all existing Sprint 3.6 resource flags.

## Version and WSL compatibility decision

LMCache 0.5.2 resolved against the existing Python 3.12, vLLM 0.25.1,
PyTorch 2.11, and CUDA 13 stack. Installation changed dependency versions
only inside `.venv-lmcache`; the baseline environment retained vLLM 0.25.1,
PyTorch 2.11, and NumPy 2.3.5.

The current recommended MP connector was attempted first. The LMCache server
started, but WSL2 failed KV-cache registration with:

```text
torch.AcceleratorError: CUDA error: invalid resource handle
```

The failure occurred while reconstructing CUDA IPC storage in the standalone
server. No benchmark result was taken from this failed condition. The
supported in-process `LMCacheConnectorV1` was then used successfully. This is
a documented limitation of the present WSL/hardware combination and the
main reason the result is conditional.

## Storage design

- backend: local CPU RAM only
- maximum size: 1.0 GiB
- chunk size: 256 tokens
- eviction: LRU
- disk/Redis/remote/distributed storage: disabled
- persistence across restart: none

One GiB leaves room for Windows, WSL, Docker, Chroma, Ollama embeddings, and
the backend on a 16 GB machine. Cleanup occurs when the vLLM process exits.

## Exact startup commands

Baseline:

```text
~/.venv/bin/python -m vllm.entrypoints.cli.main serve \
  Qwen/Qwen2.5-3B-Instruct-AWQ \
  --host 0.0.0.0 --port 8001 --dtype half --quantization awq \
  --max-model-len 8192 --gpu-memory-utilization 0.70 \
  --max-num-seqs 1 --download-dir ~/.cache/huggingface
```

LMCache adds only:

```text
LMCACHE_LOCAL_CPU=True
LMCACHE_MAX_LOCAL_CPU_SIZE=1.0
LMCACHE_CHUNK_SIZE=256
--kv-transfer-config '{"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}'
```

Both modes retained:

```text
VLLM_USE_V2_MODEL_RUNNER=0
VLLM_USE_FLASHINFER_SAMPLER=0
```

## Functional smoke test

The vLLM model endpoint and streaming chat endpoint returned HTTP 200 and
non-empty output. The short direct questions were below the 256-token cache
chunk and correctly reported zero external-cache hits. The following real RAG
run contained prompts from 1,229 to 2,960 tokens and demonstrated LMCache hits
from 512 to 2,816 tokens per request. There was no crash, invalid response,
provider fallback, or silent fallback.

## Controlled benchmark

Each condition used:

- one cold sequence;
- three warm sequences;
- eight questions in the same order;
- six in-domain and two out-of-domain questions;
- 32 real KnowledgeChat RAG requests;
- 32 direct streaming vLLM requests for client-side TTFT.

This produced 64 requests per condition and 128 total measured requests.
Out-of-domain RAG questions were tracked separately and bypassed generation,
as expected.

## Performance results

| Metric | Baseline | LMCache | Result |
|---|---:|---:|---|
| Direct average TTFT | 43.486 ms | 46.719 ms | 7.43% regression |
| Direct median TTFT | 31.643 ms | 34.696 ms | regression |
| Direct p95 TTFT | 45.067 ms | 46.535 ms | 3.26% regression |
| In-domain cold average total | 4.678 s | 4.801 s | 2.62% regression |
| In-domain warm average total | 4.414 s | 4.420 s | 0.15% regression |
| In-domain warm p95 total | 13.506 s | 13.541 s | 0.26% regression |
| Successful RAG requests | 32/32 | 32/32 | equal |
| Timeouts / failures | 0 / 0 | 0 / 0 | equal |
| Peak observed VRAM | 6,331 MiB | 6,341 MiB | +10 MiB |
| Process RSS | 3,472,856 KiB | 4,599,784 KiB | +1,126,928 KiB |
| Endpoint-ready startup | about 61 s | about 65 s | about +4 s |

Negative differences are labelled as regressions, not improvements. The
measured RSS overhead (about 1.075 GiB) is consistent with the configured
1.0 GiB cache plus bookkeeping.

## Cache-reuse analysis

LMCache server-side logs are the authoritative cache evidence:

- RAG generation calls: 28 (24 normal plus four answer-correction calls)
- calls with LMCache hits: 27
- observed prompt tokens: 57,095
- LMCache hit tokens: 45,568
- token hit ratio: 79.8%
- average hit tokens per generation call: 1,627

The first long RAG prompt was cold. Later questions received 512-token shared
prefix reuse, while repeated warm questions reused 1,024–2,816 tokens.
Repeated system/prompt structure provided natural shared-prefix reuse;
identical warm questions added larger reuse. Retrieval order was not changed.
Out-of-domain questions bypassed generation and were not cache opportunities.

The lack of latency benefit is attributable to this single-request,
single-sequence workload and vLLM's already effective GPU prefix cache.
External CPU-cache transfer/lookup overhead offsets the saved prefill work.

## Quality preservation

- baseline RAG answers: 32
- LMCache RAG answers: 32
- byte-identical pairs: 32/32
- degraded or meaningfully different pairs: 0
- citation schema and source families: preserved
- out-of-domain decisions: 8/8 correct across both conditions
- out-of-domain generation calls: 0
- provider fallback: 0
- Ollama generation calls: 0
- Ollama usage: `nomic-embed-text` only

Because outputs were byte-identical, the Sprint 3.6 project-level manual
quality scores remain applicable. These are engineering evaluations against
returned evidence, not expert ground truth. LMCache neither fixed nor worsened
the model's known unsupported VPN-comparison behavior.

## Errors, cleanup, and limitations

- MP mode is unusable in the current WSL2 CUDA IPC path.
- In-process mode is functional but currently documented as the simpler,
  non-preferred integration mode.
- Client-side TTFT was measured through direct streaming because the public
  KnowledgeChat API remains non-streaming.
- Direct questions were shorter than one LMCache chunk; RAG logs supplied the
  real cache-hit evidence.
- This serial workload does not measure concurrent throughput.

After testing, the backend, vLLM, LMCache, and monitors were stopped;
`nomic-embed-text` was unloaded; final GPU memory was 0 MiB. Model files and
the isolated environments remain outside Git.

## Automated validation

- backend: 192 passed plus 42 subtests;
- focused benchmark/SSE tests: 4 passed;
- Visual Guide Extraction: 32/32 passed;
- frontend production build: passed;
- Python syntax: passed;
- Bash syntax: passed;
- `git diff --check`: passed.

Ollama remains the default provider. LMCache is absent from backend
requirements and normal startup. No production application, retrieval,
prompt, embedding, Chroma, API, frontend, knowledge-base, or historical
benchmark file was modified.

## Sprint decision and Sprint 5 recommendation

Decision: **CONDITIONAL GO**.

LMCache is technically working and provides strong cache reuse without quality
loss, but it adds approximately 1.075 GiB RAM and provides no measurable
latency gain in the current workload. Do not enable it in production.

For Sprint 5, test a workload where external KV reuse is expected to matter:
longer shared RAG prefixes, cache pressure sufficient to evict GPU prefix
entries, and controlled concurrency. First investigate whether a future
WSL/driver/LMCache release resolves MP CUDA IPC. Keep the same quality,
citation, and provider-isolation gates, and require a positive TTFT/p95 result
before progressing beyond experimental opt-in status.
