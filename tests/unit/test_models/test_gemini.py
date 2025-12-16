"""Tests for Gemini Pydantic models."""

import pytest
from pydantic import ValidationError

from backend.deep_agent.models.llm import (
    THINKING_LEVEL_TO_BUDGET,
    GeminiConfig,
    ThinkingLevel,
)


class TestThinkingLevel:
    """Test ThinkingLevel enum."""

    def test_thinking_level_values(self) -> None:
        """Test all thinking level enum values (API only accepts 'low' or 'high')."""
        assert ThinkingLevel.LOW == "low"
        assert ThinkingLevel.HIGH == "high"

    def test_thinking_level_from_string(self) -> None:
        """Test creating ThinkingLevel from string."""
        assert ThinkingLevel("low") == ThinkingLevel.LOW
        assert ThinkingLevel("high") == ThinkingLevel.HIGH


class TestThinkingLevelToBudget:
    """Test THINKING_LEVEL_TO_BUDGET mapping constant.

    This mapping is required because google-ai-generativelanguage v0.9.0
    ThinkingConfig only supports thinking_budget (token count), not thinking_level.
    """

    def test_mapping_has_all_levels(self) -> None:
        """Test that mapping covers all ThinkingLevel values."""
        assert "low" in THINKING_LEVEL_TO_BUDGET
        assert "high" in THINKING_LEVEL_TO_BUDGET

    def test_low_level_budget(self) -> None:
        """Test low thinking level maps to 1024 tokens."""
        assert THINKING_LEVEL_TO_BUDGET["low"] == 1024

    def test_high_level_budget(self) -> None:
        """Test high thinking level maps to 8192 tokens."""
        assert THINKING_LEVEL_TO_BUDGET["high"] == 8192

    def test_budget_values_are_positive(self) -> None:
        """Test all budget values are positive integers."""
        for _level, budget in THINKING_LEVEL_TO_BUDGET.items():
            assert isinstance(budget, int)
            assert budget > 0

    def test_high_budget_greater_than_low(self) -> None:
        """Test high thinking budget is greater than low."""
        assert THINKING_LEVEL_TO_BUDGET["high"] > THINKING_LEVEL_TO_BUDGET["low"]


class TestGeminiConfig:
    """Test GeminiConfig model."""

    def test_default_config(self) -> None:
        """Test GeminiConfig with default values."""
        config = GeminiConfig()
        assert config.model_name == "gemini-3-pro-preview"
        assert config.temperature == 1.0
        assert config.thinking_level == ThinkingLevel.HIGH
        assert config.max_output_tokens == 4096
        assert config.streaming is True

    def test_custom_config(self) -> None:
        """Test GeminiConfig with custom values."""
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

    def test_temperature_validation(self) -> None:
        """Test temperature validation (0.0 to 2.0)."""
        GeminiConfig(temperature=0.0)
        GeminiConfig(temperature=1.0)
        GeminiConfig(temperature=2.0)

        with pytest.raises(ValidationError):
            GeminiConfig(temperature=-0.1)
        with pytest.raises(ValidationError):
            GeminiConfig(temperature=2.1)

    def test_max_output_tokens_validation(self) -> None:
        """Test max_output_tokens validation."""
        GeminiConfig(max_output_tokens=1)
        GeminiConfig(max_output_tokens=64000)

        with pytest.raises(ValidationError):
            GeminiConfig(max_output_tokens=0)
        with pytest.raises(ValidationError):
            GeminiConfig(max_output_tokens=-1)

    def test_config_serialization(self) -> None:
        """Test GeminiConfig serialization to dict."""
        config = GeminiConfig(thinking_level=ThinkingLevel.LOW, temperature=0.7)
        data = config.model_dump()

        assert data["model_name"] == "gemini-3-pro-preview"
        assert data["temperature"] == 0.7
        assert data["thinking_level"] == "low"

    def test_config_deserialization(self) -> None:
        """Test GeminiConfig deserialization from dict."""
        data = {
            "model_name": "gemini-3-flash",
            "temperature": 1.5,
            "thinking_level": "high",
            "max_output_tokens": 2048,
        }
        config = GeminiConfig(**data)

        assert config.model_name == "gemini-3-flash"
        assert config.temperature == 1.5
        assert config.thinking_level == ThinkingLevel.HIGH

    def test_default_temperature_is_one(self) -> None:
        """Test default temperature is 1.0 per Google recommendation."""
        config = GeminiConfig()
        assert config.temperature == 1.0

    def test_default_thinking_level_is_high(self) -> None:
        """Test default thinking level is HIGH per Google default."""
        config = GeminiConfig()
        assert config.thinking_level == ThinkingLevel.HIGH
