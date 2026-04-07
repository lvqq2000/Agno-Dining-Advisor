from agno.workflow import Workflow, Step
from app.agents.cag_match import create_cag_match_agent
from app.agents.intake import create_intake_agent
from app.agents.rag_match import create_rag_match_agent
from app.agents.generate import create_generate_agent
from app.steps.mock_step import mock_step

def create_workflow():
    return Workflow(
        name="Dining Advisor",
        # db=PostgresDb(db_url=db_url),
        steps=[
            mock_step,
            # Step(name="intake", agent=intake_agent),
            # Step(name="cag_match", agent=cag_match_agent), # Might change it to function later
            # Step(name="rag_match", agent=rag_match),
            # Step(name="generate", agent=generate_agent),
            # validate_output,
        ],
    )