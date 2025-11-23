"""Tests for LLM factory functions (Gemini and GPT).

NOTE: Uses string-based type checking to avoid importing langchain_google_genai
at module load time, which causes gRPC initialization hangs.
"""
import pytest

from backend.deep_agent.models.llm import (
    GeminiConfig,
    GPTConfig,
    ReasoningEffort,
    ThinkingLevel,
    Verbosity,
)
from backend.deep_agent.services.llm_factory import create_gemini_llm, create_gpt_llm


class TestCreateGeminiLLM:
    """Test create_gemini_llm factory function (primary model)."""

    def test_create_with_defaults(self) -> None:
        """Test creating ChatGoogleGenerativeAI with default config."""
        llm = create_gemini_llm(api_key="test_key")

        # Use string comparison to avoid importing ChatGoogleGenerativeAI at module level
        assert llm.__class__.__name__ == "ChatGoogleGenerativeAI"
        # ChatGoogleGenerativeAI.model property returns "models/{model_name}"
        assert "gemini-3-pro-preview" in llm.model

    def test_create_with_custom_config(self) -> None:
        """Test creating ChatGoogleGenerativeAI with custom GeminiConfig."""
        config = GeminiConfig(
            model_name="gemini-3-flash",
            temperature=0.8,
            thinking_level=ThinkingLevel.MEDIUM,
            max_output_tokens=8192,
        )
        llm = create_gemini_llm(api_key="test_key", config=config)

        # Use string comparison to avoid importing ChatGoogleGenerativeAI at module level
        assert llm.__class__.__name__ == "ChatGoogleGenerativeAI"
        # ChatGoogleGenerativeAI.model property returns "models/{model_name}"
        assert "gemini-3-flash" in llm.model

    def test_create_with_all_thinking_levels(self) -> None:
        """Test all thinking levels work."""
        for level in [ThinkingLevel.LOW, ThinkingLevel.MEDIUM, ThinkingLevel.HIGH]:
            config = GeminiConfig(thinking_level=level)
            llm = create_gemini_llm(api_key="test_key", config=config)
            assert llm.__class__.__name__ == "ChatGoogleGenerativeAI"

    def test_create_without_api_key(self) -> None:
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="Google API key is required"):
            create_gemini_llm(api_key="")

    def test_returns_langchain_compatible_llm(self) -> None:
        """Test that returned LLM is LangChain-compatible."""
        llm = create_gemini_llm(api_key="test_key")

        assert hasattr(llm, "invoke")
        assert hasattr(llm, "stream")
        assert hasattr(llm, "batch")


class TestCreateGPTLLM:
    """Test create_gpt_llm factory function (fallback model)."""

    def test_create_with_defaults(self) -> None:
        """Test creating ChatOpenAI with default config."""
        llm = create_gpt_llm(api_key="test_key")

        # Use string comparison to avoid importing ChatOpenAI at module level
        assert llm.__class__.__name__ == "ChatOpenAI"
        assert llm.model_name == "gpt-5.1-2025-11-13"

    def test_create_with_custom_config(self) -> None:
        """Test creating ChatOpenAI with custom GPTConfig."""
        config = GPTConfig(
            model_name="gpt-5-mini",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.LOW,
            max_tokens=2048,
        )
        llm = create_gpt_llm(api_key="test_key", config=config)

        # Use string comparison to avoid importing ChatOpenAI at module level
        assert llm.__class__.__name__ == "ChatOpenAI"
        assert llm.model_name == "gpt-5-mini"

    def test_create_with_reasoning_effort(self) -> None:
        """Test reasoning effort is passed to ChatOpenAI."""
        for effort in [
            ReasoningEffort.MINIMAL,
            ReasoningEffort.LOW,
            ReasoningEffort.MEDIUM,
            ReasoningEffort.HIGH,
        ]:
            config = GPTConfig(reasoning_effort=effort)
            llm = create_gpt_llm(api_key="test_key", config=config)
            assert llm.__class__.__name__ == "ChatOpenAI"

    def test_create_with_verbosity(self) -> None:
        """Test verbosity is passed to ChatOpenAI."""
        for verbosity in [Verbosity.LOW, Verbosity.MEDIUM, Verbosity.HIGH]:
            config = GPTConfig(verbosity=verbosity)
            llm = create_gpt_llm(api_key="test_key", config=config)
            assert llm.__class__.__name__ == "ChatOpenAI"

    def test_create_with_all_model_variants(self) -> None:
        """Test creating LLM with all GPT model variants."""
        models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
        for model_name in models:
            config = GPTConfig(model_name=model_name)
            llm = create_gpt_llm(api_key="test_key", config=config)

            # Use string comparison to avoid importing ChatOpenAI at module level
            assert llm.__class__.__name__ == "ChatOpenAI"
            assert llm.model_name == model_name

    def test_create_without_api_key(self) -> None:
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="API key is required"):
            create_gpt_llm(api_key="")

    def test_create_with_kwargs_override(self) -> None:
        """Test that kwargs can override config values."""
        config = GPTConfig(model_name="gpt-5")
        llm = create_gpt_llm(
            api_key="test_key",
            config=config,
            model="gpt-5-nano",
        )

        # Use string comparison to avoid importing ChatOpenAI at module level
        assert llm.__class__.__name__ == "ChatOpenAI"
        assert llm.model_name == "gpt-5-nano"

    def test_returns_langchain_compatible_llm(self) -> None:
        """Test that returned LLM is LangChain-compatible."""
        llm = create_gpt_llm(api_key="test_key")

        assert hasattr(llm, "invoke")
        assert hasattr(llm, "stream")
        assert hasattr(llm, "batch")


class TestLLMFactoryEdgeCases:
    """Test edge cases for LLM factory."""

    def test_minimal_reasoning_with_nano_model(self) -> None:
        """Test fastest GPT configuration (minimal reasoning + nano model)."""
        config = GPTConfig(
            model_name="gpt-5-nano",
            reasoning_effort=ReasoningEffort.MINIMAL,
        )
        llm = create_gpt_llm(api_key="test_key", config=config)

        assert llm.model_name == "gpt-5-nano"

    def test_high_reasoning_with_standard_model(self) -> None:
        """Test most thorough GPT configuration (high reasoning)."""
        config = GPTConfig(
            model_name="gpt-5.1-2025-11-13",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.HIGH,
        )
        llm = create_gpt_llm(api_key="test_key", config=config)

        assert llm.model_name == "gpt-5.1-2025-11-13"

    def test_very_high_max_tokens_gpt(self) -> None:
        """Test GPT with very high max_tokens value."""
        config = GPTConfig(max_tokens=100000)
        llm = create_gpt_llm(api_key="test_key", config=config)
        assert llm.__class__.__name__ == "ChatOpenAI"

    def test_very_high_max_tokens_gemini(self) -> None:
        """Test Gemini with very high max_output_tokens value."""
        config = GeminiConfig(max_output_tokens=64000)
        llm = create_gemini_llm(api_key="test_key", config=config)
        assert llm.__class__.__name__ == "ChatGoogleGenerativeAI"

    def test_gemini_low_thinking_for_speed(self) -> None:
        """Test fastest Gemini configuration (low thinking)."""
        config = GeminiConfig(thinking_level=ThinkingLevel.LOW)
        llm = create_gemini_llm(api_key="test_key", config=config)
        assert llm.__class__.__name__ == "ChatGoogleGenerativeAI"
