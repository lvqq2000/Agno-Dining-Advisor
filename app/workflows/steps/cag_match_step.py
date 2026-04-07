from app.services.cag_matching_service import find_top_k_matches
from app.agents.cag_match import create_cag_match_agent
from app.db.session import SessionLocal
import json
import re


def cag_match_step(state):
    # Frontend provides a single free-text field named 'feeling'. Use it.
    user_input = state["feeling"]

    session = SessionLocal()

    try:
        # 1. Get candidates from DB
        candidates = find_top_k_matches(session, user_input, k=5)

        # 2. Build a textual prompt for the agent that includes the user input
        #    and the candidate list so the LLM can reason over them directly.
        candidates_text = []
        for i, c in enumerate(candidates, start=1):
            candidates_text.append(f"{i}. text: {c['reference_text']} | styles: {c['dining_styles']} | similarity: {c['similarity']}")

        prompt_text = (
            f"User input: {user_input}\n\nCandidates:\n" + "\n".join(candidates_text)
            + "\n\nChoose the single best matching candidate from the list above using the similarity scores as guidance."
            + " Return a JSON object with keys: dining_styles (the candidate's dining_styles list), confidence (a float similarity between 0 and 1), and fallback (true if no candidate is suitable)."
            + " If you are uncertain, still return the most likely dining_styles based on the candidates."
            + " Example output: {\"dining_styles\": [\"Cafe\"], \"confidence\": 0.65, \"fallback\": false }"
        )

        # 3. Let LLM pick best match using a plain text prompt (agent has system instructions)
        agent = create_cag_match_agent()
        result = agent.run(prompt_text)

        # result may be a RunOutput; try to extract the textual content
        text_out = None
        try:
            # Try common attributes
            if hasattr(result, 'content') and result.content:
                text_out = result.content
            elif hasattr(result, 'text') and result.text:
                text_out = result.text
            else:
                text_out = str(result)
        except Exception:
            text_out = str(result)

        # 4. Attempt to parse JSON from the model's reply
        parsed = None
        try:
            parsed = json.loads(text_out)
        except Exception:
            # try to extract a JSON substring
            m = re.search(r"\{[\s\S]*\}", text_out)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None

        # 5. Fallback: if parsing failed, pick the top candidate heuristically
        if not parsed:
            if candidates:
                top = max(candidates, key=lambda x: x.get('similarity', 0))
                # Use a lower threshold for fallback determination so we still
                # surface reasonable dining styles when similarity is low.
                threshold = 0.50
                parsed = {
                    "dining_styles": top.get('dining_styles', []),
                    "confidence": float(top.get('similarity', 0)),
                    "fallback": False if top.get('similarity', 0) >= threshold else True,
                }
            else:
                parsed = {"dining_styles": [], "confidence": 0.0, "fallback": True}

        # Attach a small preview of the top candidates to help debugging/UI
        try:
            parsed_candidates = [
                {"text": c.get('reference_text'), "similarity": float(c.get('similarity', 0))}
                for c in candidates[:5]
            ]
            parsed["candidates"] = parsed_candidates
        except Exception:
            parsed["candidates"] = []

        # 6. Save into workflow state as a plain dict
        state["cag_result"] = parsed

        return state

    finally:
        session.close()