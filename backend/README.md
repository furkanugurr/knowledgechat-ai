# KnowledgeChat AI Backend

The backend provides the HTTP application foundation for KnowledgeChat AI. It
currently supports service health reporting and stateless, single-turn response
generation through a provider-independent LLM interface. Ollama is the current
provider implementation. Retrieval, embeddings, memory, and conversation
history are not included.

## Structure

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/     # Health and chat HTTP routes
│   ├── core/           # Configuration and logging infrastructure
│   ├── developer_prompts/
│   │   └── default.txt # Default developer instructions
│   ├── models/         # Future domain and persistence models
│   ├── prompt/         # Managed prompt construction
│   ├── providers/      # LLM contract and provider implementations
│   ├── schemas/        # Validated API request and response schemas
│   ├── services/       # Provider-independent application services
│   ├── system_prompts/
│   │   └── default.txt # Default system instructions
│   ├── utils/          # Future shared utilities
│   └── main.py         # FastAPI application factory and entry point
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
```

Configure `.env` with the local Ollama API, selected model, and request timeout:

```dotenv
OLLAMA_HOST=http://localhost:11434
CHAT_MODEL=gemma3
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
