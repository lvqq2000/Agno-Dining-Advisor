import os
from openai import OpenAI

MODEL_ID = os.getenv("MODEL_ID", "gpt-4o-mini")

DEFAULT_MODEL = OpenAI.Model(id=MODEL_ID)