from sqlalchemy import Column, Integer, String, Text
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class CAGReferenceData(Base):
    __tablename__ = "cag_reference_data"

    id = Column(Integer, primary_key=True)

    # The possible dining styles users might like
    dining_style = Column(String, nullable=False)

    # The reference text users might input
    reference_text = Column(Text, nullable=False)

    # Embedding vector for semantic matching
    embedding = Column(Vector(1536), nullable=False)