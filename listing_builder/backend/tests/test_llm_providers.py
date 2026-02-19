# backend/tests/test_llm_providers.py
# Purpose: Unit tests for LLM provider abstraction
# NOT for: Integration tests with real API keys

import pytest
from services.llm_providers import (
    PROVIDERS,
    COST_TABLE,
    get_cost_per_1m,
    mask_api_key,
    call_llm,
)


def test_providers_registry_has_required_keys():
    """All expected providers exist with default_model."""
    for provider in ("groq", "gemini_flash", "gemini_pro", "openai"):
        assert provider in PROVIDERS
        assert "default_model" in PROVIDERS[provider]


def test_cost_table_covers_all_default_models():
    """Every provider's default model has a cost entry."""
    for provider, config in PROVIDERS.items():
        model = config["default_model"]
        assert model in COST_TABLE, f"Missing cost entry for {model}"
        assert "prompt" in COST_TABLE[model]
        assert "completion" in COST_TABLE[model]


def test_get_cost_per_1m_known_model():
    cost = get_cost_per_1m("gemini-2.0-flash")
    assert cost["prompt"] == 0.10
    assert cost["completion"] == 0.40


def test_get_cost_per_1m_unknown_model_falls_back():
    """Unknown model returns Groq pricing as fallback."""
    cost = get_cost_per_1m("nonexistent-model-xyz")
    assert cost == COST_TABLE["llama-3.3-70b-versatile"]


def test_mask_api_key_normal():
    assert mask_api_key("AIzaSyD12345abcdefgh") == "AIza****efgh"


def test_mask_api_key_short():
    assert mask_api_key("abc") == "****"


def test_mask_api_key_empty():
    assert mask_api_key("") == "****"


def test_mask_api_key_exactly_8():
    assert mask_api_key("12345678") == "1234****5678"


def test_call_llm_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        call_llm("nonexistent", "key", None, "hello", 0.5, 100)


def test_call_llm_groq_raises():
    """Groq should use groq_client directly, not call_llm."""
    with pytest.raises(ValueError, match="must use groq_client"):
        call_llm("groq", "key", None, "hello", 0.5, 100)
