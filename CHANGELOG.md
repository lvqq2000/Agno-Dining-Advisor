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

For detailed implementation notes and file-level changes, see the repo commits for this release.
