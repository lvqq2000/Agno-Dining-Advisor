from agno.workflow import Workflow, Step, Condition
from app.workflows.steps.generate_random_step import generate_random_step
from app.workflows.steps.cag_match_step import cag_match_step
from app.workflows.steps.generate_with_cag_step import generate_with_cag_step
from app.workflows.steps.generate_with_rag_step import generate_with_rag_step
from app.workflows.steps.generate_with_only_selection_step import generate_with_only_selection_step
from app.workflows.steps.intake_step import intake_step
from app.workflows.steps.validate_output_step import validate_output_step

def create_workflow():
    return Workflow(
        name="Dining Advisor",
        steps=[
            intake_step,
            Condition(
                name="random recommendation",
                evaluator=lambda state: state.get("mode") == "random",
                steps=[
                    generate_random_step,
                    validate_output_step,
                ],
                else_steps=[
                    cag_match_step,
                    Condition(
                        name="conditional_generation_strategy",
                        evaluator=lambda state: state.get("cag_result", {}).get("fallback", True),
                        steps=[generate_with_only_selection_step],
                        else_steps=
                        [
                            Condition(
                                name="rag_generation_strategy",
                                evaluator=lambda state: state.get("do_rag_matching", False),
                                steps=[generate_with_rag_step],
                            ),
                            Condition(
                                name="generation_strategy_if_rag_fail",
                                evaluator=lambda state: not state.get("result", []),
                                steps=[generate_with_cag_step],
                            ),
                        ],
                    ),
                    validate_output_step,
                ],
            )
        ],
    )