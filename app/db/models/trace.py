from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Trace(Base):
    __tablename__ = "traces"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), index=True, nullable=False)
    step_name = Column(String(128), nullable=False)
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    status = Column(String(32), nullable=False)
    prompt_version = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
