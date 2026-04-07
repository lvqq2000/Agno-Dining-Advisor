from agno.agent import Agent
from app.core.config import DEFAULT_MODEL

def create_cag_match_agent():
    return Agent(
        name="CAG Match",
        model=DEFAULT_MODEL,
        instructions="""
You are a semantic matching assistant.

Given:
- a user input
- a list of candidate reference texts with similarity scores

Your job:
- choose the best matching reference
- return:
  - selected dining_styles
  - confidence score (use similarity as base)
  - fallback = true if no strong match (similarity < 0.75)

Respond in JSON:
{
  "dining_styles": [],
  "confidence": 0.0,
  "fallback": false
}
"""
    )