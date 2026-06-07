from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

DEFAULT_PROVIDER = os.getenv("AGENTFLOW_MODEL_PROVIDER", "openai")
DEFAULT_MODEL = os.getenv("AGENTFLOW_MODEL_NAME", "gpt-4o-mini")
SAMPLE_DOCS_DIR = os.getenv(
    "AGENTFLOW_DOCS_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge"),
)


@lru_cache(maxsize=1)
def get_chat_model():
    provider = DEFAULT_PROVIDER.lower()
    if provider == "anthropic":
        model_id = f"anthropic:{DEFAULT_MODEL}"
    else:
        model_id = f"openai:{DEFAULT_MODEL}"
    return init_chat_model(model_id, temperature=0)


def require_api_key() -> None:
    provider = DEFAULT_PROVIDER.lower()
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for anthropic provider")
    if provider != "anthropic" and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for openai provider")
