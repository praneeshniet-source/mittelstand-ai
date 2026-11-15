
import requests

from config.settings import settings


OLLAMA_EMBED_URL = (
    f"{settings.ollama_base_url.rstrip('/')}/api/embed"
)

EMBEDDING_MODEL = settings.embedding_model


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
        timeout=settings.ollama_timeout
    )

    response.raise_for_status()

    result = response.json()
    embedding = result["embeddings"][0]

    if len(embedding) != settings.embedding_dimensions:
        raise ValueError(
            f"Expected {settings.embedding_dimensions} dimensions, "
            f"received {len(embedding)}."
        )

    return embedding
