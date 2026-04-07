from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder
import os

from app.core.constants import KNOWLEDGE_BASE_URLS

_knowledge_instance = None

def get_knowledge_base():
    global _knowledge_instance

    if _knowledge_instance is None:
        # Read database URL from environment to match the app configuration
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")

        vector_db = PgVector(
            table_name="restaurants",
            db_url=db_url,
            search_type="hybrid",
            embedder=OpenAIEmbedder(),
        )
        _knowledge_instance = Knowledge(vector_db=vector_db)

        for url in KNOWLEDGE_BASE_URLS:
            _knowledge_instance.insert(url=url, skip_if_exists=True)
        #  _knowledge_instance.load_content()

    return _knowledge_instance