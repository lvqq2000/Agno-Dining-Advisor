from agno.agent import Agent
from app.config import DEFAULT_MODEL

def create_cag_match_agent():
    return Agent(
        name="CAG Match",
        model=DEFAULT_MODEL,
        # instructions="Use embeddings to find the best semantic match between the user's free-text input and the reference data"
    )