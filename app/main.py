from app.workflows.main_workflow import create_workflow

workflow = create_workflow()

if __name__ == "__main__":
    response = workflow.run(
        input="I want cheap sushi",
        stream=False,
    )

    print("\n--- RESULT ---")
    print(response)