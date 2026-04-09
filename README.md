# Agno-Dining-Advisor

Agno Dining Advisor is a simple open-source restaurant recommendation tool. For now, it only supports restaurants in Melbourne. It is built using Agno with an AI-powered workflow, including database-driven prompt construction, semantic matching (CAG), retrieval-augmented generation (RAG), conditional logic, and SSE streaming output.

## Table of Contents

- [Agno-Dining-Advisor](#agno-dining-advisor)
  - [Table of Contents](#table-of-contents)
  - [Architecture Overview](#architecture-overview)
  - [Setup Instructions](#setup-instructions)
    - [Prerequisites](#prerequisites)
    - [1. Open a terminal and clone the Repository](#1-open-a-terminal-and-clone-the-repository)
    - [2. Navigate to the project directory](#2-navigate-to-the-project-directory)
    - [3. Environment Setup](#3-environment-setup)
  - [How to run the project](#how-to-run-the-project)
    - [1. Install Make (if not already installed)](#1-install-make-if-not-already-installed)
    - [2. Run the project](#2-run-the-project)
    - [3. Access the test interface](#3-access-the-test-interface)
    - [3. Run tests](#3-run-tests)
    - [Future Improvements](#future-improvements)

## Architecture Overview

```
.
├── alembic/                           # DB migration scripts (alembic)
├── app/                               # Application code (FastAPI + workflow + agents)
│   ├── agents/                        # Agent factories (CAG, RAG, generate)
│   ├── core/                          # Config and constants
│   ├── db/                            # SQLAlchemy models, session, repositories and seeds
│   │   ├── models/                    # ORM models (cag_reference_data, prompt_template, traces)
│   │   └── seeds/                     # DB seed scripts for reference data & templates
│   ├── workflows/                     # Workflow definitions and step implementations
│   ├── services/                      # Embedding, LLM callers, matching logic
│   ├── static/                        # Simple test UI (`test.html`) for SSE demo
│   └── main.py                        # FastAPI app (endpoints: /recommend, /traces, /test, /options)
├── docker-compose.yml                 # Docker compose for app + pgvector Postgres
├── Dockerfile                         # App container image
├── requirements.txt                   # Python dependencies
└── README.md                          # This document
```

Key responsibilities

- FastAPI (`app/main.py`): exposes the API and a small synchronous runner used to
  stream Server-Sent Events (SSE) back to clients while persisting per-step traces
  to Postgres for observability.
- Workflow (`app/workflows/*`): composed of small steps:
  - `intake_step` — normalize incoming form data (the canonical `feeling` field)
  - `cag_match_step` — embed the free-text input and find top-matching dining styles
  - `rag_retrieve_step` — optional retrieval against a knowledge base (pgvector)
  - `generate_*_step` — render prompts (using DB-held templates) and run generation
  - `validate_output_step` — pydantic validation of the final JSON
- Agents (`app/agents/*`): factory functions that create agent objects used by steps
  (RAG agent runs searches when `search_knowledge=True`). The app currently provides
  a small local shim for a missing `agno` library so development can proceed.
- Embeddings (`app/services/embedding_service.py`): uses sentence-transformers
  `all-mpnet-base-v2` to produce 768‑dim vectors. The seeder and runtime must use
  the same model and dimension to keep similarity calculations correct.
- Data & persistence (`app/db/*` + alembic): Postgres holds:
  - `cag_reference_data` — labeled reference text with embeddings and dining_styles
  - `prompt_templates` — generation templates with versions
  - `traces` — per-step observability records (session_id, step, input, output, status)

Runtime flow (request)

1. Client POSTs form to `/recommend` (feeling + optional cuisine/dietary).
2. App creates a `session_id` and runs the workflow steps, emitting SSE events per-step.
3. Each step writes a trace record to Postgres (used by `/traces/{session_id}`).
4. If CAG is low-confidence or absent, RAG retrieval runs to augment generation context.
5. The generator produces a JSON recommendation which is validated and streamed back.

## Setup Instructions

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started) (v20.0 or higher)
- [Git](https://git-scm.com/) - Optional, required only for running Git commands in the terminal

### 1. Open a terminal and clone the Repository

MacOS / Linux: Open Terminal

Windows: Open Git Bash, Command Prompt, or PowerShell

```bash
git clone https://github.com/lvqq2000/Agno-Dining-Advisor
```

This command downloads the repository, creates a local directory named `Agno-Dining-Advisor`.

### 2. Navigate to the project directory

```bash
cd Agno-Dining-Advisor
```

### 3. Environment Setup

Create a `.env` file in the root directory and copy the content from `.env.example` file. Fill in the required environment variables.

## How to run the project

This project uses `make` to simplify common development commands.  
`make` is a build automation tool that lets you run predefined commands (defined in a `Makefile`) with simple shortcuts, instead of typing long commands manually.

### 1. Install Make (if not already installed)

- **MacOS**
  
  ```bash
  xcode-select --install
  ```

- **Linux (Ubuntu/Debian)**
  
  ```bash
  sudo apt update
  sudo apt install make
  ```

- **Windows**
  - Use Git Bash (recommended), or
  - Install WSL and follow the Linux instructions, or
  - Install via Chocolatey:
  
    ```bash
    choco install make
    ```

### 2. Run the project

After completing the setup:

```bash
# Prepare the project and start
make setup
```

### 3. Access the test interface

Open <http://localhost:8000/test> to interact with the project through a simple UI.

### 3. Run tests

> TO DO. Not yet implemented.

```bash
# Run all tests
make test
```

Notes

- Make sure Docker is running before starting the project.
- If you encounter issues, check the .env configuration and ensure all required variables are set.

### Future Improvements

- Add unit tests, end-to-end tests and integrated tests
- Optional template versioning
- Improve error handling logic such as multiple guardrails (structural + content-level), retry attempts
- Better CAG edge cases handles for multiple strong matches
- Better structured SSE events
