from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from app.db.base import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    template = Column(Text, nullable=False)

    # Using plain string for template_type to avoid DB enum serialization issues in seeders
    template_type = Column(String(length=64), nullable=False)

    # The version of the prompt template - unique for each type
    version = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("template_type", "version", name="uq_template_version"),)