from app.db.session import SessionLocal
from app.db.models.prompt_template import PromptTemplate
from app.models.enums import TemplateType


def get_prompt_template(db_session, template_type: TemplateType, version: int = None):
    """Retrieve a prompt template by type and optional version.

    db_session: a SQLAlchemy session (caller-managed)
    template_type: TemplateType enum
    version: optional integer version
    """
    query = db_session.query(PromptTemplate).filter_by(template_type=template_type)
    if version is not None:
        query = query.filter_by(version=version)

    template = query.order_by(PromptTemplate.version.desc()).first()
    return template