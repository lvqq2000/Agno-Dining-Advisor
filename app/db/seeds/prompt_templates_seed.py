JSON_RESPONSE_FORMAT = """
Return the result in JSON format:
{
  "recommendations": [
    {
      "name": "",
      "location": "",
      "description": ""
    }
  ]
}
"""

PROMPT_TEMPLATES_SEED = [
    {
        "template_type": "standard",
        "version": 1,
        "template": """You are a dining recommendation assistant.

User preferences:
- Cuisine: {{cuisine}}
- Dietary requirements: {{dietary_requirement}}
- Dining style: {{dining_style}}

Based on the above, recommend 3 real restaurants in Melbourne.

For each restaurant, include:
- Name
- Location
- Short funny description (maximum 60 words)

{JSON_RESPONSE_FORMAT}
""",
    },
    {
        "template_type": "random",
        "version": 1,
        "template": """You are a dining recommendation assistant.

Recommend 3 real restaurants in Melbourne.

For each restaurant, include:
- Name
- Location
- Short funny description (maximum 60 words)

{JSON_RESPONSE_FORMAT}
""",
    },
]