# Knowledge Base

This directory contains the administrator-maintained source material for
KnowledgeChat AI. End users do not upload or modify these files.

## Folder Organization

Store each Markdown (`.md`) or Word (`.docx`) document under the folder for its
primary subject:

```text
knowledge_base/
├── python/
├── fastapi/
├── react/
├── docker/
└── git/
```

Keep one focused topic per document. Create a new subject folder only when the
existing categories do not accurately describe the material.

This root `README.md` documents the collection and is excluded from knowledge
loading.

The repository includes short educational Markdown documents for Python,
FastAPI, React, Docker, and Git so the local RAG flow can be demonstrated
immediately.

`manifest.yaml` configures the collection's default language, supported file
extensions, chunk size, and chunk overlap. Update its `version` when making a
deliberate indexing-policy change. The manifest is configuration and is not
loaded as a knowledge document.

## Naming Conventions

- Use lowercase `snake_case` file names.
- Use `.md` for Markdown documents or `.docx` for Word documents.
- Prefer descriptive names such as `dependency_injection.md`.
- Avoid spaces, dates, and version numbers in file names unless they are
  essential to the subject.

## Writing Rules

- Write factual, administrator-reviewed content.
- Keep each file focused on one topic.
- State uncertainty and version-specific behavior explicitly.
- Do not include secrets, credentials, personal data, or generated chat logs.
- Update existing documents instead of creating near-duplicates.
- Write in English by default unless the knowledge base is intentionally
  maintained in another language. Turkish content is supported.

## Word Guidelines

- Use real Word heading styles such as `Heading 1`, `Heading 2`, or their
  Turkish equivalents such as `Başlık 1`.
- Keep each `.docx` file focused on one topic.
- Use normal paragraphs for body text.
- Use simple tables only when row/column structure improves clarity.
- Avoid images, text boxes, comments, tracked changes, and complex layouts for
  knowledge content.
- Do not store secrets, credentials, personal data, or generated chat logs.

## Markdown Guidelines

- Start each document with one level-one (`#`) heading.
- Use headings in order and avoid skipping levels.
- Keep paragraphs concise and place reusable context under meaningful headings.
- Use fenced code blocks with a language identifier.
- Ensure code examples are complete enough to understand in isolation.
- Use lists and tables only when they improve clarity.
- Use relative links for repository-local references.

These conventions make heading-aware chunking predictable and preserve useful
context for the retrieval pipeline.
