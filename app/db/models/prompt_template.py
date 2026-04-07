from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    template = Column(Text, nullable=False)

    # The version of the prompt template - used for template selection
    version = Column(Integer, unique=True, nullable=False)