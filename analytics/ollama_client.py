import logging

import requests

from config.settings import settings


logger = logging.getLogger("mittelstand_ai.ollama")

OLLAMA_URL = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
MODEL_NAME = settings.ollama_model


def ask_ollama(prompt):
    """Send a prompt to the locally running Ollama model."""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=settings.ollama_timeout,
        )

        response.raise_for_status()

        result = response.json()
        return result.get("response", "").strip()

    except requests.exceptions.RequestException as error:
        logger.exception("Ollama request failed.")
        return f"Ollama connection error: {error}"