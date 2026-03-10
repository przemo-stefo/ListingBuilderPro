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
    "beast": {"default_model": "qwen3:235b", "label": "Beast AI (unlimited)"},
    "gemini_flash": {"default_model": "gemini-2.0-flash", "label": "Gemini Flash"},
    "gemini_pro": {"default_model": "gemini-2.5-pro-preview-06-05", "label": "Gemini Pro"},
    "openai": {"default_model": "gpt-4o-mini", "label": "OpenAI"},
}

# WHY: Cost per 1M tokens — used by trace_service for accurate cost tracking per model
COST_TABLE: Dict[str, dict] = {
    "llama-3.3-70b-versatile": {"prompt": 0.59, "completion": 0.79},
    "qwen3:235b": {"prompt": 0.00, "completion": 0.00},  # WHY: Local Beast — zero API cost
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

    WHY: Uses per-request configure() call — google-generativeai doesn't
    have a Client-based API, so we reconfigure before each call. This is
    safe because Gemini calls are dispatched through this single function.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model)
    response = gen_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
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


def _call_beast(
    model: str, prompt: str, temperature: float, max_tokens: int,
) -> Tuple[str, Optional[dict]]:
    """Call Beast (local Ollama) via OpenAI-compatible API. Returns (text, usage_dict).

    WHY: Beast = Mac Studio M3 Ultra 512GB running qwen3:235b locally.
    Zero cost, no rate limits, unlimited tokens. Uses OpenAI client with custom base_url.
    """
    from openai import OpenAI
    from config import settings

    if not settings.beast_ollama_url:
        raise ValueError("Beast nie jest skonfigurowany. Ustaw BEAST_OLLAMA_URL w .env")

    client = OpenAI(
        api_key="ollama",  # WHY: Ollama ignores API key but OpenAI client requires one
        base_url=f"{settings.beast_ollama_url}/v1",
    )
    response = client.chat.completions.create(
        model=model or settings.beast_model,
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
            "model": model or settings.beast_model,
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

    if provider == "beast":
        return _call_beast(resolved_model, prompt, temperature, max_tokens)
    elif provider in ("gemini_flash", "gemini_pro"):
        return _call_gemini(api_key, resolved_model, prompt, temperature, max_tokens)
    elif provider == "openai":
        return _call_openai(api_key, resolved_model, prompt, temperature, max_tokens)
    else:
        raise ValueError(f"Provider '{provider}' must use groq_client.call_groq()")
