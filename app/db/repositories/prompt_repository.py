from app.db.session import SessionLocal
from app.db.models.prompt_template import PromptTemplate

def get_prompt_template(version: str):
    db = SessionLocal()
    template = db.query(PromptTemplate).filter_by(version=version).first()
    db.close()
    return template