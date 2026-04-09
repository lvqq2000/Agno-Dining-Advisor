# Changelog

All notable changes for this release are documented in this file.

## CAG Implementation - 2026-04-07

### Added

- POST /recommend endpoint that runs the multi-step recommendation workflow and streams progress via Server-Sent Events (SSE). Events are emitted per-step (e.g. `step:cag_match`, `step:generate`, `step:finished`).
- Persistent traces stored to PostgreSQL for each workflow step (session_id, step name, input/output, status, prompt_version). New GET /traces/{session_id} endpoint to retrieve them.
- Simple test UI at `app/static/test.html` (single free-text `feeling` input + Random recommendation button) with improved rendering: shows guessed dining style and friendly restaurant cards.

### Changed

- Switched runtime embedding implementation to use `sentence-transformers` (model: `all-mpnet-base-v2`) so live embeddings match seeded reference embeddings.
- CAG matching now includes a safe Python cosine-similarity fallback for small reference datasets to avoid pgvector SQL operator type issues during development.
- Workflow wiring: intake → cag_match → conditional RAG → generate (cag-driven or random) → validate. Normalizes LLM RunOutput objects to plain text before persistence/JSON serialization.

### Fixed

- Serialization issues when persisting non-JSON-native RunOutput objects (implemented safe serializer and normalization).
- Various runtime fixes: Condition constructor mismatch in workflow, embedding dimension mismatch in DB, and provider-prefixed model id handling.

### Database / Migrations

- Alembic migration updates applied for embedding vector dimension and trace table. Seed data updated with additional high-similarity reference rows for better CAG matches.

---

## RAG Implementation - 2026-04-10

### Added

- Optional RAG retrieval integrated via the `generate_with_rag` step (implemented using the agno workflow/runtime) which queries the knowledge base and places results onto `state['output']`. This replaces the earlier ad-hoc retrieval approach that did not run inside the agno workflow.

- Server-side SSE debug event `step:debug:output_preview` which emits a short preview of final outputs to aid client parsing during development.

- Add the ability to do random selection - without the need of any user input

### Changed

- Workflow branching updated to prefer RAG-backed generation when retrieval returns documents; falls back to CAG-driven generation otherwise. RAG retrieval is now executed inside the agno workflow via the `generate_with_rag` callable (previous implementation ran retrieval outside the agno runtime). Updated `app/workflows/main_workflow.py` to normalize evaluator inputs (supports both plain dict state and agno StepInput objects).

- Change the DESIGN documentation to match the current design

### Fixed

- Fixed issue where generation steps were imported as modules instead of callables; updated imports to reference actual step functions so the runner executes them and emits SSE events.