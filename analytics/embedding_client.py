import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"


def get_embedding(text):
    """Generate a text embedding using the local Ollama model."""

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }

    response = requests.post(
        OLLAMA_EMBED_URL,
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    result = response.json()
    embedding = result["embeddings"][0]

    if len(embedding) != 768:
        raise ValueError(
            f"Expected 768 dimensions, received {len(embedding)}."
        )

    return embedding
