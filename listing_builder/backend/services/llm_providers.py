# backend/services/llm_providers.py
# Purpose: Multi-LLM provider abstraction — dispatches to Groq, Gemini, or OpenAI
# NOT for: Prompt construction (prompt_builders.py) or Groq key rotation (groq_client.py)

from __future__ import annotations

from typing import Tuple, Optional, Dict
import structlog

logger = structlog.get_logger()

# WHY: Central registry — add new providers here, everything else reads from this
PROVIDERS: Dict[str, dict] = {
    "groq": {"default_model": "llama-3.3-70b-versatile", "label": "Groq (w cenie)"},
    "gemini_flash": {"default_model": "gemini-2.0-flash", "label": "Gemini Flash"},
    "gemini_pro": {"default_model": "gemini-2.5-pro-preview-06-05", "label": "Gemini Pro"},
    "openai": {"default_model": "gpt-4o-mini", "label": "OpenAI"},
}

# WHY: Cost per 1M tokens — used by trace_service for accurate cost tracking per model
COST_TABLE: Dict[str, dict] = {
    "llama-3.3-70b-versatile": {"prompt": 0.59, "completion": 0.79},
    "gemini-2.0-flash": {"prompt": 0.10, "completion": 0.40},
    "gemini-2.5-pro-preview-06-05": {"prompt": 1.25, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
}


def get_cost_per_1m(model: str) -> dict:
    """Return cost dict for a model, defaulting to Groq pricing if unknown."""
    return COST_TABLE.get(model, COST_TABLE["llama-3.3-70b-versatile"])


def mask_api_key(key: str) -> str:
    """Mask API key for safe display: 'AIza****abcd'."""
    if not key or len(key) < 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _call_gemini(
    api_key: str, model: str, prompt: str, temperature: float, max_tokens: int,
) -> Tuple[str, Optional[dict]]:
    """Call Google Gemini API. Returns (text, usage_dict).

    WHY: Uses per-request client instead of global genai.configure() —
    genai.configure() sets module-level state, so concurrent requests with
    different API keys would race. Client-based approach is thread-safe.
    """
    from google import genai as genai_client

    client = genai_client.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        },
    )

    text = response.text.strip()
    usage = None
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        usage = {
            "prompt_tokens": getattr(um, "prompt_token_count", 0),
            "completion_tokens": getattr(um, "candidates_token_count", 0),
            "total_tokens": getattr(um, "total_token_count", 0),
            "model": model,
        }
    return text, usage


def _call_openai(
    api_key: str, model: str, prompt: str, temperature: float, max_tokens: int,
) -> Tuple[str, Optional[dict]]:
    """Call OpenAI API. Returns (text, usage_dict)."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    text = response.choices[0].message.content.strip()
    usage = None
    if hasattr(response, "usage") and response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "model": model,
        }
    return text, usage


def call_llm(
    provider: str,
    api_key: str,
    model: str | None,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> Tuple[str, Optional[dict]]:
    """Dispatch LLM call to the correct provider.

    For provider='groq', callers should use groq_client.call_groq() directly
    (it has key rotation). This function handles gemini_flash, gemini_pro, openai.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider}")

    resolved_model = model or PROVIDERS[provider]["default_model"]

    logger.info("llm_call", provider=provider, model=resolved_model)

    if provider in ("gemini_flash", "gemini_pro"):
        return _call_gemini(api_key, resolved_model, prompt, temperature, max_tokens)
    elif provider == "openai":
        return _call_openai(api_key, resolved_model, prompt, temperature, max_tokens)
    else:
        raise ValueError(f"Provider '{provider}' must use groq_client.call_groq()")
