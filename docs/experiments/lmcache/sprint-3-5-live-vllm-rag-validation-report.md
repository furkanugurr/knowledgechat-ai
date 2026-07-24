# Experimental Sprint 3.5 — Live vLLM RAG Validation

## Executive Summary

The real KnowledgeChat HTTP pipeline completed five in-domain and two
out-of-domain requests using the existing indexed knowledge base. All seven
requests returned HTTP 200 and passed structural validation. Five in-domain
requests reached `VLLMProvider`; the two out-of-domain requests were rejected
before generation. Citations preserved the existing API schema and contained
no duplicates.

The sprint decision is **CONDITIONAL GO**. Provider integration, retrieval,
citations, and provider isolation work end to end. However, the 0.5B Qwen
model produced weak or partially unsupported language in two complex answers.
LMCache should remain deferred until a representative generation model is
validated with the same live runner.

## Sprint Goal

Validate this real flow without changing retrieval, embeddings, citations,
frontend behavior, or the default provider:

```text
HTTP chat request → retrieval → persistent ChromaDB → PromptBuilder
→ VLLMProvider → vLLM → answer and citations
```

LMCache was not integrated.

## PR #22 Merge

- PR: `#22 Experimental Sprint 3: Optional vLLM Provider Integration`
- Merge strategy: merge commit
- Merge commit: `2267a1cab7d30c1e7145b8ca402a79eec4a7ed68`
- Sprint 3.5 branch:
  `experiment/sprint-3-5-live-vllm-rag-validation`

## Missing Collection Root Cause

The collection was never missing. The prior Sprint 3 inspection mounted the
Docker volume at `/data` and opened Chroma at `/data`. Docker Compose mounts
the volume at `/workspace/backend/data`, while `VECTOR_DB_PATH` is
`/workspace/backend/data/chroma`. The equivalent inspection path is therefore
`/data/chroma`.

Opening the correct directory exposed the existing `knowledgechat` collection
with 1481 records. No collection was created and no indexing command was run.

## Index Reuse Decision

The existing index was reused.

| Observation | Value |
| --- | --- |
| Docker volume | `knowledgechat-ai_backend_data` |
| Backend persistence path | `/workspace/backend/data/chroma` |
| Inspection path | `/data/chroma` |
| Local non-Docker path | `backend/data/chroma` |
| Collection | `knowledgechat` |
| Collection records | 1481 |
| Cached documents | 177 |
| Antikor guide documents | 165 |
| Word documents in repository | 7 |
| Embedding dimension | 768 |
| Embedding model | `nomic-embed-text` |
| Metadata | document, path, section, chunk, language, source type |

The index cache also reported 177 files and 1481 chunks. These values matched
the collection exactly and were plausible for the current repository.

## Runtime Configuration

```dotenv
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://host.docker.internal:8001
VLLM_MODEL=Qwen/Qwen2.5-0.5B-Instruct
VLLM_REQUEST_TIMEOUT_SECONDS=180
OLLAMA_HOST=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text
VECTOR_DB_PATH=/workspace/backend/data/chroma
VECTOR_COLLECTION_NAME=knowledgechat
```

Ollama remained responsible only for embeddings. `ollama ps` showed
`nomic-embed-text` and no Ollama generation model during successful testing.

## Service Startup

The Sprint 2 WSL environment was reused. The first preflight used the Sprint 2
limit of 2048 tokens. Real RAG prompts exceeded that limit, so the experimental
server was restarted with an 8192-token model context:

```bash
VLLM_MAX_MODEL_LEN=8192 bash scripts/experiments/start_vllm_wsl.sh
```

The startup script now accepts `VLLM_MAX_MODEL_LEN` while retaining its
original 2048-token default for Sprint 2 reproducibility.

The backend was built as the temporary image
`knowledgechat-ai-backend:sprint35` and run on port 8000 with the existing
Docker volume and runtime-only vLLM environment overrides. Production Compose
was not changed.

## Preflight Results

- `GET http://localhost:8001/v1/models`: HTTP 200.
- Served model: `Qwen/Qwen2.5-0.5B-Instruct`.
- Ollama `/api/embed`: successful.
- Embedding dimension: 768.
- Collection count: 1481.
- Backend health: HTTP 200.
- Backend log: `LLM provider selected provider=vllm`.
- No Ollama generation model was loaded.

## Initial Warning and Resolution

With `--max-model-len 2048`, one short vLLM request succeeded and three longer
RAG requests were rejected by vLLM. KnowledgeChat returned safe deterministic
fallbacks. This was a runtime context-capacity issue, not a retrieval or
provider-selection failure.

The server was restarted at 8192 tokens. The same full validation then passed
7/7 with five successful vLLM calls. No production setting or code path was
changed to resolve the runtime issue.

## In-Domain Live Results

| Case | Duration (s) | Sources | Expected family | HTTP |
| --- | ---: | ---: | --- | ---: |
| `VLAN nedir?` | 2.467979 | 5 | Present | 200 |
| SSL VPN navigation | 0.185619 | 1 | Present | 200 |
| OSPF multipart | 2.541305 | 2 | Present | 200 |
| IPSec VPN vs SSL VPN | 4.583994 | 3 | Present | 200 |
| Rapor Ayarları fields | 2.471719 | 1 | Present | 200 |

All answers were non-empty and all included citations. The total measured run
duration was 12.650 seconds.

### Manual Grounding Observation

The sprint primarily evaluates pipeline correctness, not parity with Gemma
3 12B. The small model showed these quality limitations:

- VLAN included broadly related SD-WAN material beyond the most direct guide.
- OSPF included an unsupported command-line example after supported steps.
- The VPN comparison was repetitive and did not express a clean comparison.
- Navigation and report-field responses stayed closely aligned with citations.

These observations are why the decision is conditional rather than an
unqualified production-quality approval.

## Out-of-Domain Results

| Question | Duration (s) | Sources | Result |
| --- | ---: | ---: | --- |
| `hamburger faydalı mı?` | 0.085037 | 0 | Correct no-answer |
| İstanbul weather question | 0.114289 | 0 | Correct no-answer |

Backend logs recorded `reason=no_antikor_domain_signal` for both. No provider
request followed either rejection, so vLLM was not called.

## Citation Validation

Every in-domain response contained the unchanged source fields:

- `document_name`
- `relative_path`
- `section_title`
- `chunk_index`
- `similarity_score`
- `language`

Relative paths, document names, section titles, and chunk indices were
preserved. Duplicate citation count was zero for every response. All cited
paths belonged to the expected broad document family, though the small model's
use of that evidence was not consistently high quality.

## Provider Isolation Evidence

For the successful final run, backend logs contained five matching pairs of:

```text
Provider request started provider=vllm
Provider request succeeded provider=vllm
```

The provider implementation sends those calls to
`/v1/chat/completions`. No provider failures or silent fallbacks occurred in
the successful run. Ollama exposed only `nomic-embed-text`; no Gemma or other
Ollama generation model was loaded. The two out-of-domain requests generated
no provider-request log entries.

## GPU Memory

| Point | Observed memory |
| --- | ---: |
| vLLM loaded at 2048 context | 5870 MiB |
| vLLM plus embedding preflight | 6273 MiB |
| Successful 8192-context run peak | 6179 MiB |
| Highest observed during Sprint 3.5 | 6325 MiB |

The observed peak remained within the RTX 4060's 8 GB VRAM.

## Validation Script

`scripts/experiments/test_live_vllm_rag.py`:

- calls the real KnowledgeChat HTTP endpoint;
- includes five in-domain and two out-of-domain defaults;
- accepts a base URL and optional JSON question file;
- measures each request with `time.perf_counter`;
- records HTTP status, response, duration, answer length, citations, names,
  paths, and similarity scores;
- persists local JSON results beneath `work/`;
- exits non-zero on a required structural failure;
- does not start services or mutate knowledge/vector data.

The generated result JSON is ignored and is not committed.

## Cleanup

The temporary backend container and WSL vLLM server were stopped after
validation. The temporary Ollama model allocation was released. No vector
data, knowledge files, benchmark results, or production service definitions
were changed.

## Production Impact

- Ollama remains the default provider.
- Retrieval thresholds and behavior are unchanged.
- Embedding behavior is unchanged.
- Citation behavior and API schema are unchanged.
- ChromaDB was neither redesigned nor rebuilt.
- Frontend behavior is unchanged.
- Historical benchmark questions and results are unchanged.

## Sprint Decision

**CONDITIONAL GO**

The real RAG pipeline works end to end with vLLM, citations are preserved,
provider isolation is confirmed, and out-of-domain short-circuiting remains
intact. The small smoke-test model is not reliable enough for production
answer-quality conclusions.

## Readiness for LMCache

The provider boundary is technically ready for a controlled LMCache
experiment. Before integrating LMCache, repeat this runner with a
representative answer-quality model and a context limit of at least 8192.
Use that run as the uncached latency and quality baseline. Do not treat the
0.5B model's answer quality as a production baseline.
