from agno.workflow import Workflow, Step, Condition
from app.workflows.steps import generate_with_cag_step
from app.workflows.steps.cag_match_step import cag_match_step
from app.workflows.steps.generate_random_step import generate_random_step

def create_workflow():
    return Workflow(
        name="Dining Advisor",
        steps=[
            cag_match_step,

            Condition(
                condition=lambda state: state["cag_result"]["fallback"],
                if_true=generate_random_step,
                if_false=generate_with_cag_step,
            ),
        ],
    )