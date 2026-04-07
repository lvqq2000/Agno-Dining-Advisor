from app.services.cag_matching_service import find_top_k_matches
from app.agents.cag_match import create_cag_match_agent
from app.db.session import SessionLocal
from app.core.constants import SIMILARITY_THRESHOLD
import json
import re


def cag_match_step(state):
    # Frontend provides a single free-text field named 'feeling'. Use it.
    user_input = state["feeling"]

    session = SessionLocal()

    try:
        # 1. Get candidates from DB
        candidates = find_top_k_matches(session, user_input, k=5)

        # 2. Provide structured JSON candidates to the agent so it can reason reliably.
        candidates_json = json.dumps(candidates, ensure_ascii=False)

        prompt_text = (
            f"User input: {user_input}\n\n"
            f"Candidates (JSON):\n{candidates_json}\n\n"
            f"Choose the single best matching candidate and RETURN ONLY a JSON object with keys:"
            f" dining_styles (list), confidence (float 0..1), fallback (true/false)."
            f" If confidence < {SIMILARITY_THRESHOLD} set fallback = true."
        )

        # 3. Let LLM pick best match using the agent (its system instructions are concise).
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

        # 5. If parsing succeeded, normalize fallback according to canonical threshold.
        if parsed:
            try:
                parsed_conf = float(parsed.get("confidence", 0.0))
            except Exception:
                parsed_conf = 0.0
            # if model didn't provide a fallback flag, compute it consistently
            if "fallback" not in parsed:
                parsed["fallback"] = parsed_conf < SIMILARITY_THRESHOLD
        else:
            # If parsing failed, pick the top candidate heuristically using the same threshold
            if candidates:
                top = max(candidates, key=lambda x: x.get('similarity', 0))
                parsed = {
                    "dining_styles": top.get('dining_styles', []),
                    "confidence": float(top.get('similarity', 0)),
                    "fallback": float(top.get('similarity', 0)) < SIMILARITY_THRESHOLD,
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