from app.agents.rag_match import create_rag_match_agent


def rag_retrieve_step(state):
    """Retrieve RAG context for the current request.

    This step is intentionally lightweight: it will attempt to use the RAG agent
    to find relevant documents for the detected dining styles or user input.
    Results are stored on state['rag_results'] as a list (possibly empty).
    """
    # Use the canonical 'feeling' free-text field
    user_input = state["feeling"]
    cag = state.get("cag_result", {})

    try:
        agent = create_rag_match_agent()
        # Agent.run should consult its knowledge base when `search_knowledge=True`.
        # Provide either dining style or free text preference.
        query = None
        if cag and cag.get("dining_styles"):
            query = ", ".join(cag.get("dining_styles"))
        else:
            query = user_input

        result = agent.run({"query": query})

        # store raw rag output on state for later prompt assembly
        state["rag_results"] = result
        return state

    except Exception as e:
        # non-fatal: store error and continue without RAG context
        state["rag_results"] = []
        state["rag_error"] = str(e)
        return state
