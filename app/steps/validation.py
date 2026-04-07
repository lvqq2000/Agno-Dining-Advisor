from app.models.response import ResponseModel

def validate_output(step_input):
    data = step_input.previous_step_content
    return ResponseModel(**data).model_dump()