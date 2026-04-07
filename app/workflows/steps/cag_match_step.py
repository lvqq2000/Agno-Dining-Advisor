from app.services.cag_matching_service import find_top_k_matches
from app.agents.cag_match import create_cag_match_agent
from app.db.session import SessionLocal


def cag_match_step(state):
    user_input = state["input"]

    session = SessionLocal()

    try:
        # 1. Get candidates from DB
        candidates = find_top_k_matches(session, user_input, k=5)

        # 2. Let LLM pick best match
        agent = create_cag_match_agent()

        result = agent.run({
            "user_input": user_input,
            "candidates": candidates
        })

        # 3. Save into workflow state
        state["cag_result"] = result

        return state

    finally:
        session.close()