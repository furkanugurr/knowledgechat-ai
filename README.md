# KnowledgeChat AI

KnowledgeChat AI is an offline-first AI knowledge assistant powered by Ollama and Retrieval-Augmented Generation (RAG). It is designed to answer user questions from a curated knowledge base maintained exclusively by administrators.

## Goals

- Keep knowledge-assisted conversations private and locally operable.
- Ground answers in an administrator-curated knowledge base.
- Provide a modular foundation that can grow without coupling the user interface, application services, and knowledge infrastructure.
- Support production-ready development practices, maintainability, and scalable deployment.

## Technology Stack

The current stack includes:

- **Backend:** Python 3.12, FastAPI, Pydantic Settings
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Local AI runtime:** Ollama
- **Retrieval:** ChromaDB
- **Container orchestration:** Docker Compose

## Planned Architecture

The system is a modular application with:

- A frontend for end-user knowledge chat and citation display.
- A backend responsible for application orchestration and knowledge retrieval.
- Ollama providing local chat and embedding models.
- ChromaDB storing and searching vectorized knowledge.
- Administrator-managed ingestion processes for maintaining the curated knowledge base.

Application boundaries and technology decisions will be recorded in `docs/adr/` before implementation.

## Repository Structure

```text
knowledgechat-ai/
├── backend/            # Backend application workspace
├── frontend/           # Frontend application workspace
├── knowledge_base/     # Administrator-maintained Markdown knowledge
├── docs/
│   ├── adr/            # Architecture Decision Records
│   ├── milestones/     # Milestone plans and outcomes
│   ├── prompts/        # Versioned prompt documentation
│   └── README.md       # Documentation guide
├── scripts/            # Repository automation and maintenance scripts
├── .github/
│   └── workflows/      # Continuous integration workflows
├── README.md           # Project overview
├── LICENSE             # MIT License
├── .gitignore          # Ignored files and generated artifacts
├── .env.example        # Environment variable template
└── docker-compose.yml  # Local orchestration skeleton
```

## Run Locally

Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend runs at `http://localhost:5173` and calls the backend configured by
`VITE_API_BASE_URL`.

## Development Roadmap

1. Establish architecture decisions and development standards.
2. Scaffold the backend and frontend workspaces.
3. Define the curated knowledge ingestion workflow.
4. Implement local model and retrieval integrations.
5. Build user and administrator experiences.
6. Add production hardening, observability, testing, and deployment workflows.
