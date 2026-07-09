# KnowledgeChat AI Backend

The backend provides the HTTP application foundation for KnowledgeChat AI. It
currently supports service health reporting and stateless, single-turn response
generation through a provider-independent LLM interface. It can also generate
embeddings for prepared knowledge chunks through a separate provider contract.
Ollama is the current implementation for both contracts, and ChromaDB provides
persistent local vector storage. Retrieval, memory, and conversation history
are not included.

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
│   ├── schemas/        # Validated API request and response schemas
│   ├── services/       # Provider-independent application services
│   ├── system_prompts/
│   │   └── default.txt # Default system instructions
│   ├── utils/          # Future shared utilities
│   ├── vectorstore/    # Vector storage contracts and ChromaDB provider
│   └── main.py         # FastAPI application factory and entry point
├── data/
│   └── index_cache.json # Incremental knowledge index state
├── tests/              # Backend test suite
├── .env.example        # Environment configuration template
├── Dockerfile          # Backend container definition
└── requirements.txt    # Python runtime dependencies
```

## Architecture

The HTTP and provider layers are separated by an application service:

```text
Chat Router
    ↓
ChatService
    ├──→ PromptBuilder
    ↓
LLMProvider
    ↓
OllamaProvider
    ↓
Ollama HTTP API
```

- The router validates HTTP input and maps provider errors to HTTP responses.
- `ChatService` coordinates prompt construction and response generation.
- `PromptBuilder` combines managed system and developer prompts with the user
  message.
- `LLMProvider` defines the provider-independent generation and health contract.
- `OllamaProvider` contains all Ollama-specific HTTP and response handling.

Future providers can implement `LLMProvider` and be selected in the application
composition root without changing the router, chat service, or prompt builder.

## Knowledge Pipeline

Administrators maintain source documents as Markdown under the repository-level
`knowledge_base/` directory. End users cannot upload documents.

```text
KnowledgeIndexer
    ├──→ ManifestLoader
    ├──→ IndexCache
    └──→ KnowledgeLoader
              ↓
          MarkdownParser
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
- `KnowledgeLoader` recursively discovers contained Markdown documents.
- `MarkdownParser` preserves source content, headings, and fenced code blocks.
- `TextChunker` keeps heading sections separate and splits long sections using
  configurable character size and overlap.
- `MetadataExtractor` attaches source, section, ordering, language, and
  filesystem timestamp metadata.

The root `knowledge_base/README.md` is administrative documentation and is not
loaded as knowledge. Detailed writing and naming rules are documented there.

### Manifest

`knowledge_base/manifest.yaml` is loaded and validated on every indexing run:

```yaml
version: 1
default_language: en
chunk_size: 1200
chunk_overlap: 150
supported_extensions:
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

### Why Markdown

Markdown is human-readable, diff-friendly, version-controlled, portable, and
supports the headings and fenced code blocks needed for meaningful technical
knowledge segmentation. It also keeps knowledge review independent from a
database or proprietary editor.

### Future RAG Integration

The knowledge pipeline produces a validated `IndexResult`. The embedding layer
can consume its changed chunks without altering loading, parsing, chunking,
incremental detection, or reporting. Vector persistence and retrieval remain
future stages.

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
persist vectors. A future Vector Store layer can consume
`EmbeddingResult.embedded_chunks` and handle `IndexResult.removed_files`
without changing either indexing or embedding generation.

No vector search, retrieval, or RAG behavior is implemented.

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

The provider does not expose query or similarity-search methods. A future
Retrieval layer can depend on a separate retrieval contract without changing
indexing, embedding generation, or persistence.

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

Start Ollama and download the model configured by `CHAT_MODEL`:

```bash
ollama serve
ollama pull gemma3
ollama pull nomic-embed-text
```

Configure `.env` with the local Ollama API, selected model, and request timeout:

```dotenv
OLLAMA_HOST=http://localhost:11434
CHAT_MODEL=gemma3
EMBEDDING_MODEL=nomic-embed-text
VECTOR_DB_PATH=./data/chroma
VECTOR_COLLECTION_NAME=knowledgechat
REQUEST_TIMEOUT=60
```

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
  "response": "Python is ..."
}
```

## Tests

The tests replace the Ollama dependency, so a running model is not required:

```bash
python -m unittest discover -s tests -v
```
