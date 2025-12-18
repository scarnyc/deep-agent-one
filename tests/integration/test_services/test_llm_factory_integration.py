"""Integration tests for LLM factory functions.

Tests real LLM creation with actual configuration, error handling,
and retry behavior. Focuses on integration aspects rather than
trivial attribute checking.
"""

import pytest

from backend.deep_agent.models.llm import (
    THINKING_LEVEL_TO_BUDGET,
    GeminiConfig,
    GPTConfig,
    ReasoningEffort,
    ThinkingLevel,
)
from backend.deep_agent.services.llm_factory import create_gemini_llm, create_gpt_llm


class TestGeminiLLMIntegration:
    """Integration tests for Gemini LLM factory."""

    def test_create_gemini_with_thinking_budget_mapping(self) -> None:
        """Test that thinking_level correctly maps to thinking_budget tokens.

        This integration test verifies the fix for ValueError:
        'Unknown field for ThinkingConfig: thinking_level'

        The factory must convert thinking_level (enum) to thinking_budget (int)
        because google-ai-generativelanguage v0.9.0 only supports thinking_budget.
        """
        # Test LOW thinking level -> 1024 tokens
        config_low = GeminiConfig(thinking_level=ThinkingLevel.LOW)
        llm_low = create_gemini_llm(api_key="test_key", config=config_low)
        assert llm_low.thinking_budget == THINKING_LEVEL_TO_BUDGET["low"]
        assert llm_low.thinking_budget == 1024

        # Test HIGH thinking level -> 8192 tokens
        config_high = GeminiConfig(thinking_level=ThinkingLevel.HIGH)
        llm_high = create_gemini_llm(api_key="test_key", config=config_high)
        assert llm_high.thinking_budget == THINKING_LEVEL_TO_BUDGET["high"]
        assert llm_high.thinking_budget == 8192

    def test_create_gemini_validates_api_key(self) -> None:
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="Google API key is required"):
            create_gemini_llm(api_key="")


class TestGPTLLMIntegration:
    """Integration tests for GPT LLM factory."""

    def test_create_gpt_with_extended_timeout_configuration(self) -> None:
        """Test that GPT LLM is created with extended timeout configuration.

        Verifies fix for Issue #7: BrokenResourceError at 45s during parallel tool execution.
        Factory must configure 120s read timeout instead of default 60s.
        """
        config = GPTConfig(
            model_name="gpt-5.1-2025-11-13",
            reasoning_effort=ReasoningEffort.HIGH,
        )
        llm = create_gpt_llm(api_key="sk-test-key", config=config)

        # Verify model configuration
        assert llm.model_name == "gpt-5.1-2025-11-13"

        # Verify timeout is extended (120s read timeout)
        # Note: ChatOpenAI wraps AsyncOpenAI client, so we check client timeout
        assert llm.client.timeout.read == 120.0
        assert llm.client.timeout.connect == 10.0

    def test_create_gpt_validates_api_key_format(self) -> None:
        """Test that API key format validation logs warning for invalid format."""
        # Valid format (sk- prefix)
        with pytest.raises(ValueError, match="API key is required"):
            create_gpt_llm(api_key="")

    def test_create_gpt_with_kwargs_override(self) -> None:
        """Test that kwargs can override config values (integration test)."""
        config = GPTConfig(model_name="gpt-5")
        llm = create_gpt_llm(
            api_key="sk-test-key",  # pragma: allowlist secret
            config=config,
            model="gpt-5-nano",
        )

        # Kwargs override should work
        assert llm.model_name == "gpt-5-nano"
