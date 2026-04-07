from app.core.config import SIMILARITY_THRESHOLD
from app.services.embedding_service import get_embedding
from sqlalchemy.orm import Session

def find_top_k_matches(session, user_input: str, k: int = 5):
    embedding = get_embedding(user_input)

    results = session.execute(
        """
        SELECT 
            reference_text,
            dining_styles,
            1 - (embedding <=> :embedding) AS similarity
        FROM cag_reference_data
        ORDER BY embedding <=> :embedding
        LIMIT :k
        """,
        {"embedding": embedding, "k": k}
    ).fetchall()

    return [
        {
            "reference_text": r.reference_text,
            "dining_styles": r.dining_styles,
            "similarity": float(r.similarity),
        }
        for r in results
    ]