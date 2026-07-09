# KnowledgeChat AI

KnowledgeChat AI is an offline-first knowledge assistant that answers questions
from administrator-maintained Markdown documents. It uses Ollama for local chat
and embedding models, ChromaDB for vector storage, and Retrieval-Augmented
Generation (RAG) to return grounded answers with citation metadata.

## Architecture

```text
React frontend
      ↓ POST /api/v1/chat
FastAPI → RetrievalService → ChromaDB
      ↓                       ↑
PromptBuilder              Embeddings
      ↓                       ↑
Ollama chat model      Ollama embedding model
```

Knowledge is prepared separately:

```text
knowledge_base/ → indexer → embeddings → persistent ChromaDB
```

## Features

- Local, single-turn RAG chat
- Markdown assistant responses
- Source citations without exposing chunk text or embeddings
- Administrator-managed Markdown knowledge base
- Incremental SHA-256-based indexing
- Persistent local ChromaDB storage
- Responsive React interface
- Local or Docker Compose development setup

## Tech Stack

- Python 3.12, FastAPI, Pydantic Settings, Uvicorn
- React 19, TypeScript, Vite, Tailwind CSS
- Ollama HTTP API
- ChromaDB
- Docker Compose

## Requirements

For a fully local setup:

- Python 3.12+
- Node.js compatible with Vite 8
- Ollama

For the container setup:

- Docker with Docker Compose
- Ollama running on the host machine

## Ollama and Models

Start Ollama and pull the configured chat and embedding models:

```bash
ollama serve
ollama pull gemma3
ollama pull nomic-embed-text
```

Ollama remains an external local dependency. Docker Compose does not start an
Ollama container.

## Environment Setup

Local backend:

```bash
cp backend/.env.example backend/.env
```

Local frontend:

```bash
cp frontend/.env.example frontend/.env
```

Docker Compose optionally reads overrides from the repository root:

```bash
cp .env.example .env
```

Important backend variables:

| Variable | Purpose | Local default |
| --- | --- | --- |
| `APP_NAME` | FastAPI application name | `KnowledgeChat AI Backend` |
| `APP_VERSION` | Application version | `0.1.0` |
| `ENVIRONMENT` | Runtime environment label | `development` |
| `API_V1_PREFIX` | API route prefix | `/api/v1` |
| `OLLAMA_HOST` | Ollama HTTP API | `http://localhost:11434` |
| `CHAT_MODEL` | Chat generation model | `gemma3` |
| `EMBEDDING_MODEL` | Embedding model | `nomic-embed-text` |
| `VECTOR_DB_PATH` | Persistent ChromaDB path | `./data/chroma` |
| `VECTOR_COLLECTION_NAME` | Chroma collection | `knowledgechat` |
| `RETRIEVAL_TOP_K` | Maximum retrieved chunks | `5` |
| `REQUEST_TIMEOUT` | Ollama timeout in seconds | `60` |
| `CORS_ORIGINS` | Comma-separated browser origins | `http://localhost:5173` |

The frontend uses:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

## Run Locally

### 1. Start the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.

### 2. Index the Knowledge Base

Add administrator-reviewed Markdown files under `knowledge_base/`, then run:

```bash
cd backend
source .venv/bin/activate
python scripts/index_knowledge.py
```

The script updates the incremental cache and stores embeddings in the configured
local ChromaDB path. It does not create an upload or admin endpoint.

### 3. Start the Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Run with Docker Compose

Keep Ollama running on the host, then run:

```bash
cp .env.example .env
docker compose up --build
```

The services are available at:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/api/v1/health`

The backend reaches host Ollama through
`http://host.docker.internal:11434`. Linux compatibility is provided through
the `host-gateway` mapping.

Index repository knowledge inside the running backend container:

```bash
docker compose exec backend python scripts/index_knowledge.py
```

The `knowledge_base/` directory is mounted read-only. ChromaDB and the
incremental index cache persist in the Docker volume named `backend_data`.

Stop the services without deleting indexed data:

```bash
docker compose down
```

To intentionally delete the Docker-managed vector data:

```bash
docker compose down --volumes
```

## Manual RAG Test

1. Start Ollama and pull both models.
2. Add a Markdown document under `knowledge_base/`.
3. Start the backend or Docker Compose.
4. Run the knowledge indexing command.
5. Start/open the frontend.
6. Ask a question covered by the indexed document.
7. Verify the answer and source cards shown below it.

## API Examples

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

Chat request:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain Python classes."}'
```

Example response:

```json
{
  "response": "A class defines data and behavior...",
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

## Repository Structure

```text
knowledgechat-ai/
├── backend/          # FastAPI, RAG, indexing, and vector storage
├── frontend/         # React chat interface
├── knowledge_base/   # Curated Markdown documents and manifest
├── docs/             # Architecture and milestone documentation
└── docker-compose.yml
```

## Current Limitations

- Ollama and the configured models must be installed locally.
- Chat is single-turn with no conversation memory or persistence.
- Responses are not streamed.
- There is no authentication, admin panel, or document upload UI.
- Retrieval does not include filtering, reranking, or hybrid search.
- Docker setup targets local development, not cloud deployment.
