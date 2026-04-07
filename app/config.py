import os
from agno.models.anthropic import Claude

MODEL_ID = os.getenv("MODEL_ID", "claude-sonnet-4-6")

DEFAULT_MODEL = Claude(id=MODEL_ID)