from app.db.models.trace import Trace


def create_trace(db_session, session_id: str, step_name: str, input_text: str, output_text: str, status: str, prompt_version: int = None):
    trace = Trace(
        session_id=session_id,
        step_name=step_name,
        input=input_text,
        output=output_text,
        status=status,
        prompt_version=prompt_version,
    )
    db_session.add(trace)
    db_session.commit()
    db_session.refresh(trace)
    return trace


def get_traces_by_session(db_session, session_id: str):
    rows = db_session.query(Trace).filter_by(session_id=session_id).order_by(Trace.created_at).all()
    # convert to plain dicts for JSON serialisation
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "session_id": r.session_id,
            "step_name": r.step_name,
            "input": r.input,
            "output": r.output,
            "status": r.status,
            "prompt_version": r.prompt_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result
