# Design Specification

## Table of Contents

- [Design Specification](#design-specification)
  - [Table of Contents](#table-of-contents)
  - [Domain choice and rationale](#domain-choice-and-rationale)
  - [System architecture diagram](#system-architecture-diagram)
  - [Decisions Made to Limit AI First Coding Issues](#decisions-made-to-limit-ai-first-coding-issues)
  - [Database Schema Design](#database-schema-design)
    - [Tables](#tables)
    - [Enums](#enums)
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
  - [Open questions and Assumptions](#open-questions-and-assumptions)
    - [Questions asked](#questions-asked)

## Domain choice and rationale

I chose to develop a dining advisor that recommends restaurant options based on how the user wants to feel in a restaurant.

This domain works well with CAG because user preferences can be expressed as free text (e.g., "cheap", "romantic") and semantically matched to predefined dining styles. Based on the detected dining style and the user’s preferences, the system can apply different generation strategies, such as selecting different prompt templates.

RAG can be used to recommend restaurant based on the detected dining style, or retrieve relevant restaurant knowledge (e.g., restaurant descriptions and review) to enrich the generated recommendations if needed.

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
        │     - Pydantic validation
        │
        ├── CAG Service
        │     - Loads dining_styles (PostgreSQL)
        │     - Embedding similarity search
        │
        ├── RAG Service
        │     - Query pgvector knowledge base
        │     - Hybrid search
        │
        ├── Prompt Service
        │     - Fetch prompt_templates (PostgreSQL)
        │     - Resolve variables
        │
        ├── LLM Service
        │     - External or local model
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
   - Used CAG to classify user's preference on dining styles instead of relying on LLM classification
   - Reduces:
     1. hallucination risk
     2. (possibly) token cost
     3. security risk (aviod hacker/bad user to send command to LLM directly)
  
2. Minimise LLM Responsibility
   - LLM is only used for:
      - final generation
   - Not used for:
      - classification
      - data transformation
      - preprocessing
   - Advantages: Keeps system predictable and testable

3. Use Structured Data Over Free Text Where Possible
   - Introduced:
      - enums (cuisine, dietary requirements)
      - preprocessed (chunked) RAG documents
   - Improves:
      - retrieval quality
      - prompt clarity

4. Use Library Capabilities Instead of Custom Implementations
   - Used:
      - Agno for workflow orchestration
      - pgvector for similarity search
      - Pydantic for validation
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
3. knowledge_documents (RAG)
   - Stores restaurant-related documents
   - Embedded and stored in pgvector
   - Used for retrieval

### Enums

1. cuisines
   - Used for user preferences (include/exclude)
2. dietary_requirements
   - e.g., gluten-free, vegan

### Output Schema (Pydantic)

Defines the expected structure of the generated response to ensure consistency and correctness.

#### Expected Output Structure

The system expects the LLM to return a JSON object with the following structure:

```JSON
{
  "recommendations": [
    {
      "name": "Restaurant name",
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

| Step                                                  | Input                                                                | Input Type                          | Output                                        | Output Type                                                    |
| ----------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------- | --------------------------------------------- | -------------------------------------------------------------- |
| Intake                                                | Form submission                                                      | string, boolean, enums (as strings) | Validation result                             | boolean, error message                                         |
| CAG Matching (if user chooses to include preferences) | User preference (free text)                                          | string                              | Relevant dining styles with confidence scores | List of tuples (dining style: string, confidence score: float) |
| RAG Retrieval (if needed)                             | Dining style or user preference                                      | string                              | Retrieved contextual documents                | List of documents (string)                                     |
| Generation                                            | User preferences and/or selected dining style + optional RAG context | string, boolean                     | Generated recommendations                     | string (JSON format)                                           |
| Validation                                            | Generated recommendations                                            | string                              | Validation result                             | boolean, error message                                         |

Additional Notes:

- All inputs and outputs at each step are logged in a structured manner for observability and debugging.
- Conditional branching occurs:
  - after CAG Matching (based on confidence score)
  - before RAG Retrieval (whether additional context is needed)

## Prompt Template Strategy

> How I structure templates, what variables they'll use, and how they're selected

Templates will be stored in the database, together with version, and their condition.

### Variables

The variables will be represented by placeholders like {{cuisine}}, {{dietary_requirement}}.

**Variables:**

- cuisine
- dietary_requirement
- dining_style
- possible_feeling (free text from user)

### Branches of Template

1. After CAG Matching

1.1 RAG Context Available

- If retrieved documents contain relevant restaurant recommendations:
  - Use a prompt template that incorporates RAG context
  - Ask the LLM to generate 3 recommendations based on:
    - Retrieved restaurants
    - User preferences (if the number of retrieved restaurants are less than 3)

1.2 No Relevant RAG Context
a. Multiple Strong Dining Style Matches

- If there are several strong CAG matches:
  - Use a prompt template that considers multiple dining styles
  - Ask the LLM to balance these styles in the recommendations

b. Single Strong Dining Style Match

- If there is only one strong CAG match:
  - Use a focused prompt template
  - Ask the LLM to generate recommendations based on the top dining style

2. Random Recommendation (User Selected)

- If the user selects a random recommendation:
  - Skip both CAG and RAG
  - Use a simple prompt template
  - Ask the LLM to generate random restaurant recommendations

3. Low Confidence in CAG Matching

- If the top CAG confidence score is below a defined threshold:
  - Do not rely on the matched dining style
  - Use a fallback prompt template
  - Generate recommendations based on structured user inputs (e.g., cuisine, dietary requirements)
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
- Free-text user input (e.g., describing feelings or preferences) is semantically matched to predefined dining styles using preloaded reference data.
- This approach:
  - Enables flexible free-text input
  - Improves output quality through structured classification
  - Reduces token usage by avoiding unnecessary LLM interpretation
  - Avoid directly passing raw free-text input to the LLM for security reason

### RAG

- RAG is executed after CAG to determine whether relevant supporting documents exist.
- The predicted dining styles from CAG are used as part of the retrieval query.
- It is mainly used to provide factual context and reduce hallucination from the LLM.
- If no relevant documents are found, the system continues without RAG context (graceful fallback).

## Error Handling Approach

| Step          | Errors                                                 | Approach                                                                                  |
| ------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Intake        | Input validation errors                                | Display validation errors in the UI                                                       |
| CAG Matching  | Database connection error                              | Display database connection error in the UI                                               |
| CAG Matching  | Low confidence score (not an error but handled)        | Use fallback prompt template based on structured input instead of CAG result              |
| RAG Retrieval | No relevant documents found (not an error but handled) | Continue without RAG context                                                              |
| Generation    | Prompt not found                                       | Use fallback prompt (e.g., random recommendation template)                                |
| Generation    | LLM connection error / output failure                  | Retry several times; if still failing, return error to UI                                 |
| Validation    | Validation failure                                     | Retry with corrective prompting; log failures and return structured error if retries fail |

Errors will be surfaced to the user and logged in a structured manner to support both debugging and observability. Each workflow step emits structured logs containing the step name, input, output, status (success/failure), and any associated error messages. These logs are persisted with a session ID in the database, allowing them to be queried later via the trace endpoint (e.g., GET /traces/{session_id}).

For the frontend, errors are communicated through Server-Sent Events (SSE) with clearly defined event types (e.g., step:error, step:success), enabling the UI to display real-time feedback for each stage of the workflow. Where possible, the system follows a graceful degradation strategy—non-critical failures (such as low CAG confidence or missing RAG results) do not interrupt the workflow, while critical failures (such as repeated LLM or validation failures) return a structured error response.

## Testing Strategy

> What I test, how, and at what level (unit, integration, end-to-end)

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

Include 3 test cases with known inputs that can be easily selected in ui. Display expected output characteristics and the output in ui for the user to check.

## Open questions and Assumptions

### Questions asked

- For the RAG knowledge base, do the documents need to be sourced from real data (e.g., actual documents or links), or is curated/synthetic content acceptable as long as it is realistic and meaningful?
- The requirement states: “Are RAG documents chunked appropriately?” Regarding document chunking, is an automated approach using LLM (e.g., simply providing a URL and using an embedder like OpenAIEmbedder) sufficient? Should I include manual chunking or some sort of preprocessing before embedding? And should those be handled as part of the data ingestion process, or are they expected to be included within the workflow itself, given the requirement to “integrate retrieval into the workflow”?
- Would using the OpenAI API or similar paid APIs be acceptable during evaluation? I’m mindful that API keys should not be included in a public repository. Given that these services are paid, I’d like to double-check that this approach is acceptable and won’t affect the team’s ability to test the application.
- For the CAG requirement of 50-200 rows, should this be implemented as a single reference table, or can it be distributed across multiple related tables?
- Could you please explain the requirement "Migrations are reversible"? What level of implementation is expected for this?