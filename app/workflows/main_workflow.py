from agno.workflow import Workflow, Step, Condition
from app.workflows.steps import generate_with_cag_step, generate_with_rag_step, generate_with_selection_step
from app.workflows.steps.cag_match_step import cag_match_step
from app.workflows.steps.intake_step import intake_step
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

            # Choose generation strategy based on CAG fallback flag
            # Use the agno.Condition API (evaluator, steps, else_steps)
            Condition(
                name="generation_strategy_fallback",
                evaluator=lambda state: state.get("cag_result", {}).get("fallback", False),
                steps=[generate_with_selection_step],
                else_steps=[generate_with_rag_step],
            ),

            Condition(
                name="generation_strategy_if_rag_fail",
                # Use the RAG retrieval results placed on state['rag_results'] by
                # `rag_retrieve_step`. If RAG returned no documents (empty list
                # or falsy), fall back to the CAG-driven generator (without using stored knowledge).
                evaluator=lambda state: not state.get("rag_results"),
                steps=[generate_with_cag_step],
                else_steps=[generate_with_rag_step],
            ),

            # Validate LLM output against Pydantic schema
            validate_output_step,
        ],
    )