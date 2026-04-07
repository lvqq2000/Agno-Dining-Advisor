from app.agents.generate import generate_agent
from app.db.repositories.prompt_repository import get_prompt_template
from app.db.session import SessionLocal
from app.models.enums import TemplateType
from app.services.template_renderer import render_template


def generate_recommendation_step(state):
    session = SessionLocal()

    try:
        template = get_prompt_template(
            session,
            template_type=TemplateType.RECOMMENDATION_WITH_CAG
        )

        variables = {
            "cuisine": state.get("cuisine", "any"),
            "dietary_requirement": state.get("dietary_requirement", "none"),
            "dining_style": ", ".join(state["cag_result"]["dining_styles"]),
        }

        prompt = render_template(template, variables)

        agent = generate_agent()

        result = agent.run(prompt)

        state["output"] = result
        return state

    finally:
        session.close()