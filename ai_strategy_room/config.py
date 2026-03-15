"""
config.py — Central settings for AI Decision Simulation Lab.

Loads API keys from .env and provides model configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── LLM Provider ────────────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # gemini | groq | anthropic | openai
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# ── API Keys ────────────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── n8n Integration (optional) ──────────────────────────────────────────────
N8N_WEBHOOK_URL: str = os.getenv("N8N_WEBHOOK_URL", "")  # If set, tool calls route to n8n

# ── Simulation Defaults ─────────────────────────────────────────────────────
DEFAULT_NUM_ROUNDS: int = 3
MAX_NEGOTIATION_PROPOSALS: int = 3
BLACK_SWAN_PROBABILITY: float = float(os.getenv("BLACK_SWAN_PROBABILITY", "0.35"))
CHAOS_MODE: bool = os.getenv("CHAOS_MODE", "false").lower() == "true"


MODELS = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}


def get_chat_model():
    """Return a LangChain chat model based on the configured provider.
    Reads env vars fresh each call so BYOK sidebar overrides work."""
    provider = os.getenv("LLM_PROVIDER", "gemini")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    model_id = MODELS.get(provider, MODELS["gemini"])

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_id, temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY", ""), max_output_tokens=2048,
            timeout=30,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_id, temperature=temperature,
            groq_api_key=os.getenv("GROQ_API_KEY", ""), max_tokens=2048,
            timeout=30,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_id, temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY", ""), max_tokens=2048,
            timeout=30,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_id, temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY", ""), max_tokens=2048,
            timeout=30,
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
