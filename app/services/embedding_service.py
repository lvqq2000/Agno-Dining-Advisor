from openai import OpenAI

client = OpenAI()

def get_embedding(text: str) -> list[float]:
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding