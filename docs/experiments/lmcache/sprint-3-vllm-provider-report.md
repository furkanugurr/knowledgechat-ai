# Experimental Sprint 3 — Optional vLLM Provider Integration

## Scope

Sprint 3 adds vLLM as an optional chat-generation provider behind the existing
`LLMProvider` contract. Ollama remains the default and continues to provide
embeddings. Retrieval, ChromaDB, citations, indexing, the public API, frontend,
and production Docker Compose behavior are unchanged. LMCache is not included.

The integration uses vLLM's OpenAI-compatible
`POST /v1/chat/completions` API. The experimental model is
`Qwen/Qwen2.5-0.5B-Instruct`, served by the Sprint 2 WSL workflow.

## Configuration

```dotenv
LLM_PROVIDER=ollama
VLLM_BASE_URL=http://localhost:8001
VLLM_MODEL=Qwen/Qwen2.5-0.5B-Instruct
VLLM_API_KEY=
VLLM_REQUEST_TIMEOUT_SECONDS=120
```

Supported provider values are `ollama` and `vllm`. Values are normalized to
lowercase and unknown values fail configuration validation. When
`LLM_PROVIDER` is omitted, Ollama is selected.

For a backend container reaching the WSL server through Windows, use
`VLLM_BASE_URL=http://host.docker.internal:8001` as a runtime-only override.

## Architecture

```text
FastAPI lifespan
    ↓
provider factory
    ├── ollama → OllamaProvider → /api/generate
    └── vllm   → VLLMProvider   → /v1/chat/completions
                    ↓
                ChatService
                    ↓
       unchanged response and citations
```

The factory lives only at the composition boundary. Provider selection does
not appear in the chat route or `ChatService`.

## Provider Behavior

`VLLMProvider`:

- uses the managed asynchronous `httpx` lifecycle;
- sends one final RAG prompt as an OpenAI-compatible user message;
- disables streaming and uses deterministic temperature zero;
- applies the existing output token limit;
- supports an optional bearer API key;
- validates `choices[0].message.content`;
- maps timeouts and unavailable/invalid responses to shared exceptions;
- logs metadata without logging prompts or answers;
- checks health through `GET /v1/models`.

## Automated Validation

- 21 focused provider, selection, error, lifecycle, and mocked HTTP integration
  tests were added.
- The mocked endpoint integration verifies that a vLLM-generated answer keeps
  the existing response schema and citation metadata.
- The complete backend suite, frontend production build, Python compilation,
  and `git diff --check` are required before publication.

## Manual Comparison

`scripts/experiments/compare_llm_providers.py` sends the same prompt directly
to Ollama and vLLM, reports model identity, success, duration, answer, and
errors, and can persist JSON with `--output`.

```powershell
python scripts/experiments/compare_llm_providers.py `
  --prompt "VLAN kavramını iki cümlede açıkla." `
  --output work/experiments/sprint-3-provider-comparison.json
```

The output path is local experimental data and is not committed.

## Live Smoke Result

The Sprint 2 vLLM server was started with the experimental Qwen model and
`GET /v1/models` succeeded. A real comparison request reached vLLM and returned
a non-empty response in **4.049661 seconds**. This validates the configured
OpenAI-compatible request and response path. The small model's repetitive
Turkish answer is not treated as an answer-quality result.

The Ollama side of that simultaneous direct comparison returned HTTP 500 while
vLLM occupied the constrained GPU. The result was retained as a failed
measurement rather than retried or presented as successful.

An end-to-end RAG HTTP smoke was **not run**. The Docker volume
`knowledgechat-ai_backend_data` existed, but the configured `knowledgechat`
collection was absent. The experiment did not silently rebuild or re-index the
collection. Consequently no claim is made here about live vLLM RAG citations,
out-of-domain routing, or end-to-end latency. Those behaviors remain covered
by mocked integration tests until an existing indexed collection is available.

After the direct smoke, the temporary vLLM process was stopped and port 8001
was confirmed closed.

## Rollback

Set `LLM_PROVIDER=ollama` or remove the variable, then restart the backend.
No re-indexing, database migration, knowledge-base change, or frontend change
is needed.

## Limitations and Next Step

- The small Qwen model validates compatibility, not production answer quality.
- The vLLM path is experimental and is not enabled in production Compose.
- Embeddings still require Ollama.
- LMCache remains deferred until the provider boundary is validated.
- A later experiment may compare repeatable RAG latency and answer quality
  before evaluating any cache layer.
