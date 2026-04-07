from agno.agent import Agent
from app.core.config import DEFAULT_MODEL

def generate_agent():
    return Agent(
        name="Generate",
        model=DEFAULT_MODEL,
        instructions="""
You are a dining recommendation assistant.

- You will receive a fully prepared prompt with all variables already filled.
- Follow the instructions inside the prompt exactly.
- Always return valid JSON.

IMPORTANT:
- Do NOT ignore the prompt content
- Do NOT add extra explanation outside JSON
"""
    )