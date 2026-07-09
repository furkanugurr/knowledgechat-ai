# KnowledgeChat AI Frontend

The frontend is a responsive React interface for asking questions through the
KnowledgeChat AI backend. It renders assistant responses as Markdown and shows
the citation metadata returned by the RAG chat endpoint.

## Requirements

- Node.js compatible with Vite 8
- A running KnowledgeChat AI backend

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

## Environment

`VITE_API_BASE_URL` defines the backend origin:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

The frontend sends chat requests to:

```text
${VITE_API_BASE_URL}/api/v1/chat
```

The backend must allow the frontend origin through `CORS_ORIGINS`. The default
development origin is `http://localhost:5173`.

## Run

```bash
npm run dev
```

Open `http://localhost:5173`.

## Build

```bash
npm run build
```

## Current Limitations

- Messages exist only in React state and are lost on refresh.
- Responses are not streamed.
- Authentication and administration are not included.
- Knowledge documents cannot be uploaded through the frontend.
- No conversation memory or persistent chat history is available.
