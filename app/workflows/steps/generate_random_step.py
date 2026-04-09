from app.agents.generate import generate_agent
from app.db.repositories.prompt_repository import get_prompt_template
from app.db.session import SessionLocal
from app.models.enums import TemplateType


def generate_random_step(state):
    session = SessionLocal()

    try:
        template = get_prompt_template(
            session,
            template_type=TemplateType.RANDOM_RECOMMENDATION,
        )

        template_text = template.template if hasattr(template, 'template') else str(template)

        agent = generate_agent()

        print(f"Running agent with template: {template_text}")
        
        result = agent.run(template_text)

        print(f"State before generation: {result}")

        state["output"] = result
        return state

    finally:
        session.close()