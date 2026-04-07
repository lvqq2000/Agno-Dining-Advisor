def call_agent(agent, prompt: str) -> str:
    response = agent.run(prompt)
    return response