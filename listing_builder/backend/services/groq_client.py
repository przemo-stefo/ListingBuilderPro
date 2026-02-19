# backend/services/groq_client.py
# Purpose: Groq LLM client with automatic key rotation on 429 rate limits
# NOT for: Prompt construction (that's prompt_builders.py) or scoring logic

from __future__ import annotations

import re
from typing import Tuple, Optional, Dict
from groq import Groq
from config import settings
import structlog

logger = structlog.get_logger()

# WHY: Model from env var — allows testing Llama 4 Maverick, Kimi K2, DeepSeek V4
# without code changes. Default: llama-3.3-70b-versatile (proven stable)
MODEL = settings.groq_model

# WHY: Reuse Groq client objects — avoids recreating HTTP session per call.
# Keyed by API key string so each key gets its own persistent client.
_client_cache: Dict[str, Groq] = {}

# WHY: Common LLM injection patterns that attackers embed in product titles/keywords.
# These regex patterns catch "Ignore all previous instructions", "You are now a ...",
# and role-injection attempts like "system:" or "assistant:" prefixes.
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above|prior)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"(?:^|\n)\s*(?:system|assistant|human)\s*:", re.IGNORECASE),
    re.compile(r"<\s*/?\s*(?:system|instruction|prompt)\s*>", re.IGNORECASE),
]


def sanitize_llm_input(text: str) -> str:
    """Strip control characters and LLM injection patterns from user input.

    WHY: User-supplied product_title, brand, keywords go into LLM prompts.
    An attacker could inject "Ignore all instructions..." to hijack the prompt.
    We strip injection patterns, control chars, and truncate to safe length.
    """
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    # WHY: Strip injection attempts — precompiled patterns for performance
    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    return cleaned[:1000]


def _get_client(key: str) -> Groq:
    """Return cached Groq client for a given API key."""
    if key not in _client_cache:
        _client_cache[key] = Groq(api_key=key)
    return _client_cache[key]


def call_groq(prompt: str, temperature: float, max_tokens: int) -> Tuple[str, Optional[dict]]:
    """Synchronous Groq call with automatic key rotation on 429 rate limits.

    Returns (text, usage_dict | None) — usage_dict contains token counts for tracing.
    """
    keys = settings.groq_api_keys
    last_error = None

    for i, key in enumerate(keys):
        try:
            client = _get_client(key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content.strip()
            # WHY: Extract token usage for observability tracing
            usage = None
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "model": MODEL,
                }
            return text, usage
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e):
                logger.warning("groq_rate_limit", key_index=i, remaining_keys=len(keys) - i - 1)
                continue
            raise

    raise last_error
