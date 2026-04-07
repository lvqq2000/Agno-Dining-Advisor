from app.models.response import ResponseModel
import json


def validate_output_step(state):
    """Parse and validate the LLM output stored in state['output'] against Pydantic schema.

    On success sets state['validated_output'] to the parsed model dict.
    On failure sets state['validation_error'] with details.
    """
    raw = state.get("output")
    if raw is None:
        state["validation_error"] = "no output to validate"
        return state

    # If output is an object, accept it; if it's a string, attempt to parse JSON
    parsed = None
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except Exception as e:
            # sometimes LLM returns single-quoted or invalid JSON; capture error
            state["validation_error"] = f"invalid json: {e}"
            return state
    else:
        parsed = raw

    try:
        model = ResponseModel.parse_obj(parsed)
        state["validated_output"] = model.dict()
        return state
    except Exception as e:
        state["validation_error"] = str(e)
        return state
