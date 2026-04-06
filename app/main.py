from agno.agent import Agent
from agno.workflow import Workflow, Step, StepOutput
from agno.knowledge.knowledge import Knowledge
from agno.models.anthropic import Claude

default_model = Claude(id="claude-sonnet-4-6")

# Step 0: Knowledge Base setup and database setup
knowledge = Knowledge(
    #vector_db=PgVector(
    #    table_name="your_domain_docs",
    #    db_url=db_url,
    #    search_type=SearchType.hybrid,
    #    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    #),
)
# knowledge.load_content()

# Step 1: Take user's form submission and validate it
intake_agent = Agent(
    name="Intake",
    model=default_model,
    # instructions="Validate user input and extract relevant information"
)

# Step 2: Try CAG Match
cag_match_agent = Agent(
    name="CAG Match",
    model=default_model,
    # instructions="Use embeddings to find the best semantic match between the user's free-text input and the reference data"
)

# Step 3: Try RAG Match
rag_match = Agent(
    name="RAG Match",
    knowledge=knowledge,
    search_knowledge=True,
    model=default_model,
    # instructions="Check user preferences against knowledge base. Return restaurant recommendations."
)

# Step 4: Generate Response (with condition)
generate_agent = Agent(
    name="generate",
    model=default_model,
    # instructions="Select prompt template based on the result of previous steps. Return restaurant recommendations."
)

# Step 5: Validate Response
def validate_output(step_input):
    pass

# Mock step for testing
def mock_step(step_input):
    return StepOutput(content=f"Mock Input: {step_input.input}")

workflow = Workflow(
    name="Dining Advisor",
    # db=PostgresDb(db_url=db_url),
    
    steps=[
        mock_step,
        # Step(name="intake", agent=intake_agent),
        # Step(name="cag_match", agent=cag_match_agent), # Might change it to function later
        # Step(name="rag_match", agent=rag_match),
        # Step(name="generate", agent=generate_agent),
        # Step(name="validate_output", function=validate_output),
    ],
)

if __name__ == "__main__":
    response = workflow.run(
        input="I want cheap sushi",
        stream=False,
    )

    print("\n--- RESULT ---")
    print(response)