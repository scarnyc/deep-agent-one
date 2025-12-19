"""Integration tests for LLM configuration Pydantic models.

This module tests business logic, validation rules, and API contracts
for GPT and Gemini LLM configuration models.
"""

import pytest
from pydantic import ValidationError

from backend.deep_agent.models.llm import (
    THINKING_LEVEL_TO_BUDGET,
    GeminiConfig,
    GPTConfig,
    ReasoningEffort,
    ThinkingLevel,
    Verbosity,
)


class TestGPTConfigValidation:
    """Test GPTConfig model validation rules."""

    def test_config_validation_max_tokens_positive(self) -> None:
        """Test max_tokens must be positive (business rule)."""
        # Valid max_tokens
        config = GPTConfig(max_tokens=1)
        assert config.max_tokens == 1

        config = GPTConfig(max_tokens=10000)
        assert config.max_tokens == 10000

    def test_config_validation_max_tokens_zero_rejected(self) -> None:
        """Test max_tokens cannot be zero (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            GPTConfig(max_tokens=0)

        errors = exc_info.value.errors()
        assert any("max_tokens" in str(error["loc"]) for error in errors)
        assert any(error["type"] == "greater_than" for error in errors)

    def test_config_validation_max_tokens_negative_rejected(self) -> None:
        """Test max_tokens cannot be negative (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            GPTConfig(max_tokens=-1)

        errors = exc_info.value.errors()
        assert any("max_tokens" in str(error["loc"]) for error in errors)

    def test_all_reasoning_efforts(self) -> None:
        """Test all reasoning effort levels are accepted."""
        efforts = [
            ReasoningEffort.MINIMAL,
            ReasoningEffort.LOW,
            ReasoningEffort.MEDIUM,
            ReasoningEffort.HIGH,
        ]
        for effort in efforts:
            config = GPTConfig(reasoning_effort=effort)
            assert config.reasoning_effort == effort

    def test_all_verbosity_levels(self) -> None:
        """Test all verbosity levels are accepted."""
        levels = [Verbosity.LOW, Verbosity.MEDIUM, Verbosity.HIGH]
        for level in levels:
            config = GPTConfig(verbosity=level)
            assert config.verbosity == level

    def test_custom_config_integration(self) -> None:
        """Test GPTConfig with custom values (integration scenario)."""
        config = GPTConfig(
            model_name="gpt-5-mini",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.LOW,
            max_tokens=8192,
        )
        assert config.model_name == "gpt-5-mini"
        assert config.reasoning_effort == ReasoningEffort.HIGH
        assert config.verbosity == Verbosity.LOW
        assert config.max_tokens == 8192


class TestGeminiConfigValidation:
    """Test GeminiConfig model validation rules."""

    def test_temperature_validation_range(self) -> None:
        """Test temperature validation (0.0 to 2.0) - business rule."""
        # Valid temperatures at boundaries
        config = GeminiConfig(temperature=0.0)
        assert config.temperature == 0.0

        config = GeminiConfig(temperature=1.0)
        assert config.temperature == 1.0

        config = GeminiConfig(temperature=2.0)
        assert config.temperature == 2.0

    def test_temperature_validation_below_range(self) -> None:
        """Test temperature below 0.0 is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            GeminiConfig(temperature=-0.1)

        errors = exc_info.value.errors()
        assert any("temperature" in str(error["loc"]) for error in errors)
        assert any(error["type"] == "greater_than_equal" for error in errors)

    def test_temperature_validation_above_range(self) -> None:
        """Test temperature above 2.0 is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            GeminiConfig(temperature=2.1)

        errors = exc_info.value.errors()
        assert any("temperature" in str(error["loc"]) for error in errors)
        assert any(error["type"] == "less_than_equal" for error in errors)

    def test_max_output_tokens_validation_positive(self) -> None:
        """Test max_output_tokens must be positive (business rule)."""
        config = GeminiConfig(max_output_tokens=1)
        assert config.max_output_tokens == 1

        config = GeminiConfig(max_output_tokens=64000)
        assert config.max_output_tokens == 64000

    def test_max_output_tokens_validation_zero_rejected(self) -> None:
        """Test max_output_tokens cannot be zero (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            GeminiConfig(max_output_tokens=0)

        errors = exc_info.value.errors()
        assert any("max_output_tokens" in str(error["loc"]) for error in errors)
        assert any(error["type"] == "greater_than" for error in errors)

    def test_max_output_tokens_validation_negative_rejected(self) -> None:
        """Test max_output_tokens cannot be negative (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            GeminiConfig(max_output_tokens=-1)

        errors = exc_info.value.errors()
        assert any("max_output_tokens" in str(error["loc"]) for error in errors)

    def test_custom_config_integration(self) -> None:
        """Test GeminiConfig with custom values (integration scenario)."""
        config = GeminiConfig(
            model_name="gemini-3-pro",
            temperature=0.8,
            thinking_level=ThinkingLevel.LOW,
            max_output_tokens=8192,
            streaming=False,
        )
        assert config.model_name == "gemini-3-pro"
        assert config.temperature == 0.8
        assert config.thinking_level == ThinkingLevel.LOW
        assert config.max_output_tokens == 8192
        assert config.streaming is False


class TestThinkingLevelToBudgetMapping:
    """Test THINKING_LEVEL_TO_BUDGET constant mapping (integration).

    This mapping is critical for LangChain integration since google-ai-generativelanguage
    v0.9.0 only supports thinking_budget (token count), not thinking_level strings.
    """

    def test_mapping_has_all_levels(self) -> None:
        """Test that mapping covers all ThinkingLevel values."""
        assert "low" in THINKING_LEVEL_TO_BUDGET
        assert "high" in THINKING_LEVEL_TO_BUDGET

    def test_budget_values_are_correct(self) -> None:
        """Test budget values match expected token counts."""
        assert THINKING_LEVEL_TO_BUDGET["low"] == 1024
        assert THINKING_LEVEL_TO_BUDGET["high"] == 8192

    def test_high_budget_greater_than_low(self) -> None:
        """Test high thinking budget is greater than low."""
        assert THINKING_LEVEL_TO_BUDGET["high"] > THINKING_LEVEL_TO_BUDGET["low"]

    def test_mapping_integration_with_config(self) -> None:
        """Test mapping can be used with GeminiConfig (integration scenario)."""
        config = GeminiConfig(thinking_level=ThinkingLevel.HIGH)
        budget = THINKING_LEVEL_TO_BUDGET[config.thinking_level.value]

        assert budget == 8192
        assert isinstance(budget, int)
        assert budget > 0


class TestProviderConfigComparison:
    """Test integration scenarios comparing GPT and Gemini configs."""

    def test_default_configs_differ_in_parameters(self) -> None:
        """Test that GPT and Gemini have different default parameters."""
        gpt_config = GPTConfig()
        gemini_config = GeminiConfig()

        # GPT uses reasoning_effort, Gemini uses thinking_level
        assert hasattr(gpt_config, "reasoning_effort")
        assert hasattr(gemini_config, "thinking_level")

        # GPT has verbosity, Gemini doesn't
        assert hasattr(gpt_config, "verbosity")
        assert not hasattr(gemini_config, "verbosity")

        # Gemini has temperature, GPT doesn't (GPT-5.1)
        assert hasattr(gemini_config, "temperature")
        assert not hasattr(gpt_config, "temperature")

    def test_both_configs_have_max_tokens_field(self) -> None:
        """Test both providers support max tokens (different field names)."""
        gpt_config = GPTConfig()
        gemini_config = GeminiConfig()

        assert hasattr(gpt_config, "max_tokens")
        assert hasattr(gemini_config, "max_output_tokens")

        # Both should have positive default values
        assert gpt_config.max_tokens > 0
        assert gemini_config.max_output_tokens > 0
