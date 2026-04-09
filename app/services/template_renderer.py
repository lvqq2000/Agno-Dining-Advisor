from app.db.seeds.prompt_templates_seed import JSON_RESPONSE_FORMAT

def render_template(template: str, variables: dict) -> str:
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        template = template.replace(placeholder, str(value))

    # Replace single-brace constants (e.g. {JSON_RESPONSE_FORMAT}) if present in template
    if "{JSON_RESPONSE_FORMAT}" in template:
        template = template.replace("{JSON_RESPONSE_FORMAT}", JSON_RESPONSE_FORMAT)

    return template