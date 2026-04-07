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
      # instructions="Return restaurant recommendations based on the user's preferences and dietary requirements."
    )