from agno.agent import Agent
from app.core.config import DEFAULT_MODEL
from app.knowledge.knowledge_base import get_knowledge_base

def create_rag_match_agent():
    knowledge = get_knowledge_base()
    
    return Agent(
      name="RAG Match",
      knowledge=knowledge,
      search_knowledge=True,
      model=DEFAULT_MODEL,
        instructions="""
You are a dining recommendation assistant.

- You will receive a fully prepared prompt with all variables already filled.
- Search the knowledge base for restaurant documents that match the dining styles first, then cuisine, then dietary requirements.
- If no matching restaurants are found, return an empty JSON array (`[]`).
- Follow the instructions inside the prompt exactly.
- Always return valid JSON.

IMPORTANT:
- Do NOT ignore the prompt content
- Do NOT add extra explanation outside JSON
"""
    )