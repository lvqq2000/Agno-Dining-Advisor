from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
# from agno.embedder.openai import OpenAIEmbedder

_knowledge_instance = None

def get_knowledge_base():
    global _knowledge_instance

    if _knowledge_instance is None:
        vector_db = PgVector(
            # table_name="restaurants",
            # db_url="postgresql://user:pass@localhost:5432/db",
            # search_type="hybrid",
            # embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        )
        _knowledge_instance = Knowledge(vector_db=vector_db)
        #  _knowledge_instance.load_content()

    return _knowledge_instance