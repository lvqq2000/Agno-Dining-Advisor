from app.services.embedding_service import get_embedding
from app.db.models import CAGReferenceData
import math
import logging


def _cosine_similarity(a, b):
    # a and b are lists of floats
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_top_k_matches(session, user_input: str, k: int = 5):
    """
    Fallback implementation that computes cosine similarity in Python.
    This avoids relying on the pgvector binding for raw SQL parameters.
    It's acceptable for small reference datasets used in the seed.
    """
    query = session.query(CAGReferenceData)
    rows = query.all()
    logging.getLogger(__name__).debug(f"find_top_k_matches: loaded {len(rows)} reference rows")

    emb = get_embedding(user_input)

    scored = []
    for r in rows:
        # r.embedding may be a list-like or pgvector type
        ref_vec = list(r.embedding)
        sim = _cosine_similarity(emb, ref_vec)
        scored.append((sim, r))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:k]
    if top:
        logging.getLogger(__name__).debug(f"find_top_k_matches: top similarity={top[0][0]}")

    return [
        {
            "reference_text": r.reference_text,
            "dining_styles": r.dining_styles,
            "similarity": float(sim),
        }
        for sim, r in top
    ]