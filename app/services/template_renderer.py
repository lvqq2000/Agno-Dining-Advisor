def render_template(template: str, variables: dict) -> str:
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        template = template.replace(placeholder, str(value))
    return template