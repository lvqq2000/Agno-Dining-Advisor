from dotenv import load_dotenv
load_dotenv()  # Load environment variables

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
from app.workflows.main_workflow import create_workflow
from agno.workflow import Condition
from app.db.session import SessionLocal
from app.db.repositories.trace_repository import create_trace, get_traces_by_session
from app.models.enums import Cuisine, DietaryRequirement

app = FastAPI(title="Agno Dining Advisor API")

# Mount a simple static folder for testing UI
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _run_steps_sync(state, session_id):
    """Run a simplified workflow synchronously and yield structured events.

    Yields tuples of (event_name, data_dict)
    """
    db = SessionLocal()

    # Build the workflow and iterate its steps, emitting SSE events per step.
    workflow = create_workflow()
    steps = getattr(workflow, "steps", []) or []

    def _step_input_snapshot():
        # Small snapshot used for traces to keep payloads readable
        return {k: state.get(k) for k in ["feeling", "cuisine", "dietary_requirement", "cag_result", "output"]}

    def _normalize_step_output(result, step_callable_name):
        # If a step returns a dict, assume it's the new/updated state.
        if isinstance(result, dict):
            return result
        # Fallback: look for well-known state keys
        return state.get("cag_result") or state.get("output") or result

    def _to_json_primitive(obj):
        """Convert arbitrary objects (RunOutput, etc.) into JSON-serializable
        primitives (dict, list, str) so SSE payloads are consistent for the client.
        """
        try:
            # _safe_serialize returns a JSON string; attempt to parse it back into
            # a primitive (dict/list/str) so the outer json.dumps produces a
            # normal JSON structure rather than an escaped string.
            s = _safe_serialize(obj)
            try:
                return json.loads(s)
            except Exception:
                # If parsing fails, return the original JSON string value
                return s
        except Exception:
            try:
                return str(obj)
            except Exception:
                return None

    def _run_callable_step(step_callable):
        step_name = getattr(step_callable, "__name__", str(step_callable))

        # emit started
        input_snapshot = _step_input_snapshot()
        yield (f"step:{step_name}", {"status": "started", "input": input_snapshot})

        try:
            result = step_callable(state)
            # If the callable returned an iterable stream (e.g. agent.run(..., stream=True)),
            # iterate and emit streaming events rather than treating the result as a single value.
            from collections.abc import Iterable
            is_stream = False
            if not isinstance(result, (dict, str, bytes, list)) and isinstance(result, Iterable):
                is_stream = True

            if is_stream:
                collected = []
                for chunk in result:
                    # Attempt to map agno RunEvent-like chunks into SSE events
                    try:
                        ev = getattr(chunk, "event", None)
                        # Prefer enum name if available
                        ev_name = getattr(ev, "name", str(ev)) if ev is not None else "stream"
                        payload = {}
                        if hasattr(chunk, "content"):
                            payload["content"] = getattr(chunk, "content")
                            # collect textual content for a final trace
                            try:
                                collected.append(str(getattr(chunk, "content")))
                            except Exception:
                                pass
                        if hasattr(chunk, "tool"):
                            payload["tool"] = getattr(chunk, "tool")
                        if hasattr(chunk, "reasoning_content"):
                            payload["reasoning"] = getattr(chunk, "reasoning_content")

                        # emit per-chunk SSE event
                        yield (f"step:{step_name}:{ev_name}", {"status": "stream", "data": _safe_serialize(payload)})

                    except Exception as e:
                        # If streaming parsing fails for a chunk, emit an error chunk and continue
                        yield (f"step:{step_name}:stream_error", {"status": "error", "error": str(e)})

                # After stream completes, persist collected content as the step output
                full_output = None
                if collected:
                    try:
                        full_output = "".join(collected)
                    except Exception:
                        full_output = collected

                # emit completed with aggregated output (as JSON-serializable primitive)
                yield (f"step:{step_name}", {"status": "completed", "output": _to_json_primitive(full_output)})
                create_trace(db, session_id, step_name, _safe_serialize(input_snapshot), _safe_serialize(full_output), "success")
                return
            # If the step returned a fresh state mapping, merge it
            if isinstance(result, dict):
                state.update(result)

            output = _normalize_step_output(result, step_name)

            # emit completed (normalize output to a JSON-serializable primitive)
            yield (f"step:{step_name}", {"status": "completed", "output": _to_json_primitive(output)})

            # persist trace
            create_trace(db, session_id, step_name, _safe_serialize(input_snapshot), _safe_serialize(output), "success")
        except Exception as e:
            create_trace(db, session_id, step_name, _safe_serialize(input_snapshot), str(e), "error")
            yield (f"step:{step_name}", {"status": "error", "error": str(e)})
            # re-raise to stop workflow execution
            raise

    def _run_steps_list(steps_list):
        for s in steps_list:
            # Condition node (branching)
            if isinstance(s, Condition):
                try:
                    cond_val = bool(s.evaluator(state))
                except Exception:
                    cond_val = False
                branch = s.steps if cond_val else (s.else_steps or [])
                for ev in _run_steps_list(branch):
                    yield ev
                continue

            # Callable step
            if callable(s):
                for ev in _run_callable_step(s):
                    yield ev
                continue

            # Unknown node: skip
            continue

    try:
        for event in _run_steps_list(steps):
            yield event
        # emit a small debug event showing the type and short preview of the final output
        try:
            final_output_primitive = _to_json_primitive(state.get("output"))
            type_name = type(state.get("output")).__name__ if state.get("output") is not None else "None"
            preview = None
            if isinstance(final_output_primitive, (str, list, dict)):
                try:
                    preview = final_output_primitive if isinstance(final_output_primitive, str) else (json.dumps(final_output_primitive)[:500])
                except Exception:
                    preview = str(final_output_primitive)[:500]
            else:
                preview = str(final_output_primitive)[:500]

            yield ("step:debug:output_preview", {"type": type_name, "preview": preview})
        except Exception:
            # ignore debug emission errors
            pass

        # final finished event - include final state output if present (serialize)
        yield ("step:finished", {"status": "completed", "session_id": session_id, "output": final_output_primitive})

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
                    dietary_requirement: str = Form(None),
                    do_rag_matching: bool = Form(False),
                    mode: str = Form("normal")):
    """Accept form data, run the Agno workflow and stream results via SSE.

    The client should listen for SSE events of the form `step:<name>` to display progress.
    """
    # Create a session id for tracing
    session_id = str(uuid.uuid4())

    # Build initial workflow state using the canonical 'feeling' field
    state = {
        "feeling": feeling,
        "cuisine": cuisine,
        "dietary_requirement": dietary_requirement,
        "do_rag_matching": do_rag_matching,
        "mode": mode,
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


@app.get("/", response_class=HTMLResponse)
@app.get("/test", response_class=HTMLResponse)
def test_ui():
    # Serve a simple test UI located in app/static/test.html (support both / and /test)
    try:
        with open("app/static/test.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Test UI not found</h1>")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)