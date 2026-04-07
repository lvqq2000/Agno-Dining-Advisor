from dotenv import load_dotenv
load_dotenv()  # Load environment variables

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
from datetime import datetime

from app.workflows.steps.cag_match_step import cag_match_step
from app.workflows.steps.generate_with_cag_step import generate_recommendation_step
from app.workflows.steps.generate_random_step import generate_random_step
from app.workflows.main_workflow import create_workflow
from app.db.session import SessionLocal
from app.db.repositories.trace_repository import create_trace, get_traces_by_session
from app.db.repositories.prompt_repository import get_prompt_template
from app.models.enums import TemplateType, Cuisine, DietaryRequirement

app = FastAPI(title="Agno Dining Advisor API")

# Mount a simple static folder for testing UI
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _run_steps_sync(state, session_id):
    """Run a simplified workflow synchronously and yield structured events.

    Yields tuples of (event_name, data_dict)
    """
    db = SessionLocal()
    try:
        # 1) CAG match step
        step_name = "cag_match"
        try:
            input_snapshot = {k: state.get(k) for k in ["feeling", "cuisine", "dietary_requirement"]}
            # emit before
            yield (f"step:{step_name}", {"status": "started", "input": input_snapshot})

            result_state = cag_match_step(state)

            # emit after
            yield (f"step:{step_name}", {"status": "completed", "output": result_state.get("cag_result")})

            # persist trace (serialize RunOutput/complex objects safely)
            create_trace(db, session_id, step_name, _safe_serialize(input_snapshot), _safe_serialize(result_state.get("cag_result")), "success")

        except Exception as e:
            create_trace(db, session_id, step_name, json.dumps(input_snapshot), str(e), "error")
            yield (f"step:{step_name}", {"status": "error", "error": str(e)})
            return

        # Decide next step based on cag_result
        fallback = state.get("cag_result", {}).get("fallback", False)
        if fallback:
            step_callable = generate_random_step
            step_label = "generate:random"
        else:
            step_callable = generate_recommendation_step
            step_label = "generate:with_cag"

        # 2) Generation
        try:
            yield (f"step:{step_label}", {"status": "started"})

            # generation step may need access to DB inside
            before_input = {"state_snapshot": {k: state.get(k) for k in ["cag_result", "cuisine", "dietary_requirement"]}}

            # attempt to fetch the prompt template and its version for observability
            prompt_version = None
            try:
                if step_label == 'generate:random':
                    template_obj = get_prompt_template(db, TemplateType.RANDOM_RECOMMENDATION, version=1)
                else:
                    template_obj = get_prompt_template(db, TemplateType.RECOMMENDATION_WITH_CAG)
                if template_obj is not None and hasattr(template_obj, 'version'):
                    prompt_version = getattr(template_obj, 'version')
            except Exception:
                prompt_version = None

            result_state = step_callable(state)

            # Normalize output: if the step returned an Agno RunOutput-like
            # object, prefer its textual content field so downstream UI can
            # display/parse the actual generated JSON.
            raw_out = result_state.get("output")
            if hasattr(raw_out, "content") and raw_out.content:
                output = raw_out.content
            elif hasattr(raw_out, "text") and raw_out.text:
                output = raw_out.text
            else:
                output = raw_out

            # persist normalized output back into state for final step
            state["output"] = output

            yield (f"step:{step_label}", {"status": "completed", "output": output, "prompt_version": prompt_version})

            create_trace(db, session_id, step_label, _safe_serialize(before_input), _safe_serialize(output), "success", prompt_version)

        except Exception as e:
            create_trace(db, session_id, step_label, _safe_serialize(before_input), str(e), "error")
            yield (f"step:{step_label}", {"status": "error", "error": str(e)})
            return

        # 3) Final validation step - optional
        yield ("step:finished", {"status": "completed", "session_id": session_id, "output": state.get("output")})

    finally:
        db.close()


def sse_event_formatter(event_name, data_dict):
    # Build SSE formatted string for an event name and json data
    payload = json.dumps(data_dict, default=str)
    return f"event: {event_name}\ndata: {payload}\n\n"


def _safe_serialize(obj):
    """Return a JSON string for obj, converting non-serializable objects to
    primitives where possible.

    This handles Agno RunOutput/RunInput objects by attempting .to_dict(),
    .dict(), or falling back to __dict__ or str().
    """
    def _default(o):
        if hasattr(o, "to_dict"):
            try:
                return o.to_dict()
            except Exception:
                pass
        if hasattr(o, "dict"):
            try:
                return o.dict()
            except Exception:
                pass
        if hasattr(o, "__dict__"):
            try:
                return o.__dict__
            except Exception:
                pass
        return str(o)

    try:
        return json.dumps(obj, default=_default)
    except TypeError:
        # As a last resort, stringify the object
        return json.dumps(str(obj))


@app.post("/recommend")
async def recommend(request: Request,
                    feeling: str = Form(...),
                    cuisine: str = Form(None),
                    dietary_requirement: str = Form(None)):
    """Accept form data, run the Agno workflow and stream results via SSE.

    The client should listen for SSE events of the form `step:<name>` to display progress.
    """
    # Create a session id for tracing
    session_id = str(uuid.uuid4())

    # Build initial workflow state using the canonical 'feeling' field
    state = {
        "feeling": feeling,
        "preferences": None,
        "cuisine": cuisine,
        "dietary_requirement": dietary_requirement,
    }

    def event_stream():
        # For now use our synchronous step runner which works with the
        # normalized `state` dict. This avoids compatibility problems with
        # the Agno workflow runtime's StepInput objects in streaming mode.
        for event_name, data in _run_steps_sync(state, session_id):
            yield sse_event_formatter(event_name, data).encode("utf-8")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/traces/{session_id}")
def get_traces_endpoint(session_id: str):
    db = SessionLocal()
    try:
        traces = get_traces_by_session(db, session_id)
        return JSONResponse([t for t in traces])
    finally:
        db.close()


@app.get("/options")
def get_options():
    """Return enumerated option lists for UI consumption (cuisines, dietary requirements)."""
    return JSONResponse({
        "cuisines": Cuisine.values(),
        "dietary_requirements": DietaryRequirement.values(),
    })


@app.get("/test", response_class=HTMLResponse)
def test_ui():
    # Serve a simple test UI located in app/static/test.html
    try:
        with open("app/static/test.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Test UI not found</h1>")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)