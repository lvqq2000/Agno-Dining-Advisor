from agno.agent import Agent
from app.config import DEFAULT_MODEL

def create_intake_agent():
    return Agent(
        name="Intake",
        model=DEFAULT_MODEL,
        # instructions="Validate user input"
    )