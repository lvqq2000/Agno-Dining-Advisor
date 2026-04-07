import os
from app.core.constants import SIMILARITY_THRESHOLD

# Keep the model id as a simple string. The app's OpenAI/LLM service will
# decide how to use this identifier with the chosen client library.
# Model identifier should include the provider prefix expected by Agno, e.g. 'openai:gpt-4o-mini'
MODEL_ID = os.getenv("MODEL_ID", "openai:gpt-4o-mini")

# Use a plain string for the default model identifier to avoid SDK-specific
# object construction at import time (which caused startup failures).
DEFAULT_MODEL = MODEL_ID