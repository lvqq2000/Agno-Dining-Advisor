from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import PromptTemplate
from app.models.enums import TemplateType


def get_prompt_template(
    session: Session,
    template_type: TemplateType,
    version: int | None = None
) -> str:
    query = session.query(PromptTemplate).filter_by(template_type=template_type.value)

    # If version specified -> use it
    if version is not None:
        template = query.filter_by(version=version).first()
    else:
        # Otherwise -> get latest version
        template = query.order_by(desc(PromptTemplate.version)).first()

    if not template:
        raise ValueError(f"Template not found: {template_type.value} (version={version})")

    return template.template