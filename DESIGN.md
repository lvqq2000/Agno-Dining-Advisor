# Design Specification

## Table of Contents

- [Design Specification](#design-specification)
  - [Table of Contents](#table-of-contents)
  - [Domain choice and rationale](#domain-choice-and-rationale)
  - [System architecture diagram](#system-architecture-diagram)
  - [Decisions Made to Limit AI First Coding Issues](#decisions-made-to-limit-ai-first-coding-issues)
  - [Database Schema Design](#database-schema-design)
    - [Tables](#tables)
    - [Output Schema (Pydantic)](#output-schema-pydantic)
      - [Expected Output Structure](#expected-output-structure)
      - [Validation Flow in Workflow](#validation-flow-in-workflow)
  - [Workflow Step Breakdown](#workflow-step-breakdown)
  - [Prompt Template Strategy](#prompt-template-strategy)
    - [Variables](#variables)
    - [Branches of Template](#branches-of-template)
    - [Prompt Structure](#prompt-structure)
  - [CAG vs. RAG Boundary](#cag-vs-rag-boundary)
    - [CAG](#cag)
    - [RAG](#rag)
  - [Error Handling Approach](#error-handling-approach)
  - [Testing Strategy](#testing-strategy)
    - [Unit Tests](#unit-tests)
    - [Integration Tests](#integration-tests)
    - [End-to-End Tests](#end-to-end-tests)
    - [AI Behaviour Tests](#ai-behaviour-tests)
  - [API Documentation](#api-documentation)
    - [POST /recommend (SSE)](#post-recommend-sse)
    - [GET /traces/{session\_id}](#get-tracessession_id)
    - [GET /options](#get-options)
    - [GET /test (UI)](#get-test-ui)
  - [Open questions and Assumptions](#open-questions-and-assumptions)
    - [Questions asked](#questions-asked)
      - [During the initial catchup](#during-the-initial-catchup)
      - [Before the design stage](#before-the-design-stage)
      - [Design finalization stage](#design-finalization-stage)
    - [Assumptions](#assumptions)

## Domain choice and rationale

I chose to develop a dining advisor that recommends restaurant options based on how the user wants to feel in a restaurant.

This domain works well with CAG because user preferences can be expressed as free text (e.g., "cheap", "romantic") and semantically matched to predefined dining styles. Based on the detected dining style and the user’s preferences, the system can apply different generation strategies, such as selecting different prompt templates.

RAG matching is used after CAG matching. It will search the stored knowledge, which are restarant recommendation webistes, to recommend restaurant based on the detected dining style.

## System architecture diagram

> Subject to Change

```text
[ Client / Browser ]
        │
        ▼
[ Frontend UI ]
- Form input (enums + free text)
- Displays SSE stream
        │
        ▼
[ Backend API (FastAPI) ]
- POST /recommend (SSE endpoint)
- GET /traces/{session_id}
        │
        ▼
[ Agno Workflow Engine ]
        │
        ├── Intake & Validation Layer
        │     - Type validation
        │
        ├── CAG Service
        │     - Loads dining_styles (PostgreSQL)
        │     - Embedding similarity search
        │
        ├── RAG Service
        │     - Query pgvector knowledge base
        │     - Hybrid search
        │
        ├── Generate Service
        │     - Fetch prompt_templates (PostgreSQL)
        │     - Resolve variables
        │     - Ask LLM (OpenAI model by default) to generate recommendation
        │
        ├── Validation Layer
        │     - Pydantic schema validation
        │
        └── Streaming Layer
              - Emits SSE events per step
        │
        ▼
[ PostgreSQL ]
- prompt_templates
- dining_styles (CAG)
- traces (logs)

[ pgvector ]
- knowledge_documents (RAG)
```

## Decisions Made to Limit AI First Coding Issues

> My approach, patterns which leverage libraries, Agno and reduce creation unneeded complete custom code.

1. Prefer Deterministic Systems Before LLM Usage
   - Used CAG to classify user's preference on dining styles instead of fully relying on LLM classification
   - Reduces:
     1. hallucination risk
     2. (possibly) token cost
     3. security risk (aviod hacker/bad user to send command to LLM directly)

2. Use LLM to make the final decision on CAG matching
   - Use for handles edge cases ambiguous match, multiple strong matches
   - Reduce creating unneeded custom code

3. Use Structured Data Over Free Text Where Possible
   - Introduced:
      - enums (cuisine, dietary requirements)
      - preprocessed (chunked) RAG documents
   - Improves:
      - retrieval quality
      - prompt clarity

4. Use Library Capabilities Instead of Custom Implementations
   - Used:
      - Agno for workflow orchestration. Generate recommendation using Agno AI Agent
      - pgvector for similarity search
      - Pydantic for validation
      - SentenceTransformer for data embedding (mainly used when creating embedding and inserting cag reference data with embedding into database)
   - Avoided building custom vector search and custom workflow engine

## Database Schema Design

### Tables

1. prompt_templates
   - Stores prompt templates
   - Includes versioning and conditions
   - Enables dynamic prompt selection
2. dining_styles (CAG reference data)
   - Contains structured intent phrases
   - Used for semantic matching with user input
   - Includes embeddings for similarity comparison
3. traces
   - Contains session id, input and output of each step in the workflow, the step name, used prompt version
   - Queryable via a simple GET endpoint

### Output Schema (Pydantic)

Defines the expected structure of the generated response to ensure consistency and correctness.

#### Expected Output Structure

The system expects the LLM to return a JSON object with the following structure:

```JSON
{
  "recommendations": [
    {
      "name": "Restaurant name",
      "location": "123 example street, Toorak, VIC 1000",
      "description": "Short summary of the restaurant"
    }
  ]
}
```

#### Validation Flow in Workflow

```text
LLM Output
   ↓
Parse JSON
   ↓
Pydantic Validation
   ↓
   ├── Valid → return to user
   └── Invalid → retry with correction prompt
```

## Workflow Step Breakdown

> Each step in the Agno workflow, its inputs/outputs, and the conditions for branching

| Step                                                      | Input                                                                | Input Type                          | Output                                        | Output Type                                                        |
| --------------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------- | --------------------------------------------- | ------------------------------------------------|
| Intake                                                    | Form submission                                                      | string, boolean, enums (as strings) | Validation result                             | boolean, error message                                         |
| CAG Matching (if user chooses to include preferences)     | User preference (free text)                                          | string                              | Relevant dining styles with confidence scores | List of tuples (dining style: string, confidence score: float)                        |
| RAG Retrieval (after CAG Matching) with Generation        | Dining style, cuisine preference, dietary requirements               | string, string, string              | Generated recommendations                     | string (JSON format) or empty array(string)                                        |
| Generation (if RAG didn't return relible recommendations) | User preferences and/or selected dining style                        | string, boolean                     | Generated recommendations                     | string (JSON format)                                         |
| Validation                                                | Generated recommendations                                            | string                              | Validation result                             | boolean, error message                                         |

Additional Notes:

- All inputs and outputs at each step are logged in a structured manner for observability and debugging.
- Conditional branching occurs:
  - after CAG Matching (based on confidence score)
  - after RAG Retrieval & Generation (based on whether RAG give good results)

## Prompt Template Strategy

> How I structure templates, what variables they'll use, and how they're selected

Templates will be stored in the database, together with version, and their condition.

### Variables

The variables will be represented by placeholders like {{cuisine}}, {{dietary_requirement}}.

**Variables:**

- cuisine
- dietary_requirement
- dining_style
- feeling (free text from user)

### Branches of Template

1. After CAG Matching -> a dining style and confidence score will be given

1.1 Good Confidence in CAG Matching and RAG Context Available

- If retrieved documents contain relevant restaurant recommendations:
  - Use a prompt template that incorporates RAG context, CAG result and user preferences
  - Ask the LLM to generate 3 recommendations based on:
    - User preferences (cuisine and dietary requirements) and dining style

1.2 No Relevant RAG Context

- If RAG doesn't return any recommendations (can't find relevant resturant based on )
  - Use a prompt template that only consider CAG result and user preferences
  - Ask the LLM to generate recommendations based on the top dining style and structured user inputs (cuisine and dietary requirements)

1. Low Confidence in CAG Matching

- If the top CAG confidence score is below a defined threshold (set as 0.5 by default):
  - Do not rely on the matched dining style
  - Use a fallback prompt template
  - Generate recommendations only based on structured user inputs (cuisine and dietary requirements)
  - Avoid directly passing raw free-text input to the LLM

### Prompt Structure

All prompts follow a consistent structure:

```text
[System Instruction]
Defines the role and behavior of the assistant

[User Context]
Structured user input (cuisine, dietary requirements, etc.)

[Optional RAG Context]
Retrieved documents (if available)

[Task Instruction]
What the model should generate

[Output Format Instruction]
Strict structure required for validation
```

Example:

```text
You are a dining recommendation assistant.

User preferences:
- Cuisine: {{cuisine}}
- Dietary requirements: {{dietary_requirement}}
- Dining style: {{dining_style}}

Based on the above, recommend 3 real restaurants in Melbourne.

For each restaurant, include:
- Name
- Location
- Short funny description (maximum 60 words)

Return the result in JSON format:
{
  "recommendations": [
    {
      "name": "",
      "location": "",
      "description": "",
    }
  ]
}
```

## CAG vs. RAG Boundary

> Where CAG (preloaded matching) and RAG (dynamic retrieval) are used, and why.

### CAG

- CAG is performed for all requests unless the user explicitly selects a random recommendation without providing input.
- It occurs after input validation and before calling the LLM.
- Free-text user input (describing user's feelings) is semantically matched to predefined dining styles using preloaded reference data.
- CAG is performed with custom functions. LLM is used to validate result and make the final decision on the result.
- This approach:
  - Enables flexible free-text input
  - Improves output quality through structured classification
  - Reduces token usage by avoiding unnecessary LLM interpretation
  - Faster and reliable implementation comparing to full LLM calls (especially useful when the reference dataset become large)
  - Avoid directly passing raw free-text input to the LLM for security reason

### RAG

- RAG is executed after CAG to determine whether relevant supporting documents exist.
- The predicted dining styles from CAG are used as part of the retrieval query.
- It is mainly used to provide factual context and reduce hallucination from the LLM.
- If no relevant documents are found, the system continues without RAG context (fallback).

## Error Handling Approach

| Step          | Errors                                                 | Approach                                                                                          |
| ------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Intake        | Input validation errors                                | Display validation errors in the UI                                                               |
| CAG Matching  | Database connection error                              | Display database connection error in the UI                                                       |
| CAG Matching  | Low confidence score (not an error but handled)        | Use fallback prompt template based on structured input instead of CAG result                      |
| RAG Retrieval | No relevant documents found (not an error but handled) | Continue without RAG context                                                                      |
| Generation    | Prompt not found                                       | Use fallback prompt (e.g., random recommendation template)                                        |
| Generation    | LLM connection error / output failure                  | Retry several times; if still failing, return error to UI (TO DO)                                 |
| Validation    | Validation failure                                     | Retry with corrective prompting (TO DO); log failures and return structured error if retries fail |

Errors will be surfaced to the user and logged in a structured manner to support both debugging and observability. Each workflow step emits structured logs containing the step name, input, output, status (success/failure), and any associated error messages. These logs are persisted with a session ID in the database, allowing them to be queried later via the trace endpoint (e.g., GET /traces/{session_id}).

For the frontend, errors are communicated through Server-Sent Events (SSE) with clearly defined event types (e.g., step:error, step:success), enabling the UI to display real-time feedback for each stage of the workflow. Where possible, the system follows a graceful degradation strategy—non-critical failures (such as low CAG confidence or missing RAG results) do not interrupt the workflow, while critical failures (such as repeated LLM or validation failures) return a structured error response.

## Testing Strategy

> What I test, how, and at what level (unit, integration, end-to-end)
> Note: only AI Behaviour Tests are implemented. Unit tests, End-to-End tests and integration tests are not yet implemented.

### Unit Tests

Focus on isolated logic for each step in the workflow:

- Input Handling
  - Validate correct input parsing
  - Handle invalid or missing inputs
- CAG Matching
  - Verify correct top match selection
  - Test confidence threshold handling
- RAG Retrieval
  - Verify documents are fetched from the database
  - Ensure successful retrieval when matches exist
  - Validate relevance of retrieved documents
  - Handle cases where no matches are found
- Prompt Construction
  - Verify correct variable injection
  - Ensure correct template selection across all branching paths
- Validation
  - Ensure output matches the expected Pydantic schema
  - Include content-level guardrails:
  - Output length checks
  - Prohibited content filtering
  - Domain relevance validation

### Integration Tests

Test component interaction:

- Workflow execution (mock LLM)
- Database queries
- pgvector retrieval

### End-to-End Tests

Simulate real user flow: POST request → Agno workflow → final output via SSE stream

Validate:

- structured SSE events at each workflow step
- final response structure

### AI Behaviour Tests

The UI includes three predefined test cases based on user feelings: “Relaxed”, “Happy”, and “Sad”. Each case demonstrates how the system maps input feelings to dining styles using CAG, along with an indicative confidence level and the expected behavior of the generated recommendations.

- Relaxed → Stronger mapping (Brunch, Casual Dining with 56% confidence score), so recommendations are guided by CAG results.
- Happy → Moderate/uncertain mapping (Casual Dining with 40% confidence score), so recommendations are more general.
- Sad → Weak mapping (Comfort Food with only 31% confidence), so general recommendations are returned.

The UI displays both the expected behavior and the actual output, allowing users to easily compare and validate the system’s responses.

## API Documentation

This project exposes a small set of HTTP endpoints. The primary API used by the frontend is a POST endpoint that streams Server-Sent Events (SSE) so the client can display progress as the multi-step workflow runs.

### POST /recommend (SSE)

- Path: `/recommend`
- Method: POST
- Content-Type: multipart/form-data or application/x-www-form-urlencoded (the server uses FastAPI Form fields)
- Response: 200 OK with `Content-Type: text/event-stream` (SSE)

Request form fields

- `feeling` (string, required) — free-text description of how the user feels (the canonical input used by CAG).
- `cuisine` (string, optional) — one of the enumerated cuisine values returned by `/options`.
- `dietary_requirement` (string, optional) — one of the enumerated dietary requirement values returned by `/options`.

Behavior

- The endpoint runs the project workflow synchronously on the server (intake → CAG match → conditional RAG → generation → validate) and streams structured SSE events for each workflow step.
- Each SSE event contains an `event` name and a JSON `data` payload. Clients should parse and handle events as they arrive instead of waiting for the request to finish.

Event format (SSE)

- Each event is emitted as standard SSE with an `event:` header and a `data:` JSON payload. Example:

  event: step:cag_match
  data: {"status": "started", "input": {"feeling": "Relaxed", "cuisine": "any"}}

  event: step:cag_match
  data: {"status": "completed", "output": {"dining_styles": ["Cafe"], "confidence": 0.58, "fallback": false}}

- Common fields in the event `data` JSON:
  - `status`: one of `started`, `completed`, or `error`.
  - `input`: snapshot of inputs provided to the step (when `status == "started"`).
  - `output`: step output (when `status == "completed"`). The shape depends on the step.
  - `error`: human-readable message (when `status == "error"`).

Important step event names and typical payloads

- `step:cag_match`
  - started: {"status":"started","input":{...}}
  - completed: {"status":"completed","output": {"dining_styles": [string], "confidence": float, "fallback": bool, "candidates": [...]}}

- `step:rag_retrieve` (present only when the workflow decides to run RAG)
  - completed: {"status":"completed","output": <rag results (array or object)>}

- `step:generate:with_cag` or `step:generate:random`
  - started/completed events. `completed` `output` is the generator result. The generator often returns a JSON string (sometimes wrapped in Markdown code fences). Clients should safely strip fences and parse the JSON if possible.

- `step:finished`
  - final event with session id and normalized output: {"status":"completed","session_id": "<uuid>", "output": <final output>}

### GET /traces/{session_id}

- Path: `/traces/{session_id}`
- Method: GET
- Response: 200 OK, JSON array of trace records for the session. Each record contains at least: `step_name`, `input`, `output`, `status`, `prompt_version`, and `created_at`.

### GET /options

- Path: `/options`
- Method: GET
- Response: 200 OK, JSON object with enumerated option lists used by the UI:
  - `cuisines`: array of cuisine keys
  - `dietary_requirements`: array of dietary requirement keys

### GET /test (UI)

- Path: `/test`
- Method: GET
- Response: 200 OK, HTML page used for manual testing and demonstration. This page posts to `/recommend` and renders results as SSE events and rendered cards.

Errors

- Transient or non-fatal issues are reported as step-level SSE events with `status: "error"`. Clients should surface these messages in the UI and may continue to listen for further events.
- If the server fails before streaming any SSE (for example, due to a fatal startup error), it will return a normal HTTP error response (4xx/5xx).

## Open questions and Assumptions

### Questions asked

The below questions are sent via emails or during the initial catchup.

#### During the initial catchup

- What does 'golden' test cases mean?
- Should I document API related information in DESIGN.md?

#### Before the design stage

- For the RAG knowledge base, do the documents need to be sourced from real data (e.g., actual documents or links), or is curated/synthetic content acceptable as long as it is realistic and meaningful?
- The requirement states: “Are RAG documents chunked appropriately?” Regarding document chunking, is an automated approach using LLM (e.g., simply providing a URL and using an embedder like OpenAIEmbedder) sufficient? Should I include manual chunking or some sort of preprocessing before embedding? And should those be handled as part of the data ingestion process, or are they expected to be included within the workflow itself, given the requirement to “integrate retrieval into the workflow”?
- Would using the OpenAI API or similar paid APIs be acceptable during evaluation? I’m mindful that API keys should not be included in a public repository. Given that these services are paid, I’d like to double-check that this approach is acceptable and won’t affect the team’s ability to test the application.
- For the CAG requirement of 50-200 rows, should this be implemented as a single reference table, or can it be distributed across multiple related tables?
- Could you please explain the requirement "Migrations are reversible"? What level of implementation is expected for this?

#### Design finalization stage

- For the prompt template version, are you referring to updating a single prompt template, or using different templates for different conditions?
- The requirement suggests a preference for “using existing libraries rather than full custom AI code.” Could you clarify what is considered “full custom AI code” in this context? For example, for the CAG step, we could use a local embedding library like SentenceTransformers instead of calling an LLM for embeddings and using an agent for matching, which would be more cost-efficient (though potentially less capable compared to LLM-based approaches). Would this approach still be considered acceptable, given that it still involves writing some custom logic? I know that there isn’t a right or wrong approach here, but I want to understand your preference.
- Following up on question 3 in my previous email, do you have any preference regarding the LLM API choice? Would Claude be acceptable? I recall it being mentioned in our previous discussions.
- For the CHANGELOG, would you prefer it to include major project changes (e.g. initial setup, Docker setup), or only changes per release version?

### Assumptions

- Template versions are unique within each template type. The system always fetches the latest version for each template type.
- The OpenAI API is used, assuming this is acceptable.
- CAG reference data can be stored in a single reference table with 50+ rows.
- Documents need to be sourced from real data. In this project, I stored links to 10 websites that recommend Melbourne restaurants and retrieved data from them.
- For document chunking, an automated approach using an LLM (e.g., providing a URL and using an embedder like OpenAIEmbedder) is sufficient.
- I assume lightweight custom logic (e.g., using SentenceTransformers) is acceptable. This prioritizes efficiency and scalability over fully LLM-based approaches.
- The CHANGELOG should include major project changes (e.g., when key features like CAG or RAG are introduced).