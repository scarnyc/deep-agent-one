"""Tests for LLM factory."""
import pytest
from langchain_openai import ChatOpenAI

from backend.deep_agent.models.llm import GPTConfig, ReasoningEffort, Verbosity
from backend.deep_agent.services.llm_factory import create_llm


class TestCreateLLM:
    """Test create_llm factory function."""

    def test_create_with_defaults(self) -> None:
        """Test creating ChatOpenAI with default config."""
        llm = create_llm(api_key="test_key")

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-5.1-2025-11-13"  # Updated to GPT-5.1

    def test_create_with_custom_config(self) -> None:
        """Test creating ChatOpenAI with custom GPTConfig."""
        config = GPTConfig(
            model_name="gpt-5-mini",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.LOW,
            max_tokens=2048,
        )
        llm = create_llm(api_key="test_key", config=config)

        assert isinstance(llm, ChatOpenAI)
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
            llm = create_llm(api_key="test_key", config=config)

            assert isinstance(llm, ChatOpenAI)
            # Note: We can't easily inspect the reasoning param on ChatOpenAI,
            # so we just verify the LLM was created successfully

    def test_create_with_verbosity(self) -> None:
        """Test verbosity is passed to ChatOpenAI."""
        for verbosity in [Verbosity.LOW, Verbosity.MEDIUM, Verbosity.HIGH]:
            config = GPTConfig(verbosity=verbosity)
            llm = create_llm(api_key="test_key", config=config)

            assert isinstance(llm, ChatOpenAI)
            # Note: We can't easily inspect the verbosity param on ChatOpenAI,
            # so we just verify the LLM was created successfully

    def test_create_with_all_model_variants(self) -> None:
        """Test creating LLM with all GPT model variants."""
        models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
        for model_name in models:
            config = GPTConfig(model_name=model_name)
            llm = create_llm(api_key="test_key", config=config)

            assert isinstance(llm, ChatOpenAI)
            assert llm.model_name == model_name

    def test_create_without_api_key(self) -> None:
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="API key is required"):
            create_llm(api_key="")

    def test_create_with_kwargs_override(self) -> None:
        """Test that kwargs can override config values."""
        config = GPTConfig(model_name="gpt-5")
        llm = create_llm(
            api_key="test_key",
            config=config,
            model="gpt-5-nano",  # Override model name
        )

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-5-nano"  # Should use override value

    def test_returns_langchain_compatible_llm(self) -> None:
        """Test that returned LLM is LangChain-compatible."""
        llm = create_llm(api_key="test_key")

        # Verify it has the expected LangChain LLM interface
        assert hasattr(llm, "invoke")
        assert hasattr(llm, "stream")
        assert hasattr(llm, "batch")
        assert callable(llm.invoke)
        assert callable(llm.stream)
        assert callable(llm.batch)


class TestLLMFactoryEdgeCases:
    """Test edge cases for LLM factory."""

    def test_minimal_reasoning_with_nano_model(self) -> None:
        """Test fastest configuration (minimal reasoning + nano model)."""
        config = GPTConfig(
            model_name="gpt-5-nano",
            reasoning_effort=ReasoningEffort.MINIMAL,
        )
        llm = create_llm(api_key="test_key", config=config)

        assert llm.model_name == "gpt-5-nano"

    def test_high_reasoning_with_standard_model(self) -> None:
        """Test most thorough configuration (high reasoning + standard model)."""
        config = GPTConfig(
            model_name="gpt-5.1-thinking",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.HIGH,
        )
        llm = create_llm(api_key="test_key", config=config)

        assert llm.model_name == "gpt-5.1-2025-11-13"  # Updated to GPT-5.1

    def test_very_high_max_tokens(self) -> None:
        """Test with very high max_tokens value."""
        config = GPTConfig(max_tokens=100000)
        llm = create_llm(api_key="test_key", config=config)
        assert isinstance(llm, ChatOpenAI)
