# KnowledgeChat AI Backend

The backend provides the HTTP application foundation for KnowledgeChat AI. It
currently supports service health reporting and stateless, single-turn response
generation through a provider-independent LLM interface. It can also generate
embeddings for prepared knowledge chunks through a separate provider contract.
Ollama is the current implementation for both contracts, and ChromaDB provides
persistent local vector storage and cosine similarity retrieval. Retrieved
knowledge now augments the existing chat prompt, and source metadata is
returned as citations. Memory, streaming, and conversation history are not
included.

## Structure

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/     # Health and chat HTTP routes
│   ├── core/           # Configuration and logging infrastructure
│   ├── developer_prompts/
│   │   └── default.txt # Default developer instructions
│   ├── embedding/      # Embedding contracts, models, and Ollama provider
│   ├── knowledge/      # Knowledge loading and preparation pipeline
│   ├── models/         # Future domain and persistence models
│   ├── prompt/         # Managed prompt construction
│   ├── providers/      # LLM contract and provider implementations
│   ├── retrieval/      # Semantic retrieval models and orchestration
│   ├── schemas/        # Validated API request and response schemas
│   ├── services/       # Provider-independent application services
│   ├── system_prompts/
│   │   └── default.txt # Default system instructions
│   ├── utils/          # Future shared utilities
│   ├── vectorstore/    # Vector storage contracts and ChromaDB provider
│   └── main.py         # FastAPI application factory and entry point
├── data/
│   └── .gitkeep        # Runtime data directory placeholder
├── scripts/
│   └── index_knowledge.py # Local end-to-end indexing utility
├── tests/              # Backend test suite
├── .env.example        # Environment configuration template
├── Dockerfile          # Backend container definition
└── requirements.txt    # Python runtime dependencies
```

## RAG Chat Architecture

The router remains isolated from retrieval and provider details:

```text
Chat Router
    ↓
ChatService
    ├──→ RetrievalService
    │         ↓
    │   Relevant chunks
    ├──→ PromptBuilder
    ↓
LLMProvider
    ↓
OllamaProvider
    ↓
Ollama HTTP API
```

- The router validates HTTP input and calls only `ChatService`.
- `ChatService` coordinates retrieval, prompt construction, and generation.
- `RetrievalService` returns the most relevant indexed knowledge chunks.
- `PromptBuilder` combines managed system and developer prompts with the user
  message and optional knowledge context.
- `LLMProvider` defines the provider-independent generation and health contract.
- `OllamaProvider` contains all Ollama-specific HTTP and response handling.

Future providers can implement `LLMProvider` and be selected in the application
composition root without changing the router, chat service, or prompt builder.

If retrieval returns no chunks or the collection is empty, chat returns a safe
knowledge-base fallback without calling the LLM.

## Knowledge Pipeline

Administrators maintain source documents as Markdown (`.md`) or Word (`.docx`)
under the repository-level `knowledge_base/` directory. End users cannot upload
documents.

```text
KnowledgeIndexer
    ├──→ ManifestLoader
    ├──→ IndexCache
    └──→ KnowledgeLoader
              ↓
          KnowledgeParser
            ├── MarkdownParser
            └── WordParser
              ↓
          TextChunker
              ↓
          MetadataExtractor
              ↓
          IndexResult
```

- `KnowledgeIndexer` orchestrates the complete pipeline and produces a
  serializable result and report.
- `ManifestLoader` validates dynamic language, extension, chunk size, and
  overlap configuration.
- `IndexCache` persists versioned incremental state using atomic JSON writes.
- `KnowledgeLoader` recursively discovers contained Markdown and Word
  documents.
- `KnowledgeParser` dispatches each file to the correct format-specific parser.
- `MarkdownParser` preserves source content, headings, and fenced code blocks.
- `WordParser` extracts Word paragraphs, heading styles, and simple table text.
- `TextChunker` keeps heading sections separate and splits long sections using
  configurable character size and overlap.
- `MetadataExtractor` attaches source, section, ordering, language, and
  filesystem timestamp metadata.

The root `knowledge_base/README.md` is administrative documentation and is not
loaded as knowledge. Detailed writing and naming rules are documented there.

### Manifest

`knowledge_base/manifest.yaml` is loaded and validated on every indexing run:

```yaml
version: 2
default_language: en
chunk_size: 1200
chunk_overlap: 150
supported_extensions:
  - docx
  - md
```

Chunk settings are not hardcoded in the indexer. The complete normalized
manifest receives its own SHA-256 fingerprint. A configuration change safely
re-indexes documents because existing chunks may no longer match the requested
size, overlap, language, or extension policy.

### Incremental Indexing

Every discovered document is streamed through SHA-256 hashing. The digest is
compared with `backend/data/index_cache.json`:

- New paths are indexed.
- Changed hashes are re-indexed.
- Matching hashes are skipped without parsing or chunking.
- Removed paths are deleted from cache and returned in `removed_files`.

Unchanged files are read only once for hashing. `IndexResult.chunks` contains
only new or changed chunks, keeping memory and future embedding work
proportional to the change set.

The cache file is generated at runtime and intentionally excluded from Git.

The versioned cache uses this structure:

```json
{
  "version": 1,
  "manifest_hash": "<sha256>",
  "files": {
    "python/oop.md": {
      "relative_path": "python/oop.md",
      "sha256": "<sha256>",
      "indexed_at": "2026-07-09T10:00:00Z",
      "chunk_count": 3
    }
  }
}
```

Cache writes use a temporary file followed by an atomic replacement. Document
content and generated chunks are deliberately not persisted in this cache.

### Why Markdown and Word

Markdown is human-readable, diff-friendly, version-controlled, portable, and
supports the headings and fenced code blocks needed for meaningful technical
knowledge segmentation. It also keeps knowledge review independent from a
database or proprietary editor.

Word (`.docx`) is supported for administrator-maintained documents that already
exist in business-friendly Word format. The parser intentionally extracts text,
headings, and simple tables only; it does not depend on visual layout, comments,
or tracked changes for retrieval quality.

### RAG Integration

The knowledge pipeline produces a validated `IndexResult`. The embedding layer
can consume its changed chunks without altering loading, parsing, chunking,
incremental detection, or reporting. Retrieval uses the stored vectors, and
`ChatService` passes the resulting chunks to `PromptBuilder` as internal
knowledge context.

## Embedding Layer

Embedding generation is a separate pipeline stage:

```text
IndexResult.chunks
        ↓
EmbeddingService
        ↓
EmbeddingProvider
        ↓
OllamaEmbeddingProvider
        ↓
POST /api/embed
        ↓
EmbeddingResult
```

- `EmbeddingService` accepts prepared `KnowledgeChunk` objects, requests a
  batch of vectors, preserves chunk order, and returns `EmbeddedChunk` objects.
- `EmbeddingProvider` defines provider-independent batch generation and health
  checking.
- `OllamaEmbeddingProvider` owns Ollama HTTP communication, timeout handling,
  response validation, and model selection.
- `EmbeddingResult` is serializable and reports chunk count, vector dimensions,
  and execution duration.

Embedding is deliberately separate from `KnowledgeIndexer`. Indexing decides
which documents changed and prepares text; embedding performs model inference.
This keeps filesystem processing deterministic and lets another embedding
provider be introduced without changing the knowledge pipeline.

The Ollama integration uses the native `/api/embed` batch endpoint. It does not
persist vectors. The Vector Store layer consumes
`EmbeddingResult.embedded_chunks` and handles `IndexResult.removed_files`
without changing either indexing or embedding generation.

The embedding layer itself performs no vector search or retrieval; those
responsibilities remain in their dedicated layers.

## Vector Store Layer

Generated embeddings are persisted through a provider-independent service:

```text
EmbeddingResult + IndexResult.removed_files
                    ↓
            VectorStoreService
                    ↓
          VectorStoreProvider
                    ↓
      ChromaVectorStoreProvider
                    ↓
       Persistent ChromaDB files
```

- `VectorStoreService` coordinates document removals and embedding upserts.
- `VectorStoreProvider` defines collection creation, upsert, delete, collection
  statistics, and health contracts.
- `ChromaVectorStoreProvider` uses a lazy `PersistentClient`, automatically
  creates the configured collection, and supplies pre-generated embeddings.
- `VectorStoreResult` reports upserted, deleted, and total vector counts plus
  execution duration.

Record IDs are deterministic SHA-256 hashes of `relative_path` and
`chunk_index`. Repeating an upsert updates the existing record instead of
creating a duplicate. When a changed document produces fewer chunks, stale
chunk IDs for that document are removed before upsert.

### ChromaDB Configuration

```dotenv
VECTOR_DB_PATH=./data/chroma
VECTOR_COLLECTION_NAME=knowledgechat
```

The collection name and persistence path are never hardcoded. ChromaDB stores
its database files beneath `VECTOR_DB_PATH` and reloads them when a new provider
instance starts. For containers, this path must be mounted as a persistent
volume when container orchestration is introduced.

Every vector stores the original chunk text as its Chroma document and these
scalar metadata fields:

```text
document_name
relative_path
section_title
chunk_index
language
```

The provider exposes only unfiltered vector similarity search. Metadata
filtering and reranking are deliberately not implemented.

## Retrieval Layer

Semantic retrieval remains independent from chat generation:

```text
User question
      ↓
RetrievalService
      ↓
Retriever
      ├──→ EmbeddingService.embed_text()
      ↓
VectorStoreProvider.search()
      ↓
ChromaDB cosine query
      ↓
RetrievalResult
```

- `RetrievalService` applies the configured result limit and returns a
  serializable result with execution duration.
- `Retriever` generates one question embedding, executes vector search,
  validates metadata, and sorts results by descending similarity.
- `VectorStoreProvider.search()` keeps retrieval independent from ChromaDB.
- `ChromaVectorStoreProvider` queries with the pre-generated question vector;
  it does not use a Chroma embedding function.

New Chroma collections are configured with HNSW cosine distance. Existing
collections using another metric are rejected to prevent misleading scores.
Chroma returns distances where lower is better, so the provider normalizes each
result to cosine similarity with `1 - distance` and returns the highest score
first.

Each `RetrievedChunk` contains:

```text
chunk_text
similarity_score
document_name
relative_path
section_title
chunk_index
language
```

`RETRIEVAL_TOP_K` controls the maximum number of returned chunks and defaults
to `5`. Empty collections, embedding failures, search failures, and malformed
results have distinct retrieval exceptions.

This layer supplies validated context candidates to the RAG chat flow. It still
does not perform prompt construction or call the chat model directly.

## RAG Prompt Context

`PromptBuilder` preserves its original format when no context is provided. For
RAG chat, it inserts a clearly separated section before the user message:

```text
SYSTEM PROMPT

DEVELOPER PROMPT

KNOWLEDGE CONTEXT
## Knowledge Context

### Source 1
Document: python/oop.md
Section: Classes
Content:
...

USER MESSAGE
```

The default system prompt instructs the model to use provided context, avoid
unsupported claims, and explicitly report when information is absent from the
knowledge base. `PromptBuilder` uses retrieved chunk text only as internal model
context; citation response construction remains the responsibility of
`ChatService`.

## Citation Support

Each successful RAG response includes source metadata derived from the
retrieved chunks. Sources remain ordered by retrieval relevance. Duplicate
entries with the same `relative_path`, `section_title`, and `chunk_index` are
included only once.

Each source contains:

- `document_name`
- `relative_path`
- `section_title`
- `chunk_index`
- `similarity_score`
- Optional `language`

Chunk text is deliberately excluded from the public response. It may contain
large knowledge-base passages and is needed only for internal prompt context.
Embeddings are never exposed.

## Local Knowledge Indexing

Before testing RAG chat, place administrator-reviewed Markdown or Word
documents under `knowledge_base/`, then run the existing pipeline end to end:

```bash
cd backend
python scripts/index_knowledge.py
```

The script:

1. Loads and incrementally indexes repository Markdown and Word documents.
2. Generates embeddings with the configured Ollama embedding model.
3. Upserts vectors and removes deleted documents in ChromaDB.
4. Prints only files scanned/indexed, chunks embedded, and vectors stored.

The orchestration core is importable and testable without starting Ollama or
ChromaDB. No indexing API endpoint or admin panel is added.

## Run Locally

Python 3.12 or newer is required.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Ollama

Ollama, the configured chat model, and the configured embedding model must be
available locally:

```bash
ollama serve
ollama pull gemma3
ollama pull nomic-embed-text
```

Configure `.env` with the local Ollama API, selected model, and request timeout:

```dotenv
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
OLLAMA_HOST=http://localhost:11434
CHAT_MODEL=gemma3
EMBEDDING_MODEL=nomic-embed-text
VECTOR_DB_PATH=./data/chroma
VECTOR_COLLECTION_NAME=knowledgechat
RETRIEVAL_TOP_K=5
REQUEST_TIMEOUT=60
CORS_ORIGINS=http://localhost:5173
```

`CORS_ORIGINS` is a comma-separated list of browser origins allowed to call the
API. Its default permits the local Vite development server.

## Manual RAG Test

1. Add at least one Markdown or Word knowledge document beneath
   `knowledge_base/`.
2. Start Ollama and ensure both configured models are available.
3. Run `python scripts/index_knowledge.py` from `backend/`.
4. Start the backend with `uvicorn app.main:app --reload`.
5. Send a chat request:

```bash
curl -i http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What does the knowledge base say about Python classes?"}'
```

The success response includes citations:

```json
{
  "response": "...",
  "sources": [
    {
      "document_name": "oop.md",
      "relative_path": "python/oop.md",
      "section_title": "Classes",
      "chunk_index": 2,
      "similarity_score": 0.87,
      "language": "en"
    }
  ]
}
```

Still intentionally excluded:

- Conversation memory
- Streaming
- Reranking, hybrid search, and filtering

## Available Endpoints

### `GET /api/v1/health`

Returns HTTP `200 OK` when the backend is running:

```json
{
  "status": "ok",
  "service": "KnowledgeChat AI Backend"
}
```

Test it from another terminal:

```bash
curl -i http://localhost:8000/api/v1/health
```

### `POST /api/v1/chat`

Generates one response for one message:

```bash
curl -i http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain Python."}'
```

```json
{
  "response": "Python is ...",
  "sources": [
    {
      "document_name": "oop.md",
      "relative_path": "python/oop.md",
      "section_title": "Core Idea",
      "chunk_index": 0,
      "similarity_score": 0.91,
      "language": "en"
    }
  ]
}
```

## Tests

The tests replace the Ollama dependency, so a running model is not required:

```bash
python -m unittest discover -s tests -v
```
