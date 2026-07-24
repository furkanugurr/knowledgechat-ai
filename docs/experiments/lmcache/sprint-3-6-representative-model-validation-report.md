# Experimental Sprint 3.6 — Representative vLLM Model Validation

Access and test date: 2026-07-24

## Executive summary

PR #23 was reviewed and merged into `main` with merge commit
`fd83a918480810d151b24196152a86ca0057c7b1`. The Sprint 3.6 work was then
performed on `experiment/sprint-3-6-representative-model-validation`.

Two compact AWQ models were downloaded and tested through the real
KnowledgeChat HTTP/RAG flow. Both ran reliably with an 8,192-token context,
preserved citations and out-of-domain rejection, and used Ollama only for
`nomic-embed-text`. `Qwen/Qwen2.5-3B-Instruct-AWQ` produced the best overall
answer quality and is the selected representative model. It nevertheless
invented several details in the VPN comparison case. The sprint decision is
therefore **CONDITIONAL GO**, not an approval to use this model in production.
It is representative enough for a controlled LMCache experiment with the
same prompts and validation set.

LMCache was **not integrated**. Ollama remains the default provider.

## Goal and invariants

The goal was to find a more representative local instruction model than the
Sprint 3.5 0.5B smoke-test model without changing retrieval, embeddings,
citations, API responses, frontend behavior, Chroma data, or knowledge-base
content. The existing `knowledgechat` collection (1,481 chunks, 177 documents,
165 Antikor guides) and 768-dimensional `nomic-embed-text` embeddings were
reused.

## Hardware and environment

- Windows 11 Pro with WSL2 Ubuntu 24.04.4 LTS
- NVIDIA RTX 4060 Laptop GPU, approximately 8 GB VRAM
- AMD Ryzen 7 7840HS and 16 GB system RAM
- vLLM 0.25.1 and PyTorch 2.11.0+cu130
- isolated environment: `~/knowledgechat-vllm-poc/.venv`
- Hugging Face cache: `~/.cache/huggingface`
- free WSL disk space before testing: approximately 944 GB

Installed vLLM help was checked for the model, dtype, quantization,
max-model-length, GPU-memory-utilization, max-sequence, CPU-offload,
download-directory, eager-mode, KV-cache, and chat-template arguments. No
Linux display driver or CUDA Toolkit was installed.

## Official compatibility research

| Source | Organization | Relevant conclusion |
|---|---|---|
| [Supported Models](https://docs.vllm.ai/en/latest/models/supported_models/) | vLLM | Qwen2, Phi-3 and Gemma 3 architectures are supported. |
| [Quantization](https://docs.vllm.ai/en/v0.22.1/features/quantization/) | vLLM | AWQ, GPTQ and BitsAndBytes are supported on NVIDIA Ada GPUs, subject to model-format compatibility. |
| [Engine Arguments](https://docs.vllm.ai/en/latest/configuration/engine_args/) | vLLM | `--max-model-len`, GPU-memory utilization and optional CPU offload directly affect the weight/KV-cache budget. |
| [Qwen2.5-1.5B-Instruct-AWQ](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-AWQ) | Qwen | 1.54B, 4-bit AWQ, 32,768-token declared context, multilingual and Apache-2.0. |
| [Qwen2.5-3B-Instruct-AWQ](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-AWQ) | Qwen | 3B-class, 4-bit AWQ and long-context support; Qwen Research License imposes non-commercial restrictions. |
| [Phi-3.5-mini-instruct](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) | Microsoft | 3.8B FP16, 128K context, Turkish listed and MIT licensed, but the roughly 7.64 GB repository/weights leave insufficient 8 GB VRAM headroom. |
| [gemma-3-1b-it](https://huggingface.co/google/gemma-3-1b-it) | Google | 1B-class, 32K context, but gated access and Gemma licensing reduce reproducibility for this experiment. |

All sources were accessed on 2026-07-24. KV cache consumes the memory left
after weights and runtime allocations; consequently a model that nominally
fits can still fail at an 8,192-token context. CPU offload was avoided because
it adds host-to-device transfer overhead and was not needed.

## Shortlist and static screening

| Candidate | Format / approximate download | Context | Expected fit | Decision |
|---|---:|---:|---|---|
| `Qwen/Qwen2.5-1.5B-Instruct-AWQ` | AWQ 4-bit / 1.61 GB | 32,768 declared | Safe | Tested |
| `Qwen/Qwen2.5-3B-Instruct-AWQ` | AWQ 4-bit / 2.69 GB | long context | Viable with conservative settings | Tested |
| `microsoft/Phi-3.5-mini-instruct` | FP16 / about 7.64 GB | 128K | Unsafe weight plus KV/runtime margin | Rejected before download |
| `google/gemma-3-1b-it` | gated repository, about 10.67 GB total repository storage | 32K | Access/licensing friction; less representative than selected Qwen candidates | Rejected before download |

Only the two Qwen candidates were downloaded. No candidate over 5 GB and no
Gemma 3 12B model was downloaded.

## Exact startup configuration

Both candidates used:

```text
VLLM_USE_V2_MODEL_RUNNER=0
VLLM_USE_FLASHINFER_SAMPLER=0
~/knowledgechat-vllm-poc/.venv/bin/vllm serve <MODEL>
  --host 0.0.0.0
  --port 8001
  --dtype half
  --max-model-len 8192
  --gpu-memory-utilization 0.70
  --max-num-seqs 1
  --download-dir ~/.cache/huggingface
  --quantization awq
```

No CPU offload, excessive swap, LMCache flags, or additional generation
model was used.

## Startup and resource results

| Metric | Qwen2.5 1.5B AWQ | Qwen2.5 3B AWQ |
|---|---:|---:|
| Download/start | Successful | Successful |
| First startup (includes download) | 218.472 s | 268.843 s |
| Logged model load | Not separately retained | 187.243 s |
| `/v1/models` | HTTP 200; 8192 | HTTP 200; 8192 |
| Short completion | HTTP 200; 3.433 s | HTTP 200; 3.478 s |
| Idle/loaded VRAM | about 5,390 MiB | about 5,308 MiB before embedding load |
| Peak observed live-RAG VRAM | 5,957 MiB | 5,899 MiB |
| Peak GPU utilization | 100% | 100% |
| Shutdown | Successful | Successful |
| VRAM after cleanup | 0 MiB | 0 MiB |

The 3B engine log reported 1.95 GiB model-loading memory, 2.98 GiB available
KV cache, and 10.59x theoretical concurrency at 8,192 tokens. First-start
durations include network download and are not warm-start latency.

## Live RAG structural results

Each model was connected to the real `RetrievalService`, Chroma collection,
`PromptBuilder`, `ChatService`, and HTTP endpoint. Retrieval thresholds and
knowledge data were unchanged.

| Metric | 1.5B AWQ | 3B AWQ |
|---|---:|---:|
| In-domain structural success | 6/6 | 6/6 |
| Out-of-domain rejection | 2/2 | 2/2 |
| Valid citation/source family | 6/6 | 6/6 |
| Provider fallback | 0 | 0 |
| Ollama generation calls | 0 | 0 |
| vLLM generation requests | 7 | 7 |
| Total eight-case duration | 17.267 s | 28.469 s |

Seven vLLM calls for six in-domain questions are expected because the complex
answer required one post-validation correction attempt. The two
out-of-domain cases were rejected before generation. Ollama process evidence
showed only `nomic-embed-text`.

Request durations in seconds:

| Case | 1.5B | 3B |
|---|---:|---:|
| VLAN concept | 1.670 | 2.994 |
| SSL VPN navigation | 0.611 | 0.505 |
| OSPF multipart | 2.376 | 3.013 |
| VPN comparison | 0.788 | 6.180 |
| Report settings multi-chunk | 1.250 | 1.392 |
| Web security complex grounded | 10.220 | 14.053 |
| Out-of-domain food | 0.118 | 0.110 |
| Out-of-domain weather | 0.078 | 0.080 |

## Project-level manual quality rubric

These scores are engineering evaluations against the returned sources, not
expert ground truth. Each tuple is groundedness, completeness, relevance,
language clarity, and citation consistency (0–4 each).

### Qwen2.5 1.5B AWQ

| Case | Scores | Total | Evidence-based note |
|---|---|---:|---|
| VLAN | 2/2/3/1/3 | 11 | Relevant source family, but malformed Turkish and unsupported phrasing reduce usability. |
| SSL VPN navigation | 4/3/4/3/4 | 18 | Concise source-supported path/purpose; wording is slightly awkward. |
| OSPF multipart | 3/4/4/2/4 | 17 | Both parts answered with guide controls; definition and closing sentence are somewhat generic. |
| VPN comparison | 0/1/2/2/0 | 5 | Contradictory security claims are not supported by the returned SSL VPN evidence. |
| Report settings | 4/4/4/4/4 | 20 | Complete field list matching the cited guide. |
| Web security | 4/4/4/3/4 | 19 | Extensive supported controls; only minor Turkish wording issues. |

Average: **15.0/20**.

### Qwen2.5 3B AWQ

| Case | Scores | Total | Evidence-based note |
|---|---|---:|---|
| VLAN | 2/3/4/2/3 | 14 | More coherent than 1.5B, but adds generic isolation/security assertions beyond direct evidence. |
| SSL VPN navigation | 4/3/4/3/4 | 18 | Same strong source-supported concise answer. |
| OSPF multipart | 3/4/4/3/4 | 18 | Complete steps and clearer language, with a generic protocol definition. |
| VPN comparison | 0/3/3/3/0 | 9 | Fluent but invents protocol, DNS, port and cryptography comparisons absent from the cited source. |
| Report settings | 4/4/4/4/4 | 20 | Complete and source-consistent. |
| Web security | 4/4/4/3/4 | 19 | Detailed, relevant and source-consistent with minor language defects. |

Average: **16.3/20**.

## Selection and decision

`Qwen/Qwen2.5-3B-Instruct-AWQ` is selected as the representative experimental
model because it:

- ran stably at the required 8,192-token context;
- passed all structural, citation and out-of-domain checks;
- achieved the higher manual average;
- improved multipart completeness and Turkish clarity;
- retained a safe observed VRAM margin without CPU offload.

Its Qwen Research License must be reviewed before any commercial use. More
importantly, the unsupported VPN comparison demonstrates that structural
success is not sufficient proof of grounded answer safety. The same weakness
appeared in both sizes, though the 3B response was more fluent and therefore
potentially more misleading.

Sprint decision: **CONDITIONAL GO**. The 3B AWQ model is suitable for a
controlled LMCache performance experiment, but not approved as the production
answer model. Sprint 4 must keep answer-quality scoring as a hard guardrail.

## Cleanup and repository safety

- temporary backend container removed;
- both vLLM candidate processes stopped cleanly;
- `nomic-embed-text` unloaded after testing;
- final observed GPU memory: 0 MiB;
- downloaded Hugging Face cache retained outside the repository;
- no model files, virtual environments, Chroma data, reports under `work/`,
  secrets, knowledge files, or historical benchmark files are committed;
- Ollama remains the default provider;
- LMCache remains not integrated.

## Recommended Sprint 4 LMCache approach

Use only `Qwen/Qwen2.5-3B-Instruct-AWQ` with the exact conservative 8,192-token
configuration above. First record an uncached baseline, then enable LMCache in
the isolated experimental vLLM process only. Repeat the identical eight
questions with cold and warm prompt-prefix runs, recording time-to-first-token,
total latency, throughput, VRAM, cache-hit evidence, citations, and the same
manual groundedness rubric. Do not change retrieval, prompts, embeddings,
knowledge data, API behavior, or the default Ollama configuration. Treat any
quality or citation regression as a failed experiment even if latency improves.
