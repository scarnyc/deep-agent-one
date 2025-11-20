"""Tests for GPT-5 Pydantic models."""
import pytest
from pydantic import ValidationError

from backend.deep_agent.models.gpt5 import (
    GPT5Config,
    ReasoningEffort,
    Verbosity,
)


class TestReasoningEffort:
    """Test ReasoningEffort enum."""

    def test_reasoning_effort_values(self) -> None:
        """Test all reasoning effort enum values."""
        assert ReasoningEffort.MINIMAL == "minimal"
        assert ReasoningEffort.LOW == "low"
        assert ReasoningEffort.MEDIUM == "medium"
        assert ReasoningEffort.HIGH == "high"

    def test_reasoning_effort_from_string(self) -> None:
        """Test creating ReasoningEffort from string."""
        assert ReasoningEffort("minimal") == ReasoningEffort.MINIMAL
        assert ReasoningEffort("low") == ReasoningEffort.LOW
        assert ReasoningEffort("medium") == ReasoningEffort.MEDIUM
        assert ReasoningEffort("high") == ReasoningEffort.HIGH


class TestVerbosity:
    """Test Verbosity enum."""

    def test_verbosity_values(self) -> None:
        """Test all verbosity enum values."""
        assert Verbosity.LOW == "low"
        assert Verbosity.MEDIUM == "medium"
        assert Verbosity.HIGH == "high"

    def test_verbosity_from_string(self) -> None:
        """Test creating Verbosity from string."""
        assert Verbosity("low") == Verbosity.LOW
        assert Verbosity("medium") == Verbosity.MEDIUM
        assert Verbosity("high") == Verbosity.HIGH


class TestGPT5Config:
    """Test GPT5Config model."""

    def test_default_config(self) -> None:
        """Test GPT5Config with default values."""
        config = GPT5Config()
        assert config.model_name == "gpt-5"
        assert config.reasoning_effort == ReasoningEffort.MEDIUM
        assert config.verbosity == Verbosity.MEDIUM
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_custom_config(self) -> None:
        """Test GPT5Config with custom values."""
        config = GPT5Config(
            model_name="gpt-5-mini",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.LOW,
            max_tokens=8192,
            temperature=0.9,
        )
        assert config.model_name == "gpt-5-mini"
        assert config.reasoning_effort == ReasoningEffort.HIGH
        assert config.verbosity == Verbosity.LOW
        assert config.max_tokens == 8192
        assert config.temperature == 0.9

    def test_config_validation_temperature(self) -> None:
        """Test temperature validation."""
        # Valid temperatures
        GPT5Config(temperature=0.0)
        GPT5Config(temperature=1.0)
        GPT5Config(temperature=0.5)

        # Invalid temperatures should raise ValidationError
        with pytest.raises(ValidationError):
            GPT5Config(temperature=-0.1)
        with pytest.raises(ValidationError):
            GPT5Config(temperature=1.1)

    def test_config_validation_max_tokens(self) -> None:
        """Test max_tokens validation."""
        # Valid max_tokens
        GPT5Config(max_tokens=1)
        GPT5Config(max_tokens=10000)

        # Invalid max_tokens should raise ValidationError
        with pytest.raises(ValidationError):
            GPT5Config(max_tokens=0)
        with pytest.raises(ValidationError):
            GPT5Config(max_tokens=-1)

    def test_config_serialization(self) -> None:
        """Test GPT5Config serialization to dict."""
        config = GPT5Config(
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.LOW,
        )
        data = config.model_dump()

        assert data["model_name"] == "gpt-5"
        assert data["reasoning_effort"] == "high"
        assert data["verbosity"] == "low"
        assert data["max_tokens"] == 4096
        assert data["temperature"] == 0.7

    def test_config_deserialization(self) -> None:
        """Test GPT5Config deserialization from dict."""
        data = {
            "model_name": "gpt-5-nano",
            "reasoning_effort": "minimal",
            "verbosity": "high",
            "max_tokens": 2048,
            "temperature": 0.5,
        }
        config = GPT5Config(**data)

        assert config.model_name == "gpt-5-nano"
        assert config.reasoning_effort == ReasoningEffort.MINIMAL
        assert config.verbosity == Verbosity.HIGH
        assert config.max_tokens == 2048
        assert config.temperature == 0.5

    def test_model_name_options(self) -> None:
        """Test different GPT-5 model name options."""
        # Test all valid model names
        models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
        for model in models:
            config = GPT5Config(model_name=model)
            assert config.model_name == model

    def test_all_reasoning_efforts(self) -> None:
        """Test all reasoning effort levels."""
        efforts = [
            ReasoningEffort.MINIMAL,
            ReasoningEffort.LOW,
            ReasoningEffort.MEDIUM,
            ReasoningEffort.HIGH,
        ]
        for effort in efforts:
            config = GPT5Config(reasoning_effort=effort)
            assert config.reasoning_effort == effort

    def test_all_verbosity_levels(self) -> None:
        """Test all verbosity levels."""
        levels = [Verbosity.LOW, Verbosity.MEDIUM, Verbosity.HIGH]
        for level in levels:
            config = GPT5Config(verbosity=level)
            assert config.verbosity == level
