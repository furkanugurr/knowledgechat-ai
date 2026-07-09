# KnowledgeChat AI Project Summary

## Project

**KnowledgeChat AI** is an offline-first educational knowledge assistant. It
answers questions from a curated Markdown knowledge base and returns metadata
for the sources used during retrieval.

## Purpose

General chat models can answer without showing where their context came from.
This project demonstrates how Retrieval-Augmented Generation can ground a local
model in administrator-reviewed material while keeping the workflow practical
for local development and classroom presentation.

## Main Technologies

- FastAPI and Python 3.12 for the backend API
- React, TypeScript, Vite, and Tailwind CSS for the frontend
- Ollama for local chat and embedding models
- ChromaDB for persistent vector storage and similarity search
- Docker Compose for the optional full-stack development setup

## Main Modules

- `knowledge`: discovers, parses, chunks, and tracks Markdown documents
- `embedding`: defines embedding providers and the Ollama implementation
- `vectorstore`: persists embeddings through a ChromaDB provider
- `retrieval`: embeds questions and finds the most similar chunks
- `prompt`: combines managed instructions, retrieved context, and the question
- `services`: coordinates indexing, retrieval, storage, and chat workflows
- `providers`: isolates the chat model behind an LLM provider contract
- `frontend`: submits questions and renders Markdown answers with source cards

## RAG Pipeline

The indexing command reads Markdown files, creates heading-aware chunks,
generates embeddings, and stores them in ChromaDB. For a chat request, the
backend embeds the question, retrieves relevant chunks, inserts their text into
the managed prompt, and calls the local Ollama chat model. The API returns the
generated answer and deduplicated source metadata.

## Frontend

The responsive React interface keeps messages in temporary component state. It
supports a question textarea, loading and error states, Markdown answers, and
citation cards. It does not implement accounts, uploads, or persistent chat
history.

## Local-First Design

Ollama, ChromaDB, the backend, and the frontend can all run on the developer's
machine. Knowledge remains in repository Markdown files maintained by the
administrator. No hosted model provider is required for the demonstrated flow.

## Current Limitations

- Chat is single-turn and has no conversation memory.
- Responses are not streamed.
- Retrieval has no filtering, reranking, or hybrid search.
- There is no authentication, admin panel, or upload interface.
- The included knowledge base is intentionally small and educational.

## Possible Future Improvements

- Streaming model responses
- Conversation memory with clear privacy controls
- Retrieval filtering and reranking
- Automated quality evaluation for retrieval and answers
- Administrator tooling for reviewing indexing status
- Additional provider implementations behind the existing interfaces
