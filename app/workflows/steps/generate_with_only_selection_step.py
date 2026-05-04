from app.agents.generate import generate_agent
from agno.agent import RunEvent
from app.db.repositories.prompt_repository import get_prompt_template
from app.db.session import SessionLocal
from app.models.enums import TemplateType
from app.services.template_renderer import render_template


def generate_with_only_selection_step(state):
    session = SessionLocal()

    try:

        template = get_prompt_template(
            session,
            template_type=TemplateType.RECOMMENDATION_WITH_SELECTION
        )

        # template may be a DB model; extract the textual template
        template_text = template.template if hasattr(template, 'template') else str(template)

        variables = {
            "cuisine": state.get("cuisine", "any"),
            "dietary_requirement": state.get("dietary_requirement", "none"),
        }

        prompt = render_template(template_text, variables)

        agent = generate_agent()

        result = agent.run(prompt)

        state["output"] = result
        return state

    finally:
        session.close()