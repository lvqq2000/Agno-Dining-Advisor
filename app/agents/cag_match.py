from agno.agent import Agent
from app.core.config import DEFAULT_MODEL
from app.core.constants import SIMILARITY_THRESHOLD


def create_cag_match_agent():
  # Keep instructions short and reference the canonical threshold from constants.
  instructions = (
    "You are a semantic matching assistant.\n"
    "Given a user input and a JSON list of candidate reference texts (with similarity scores),\n"
    "choose the best matching candidate and return ONLY a JSON object with keys:\n"
    "  - dining_styles (list of strings)\n"
    "  - confidence (float 0..1)\n"
    f"  - fallback (true if confidence < {SIMILARITY_THRESHOLD})\n"
  )

  return Agent(
    name="CAG Match",
    model=DEFAULT_MODEL,
    instructions=instructions,
  )