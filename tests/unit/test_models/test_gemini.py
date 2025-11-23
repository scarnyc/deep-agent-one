"""Tests for Gemini Pydantic models."""
import pytest
from pydantic import ValidationError

from backend.deep_agent.models.llm import (
    GeminiConfig,
    ThinkingLevel,
)


class TestThinkingLevel:
    """Test ThinkingLevel enum."""

    def test_thinking_level_values(self) -> None:
        """Test all thinking level enum values."""
        assert ThinkingLevel.LOW == "low"
        assert ThinkingLevel.MEDIUM == "medium"
        assert ThinkingLevel.HIGH == "high"

    def test_thinking_level_from_string(self) -> None:
        """Test creating ThinkingLevel from string."""
        assert ThinkingLevel("low") == ThinkingLevel.LOW
        assert ThinkingLevel("medium") == ThinkingLevel.MEDIUM
        assert ThinkingLevel("high") == ThinkingLevel.HIGH


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
            thinking_level=ThinkingLevel.MEDIUM,
            max_output_tokens=8192,
            streaming=False,
        )
        assert config.model_name == "gemini-3-pro"
        assert config.temperature == 0.8
        assert config.thinking_level == ThinkingLevel.MEDIUM
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
            "thinking_level": "medium",
            "max_output_tokens": 2048,
        }
        config = GeminiConfig(**data)

        assert config.model_name == "gemini-3-flash"
        assert config.temperature == 1.5
        assert config.thinking_level == ThinkingLevel.MEDIUM

    def test_default_temperature_is_one(self) -> None:
        """Test default temperature is 1.0 per Google recommendation."""
        config = GeminiConfig()
        assert config.temperature == 1.0

    def test_default_thinking_level_is_high(self) -> None:
        """Test default thinking level is HIGH per Google default."""
        config = GeminiConfig()
        assert config.thinking_level == ThinkingLevel.HIGH
