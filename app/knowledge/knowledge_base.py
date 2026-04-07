from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
# from agno.embedder.openai import OpenAIEmbedder

def get_knowledge_base():
    vector_db = PgVector(
        # table_name="restaurants",
        # db_url="postgresql://user:pass@localhost:5432/db",
        # search_type="hybrid",
        # embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    )

    knowledge = Knowledge(vector_db=vector_db)

    # knowledge.load_content()

    return knowledge