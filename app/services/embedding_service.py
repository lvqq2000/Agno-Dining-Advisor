"""Embedding service.

Use the same sentence-transformers model used by the seeder so runtime
embeddings match the stored reference embeddings (all-mpnet-base-v2).
This avoids mismatches when computing cosine similarity between the
seeded vectors and live inputs.
"""
from sentence_transformers import SentenceTransformer

# Load lazily on first use to avoid expensive startup when not needed.
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-mpnet-base-v2")
    return _model


def get_embedding(text: str) -> list[float]:
    model = _get_model()
    emb = model.encode(text)
    # Return a plain Python list of floats to keep serialization predictable.
    return emb.tolist()