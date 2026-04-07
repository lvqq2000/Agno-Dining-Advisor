from agno.agent import Agent
from app.config import DEFAULT_MODEL

def create_generate_agent():
    return Agent(
        name="generate",
        model=DEFAULT_MODEL,
        # instructions="Use embeddings to find the best semantic match between the user's free-text input and the reference data"
    )