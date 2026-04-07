from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from app.db.base import Base
from sqlalchemy.dialects.postgresql import ENUM

from app.models.enums import TemplateType

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    template = Column(Text, nullable=False)

    # e.g. "random_recommendation"
    template_type = Column(
        ENUM(TemplateType, name="template_type_enum"),
        nullable=False
    )

    # The version of the prompt template - unique for each type
    version = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("template_type", "version", name="uq_template_version"),
)