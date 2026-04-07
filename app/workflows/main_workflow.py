from agno.workflow import Workflow, Step, Condition
from app.workflows.steps import generate_with_cag_step
from app.workflows.steps.cag_match_step import cag_match_step
from app.workflows.steps.generate_random_step import generate_random_step
from app.workflows.steps.intake_step import intake_step
from app.workflows.steps.rag_retrieve_step import rag_retrieve_step
from app.workflows.steps.validate_output_step import validate_output_step


def create_workflow():
    """Create a multi-step workflow with an intake, CAG, optional RAG, generation and validation.

    Conditional branch:
    - If CAG confidence is low (or fallback) -> run RAG retrieval to augment context
    - If CAG signals fallback -> use random generator, else use CAG-driven generator
    """
    return Workflow(
        name="Dining Advisor",
        steps=[
            # Intake & validation of the incoming form data
            intake_step,

            # CAG matching to map free text to dining styles
            cag_match_step,

            # Optional RAG retrieval when CAG confidence is low
            #Condition(
            #    condition=lambda state: (
            #        # run RAG if no cag_result or confidence is below threshold
            #        (not state.get("cag_result"))
            #        or (state.get("cag_result", {}).get("confidence", 1.0) < 0.8)
            #    ),
            #    if_true=rag_retrieve_step,
            #    if_false=None,
            #),

            # Choose generation strategy based on CAG fallback flag
            # Use the agno.Condition API (evaluator, steps, else_steps)
            Condition(
                name="generation_strategy",
                evaluator=lambda state: state.get("cag_result", {}).get("fallback", False),
                steps=[generate_random_step],
                else_steps=[generate_with_cag_step],
            ),

            # Validate LLM output against Pydantic schema
            validate_output_step,
        ],
    )