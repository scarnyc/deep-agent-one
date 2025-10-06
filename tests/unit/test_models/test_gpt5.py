"""Tests for GPT-5 Pydantic models."""
import pytest
from pydantic import ValidationError

from backend.deep_agent.models.gpt5 import (
    GPT5Config,
    GPT5Request,
    GPT5Response,
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
        assert Verbosity.STANDARD == "standard"
        assert Verbosity.VERBOSE == "verbose"
        assert Verbosity.CONCISE == "concise"


class TestGPT5Config:
    """Test GPT5Config model."""

    def test_default_config(self) -> None:
        """Test GPT5Config with default values."""
        config = GPT5Config()
        assert config.model_name == "gpt-5"
        assert config.reasoning_effort == ReasoningEffort.MEDIUM
        assert config.verbosity == Verbosity.STANDARD
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.stream is True

    def test_custom_config(self) -> None:
        """Test GPT5Config with custom values."""
        config = GPT5Config(
            model_name="gpt-5-turbo",
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.VERBOSE,
            max_tokens=8192,
            temperature=0.9,
            stream=False,
        )
        assert config.model_name == "gpt-5-turbo"
        assert config.reasoning_effort == ReasoningEffort.HIGH
        assert config.verbosity == Verbosity.VERBOSE
        assert config.max_tokens == 8192
        assert config.temperature == 0.9
        assert config.stream is False

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
            verbosity=Verbosity.CONCISE,
        )
        data = config.model_dump()

        assert data["model_name"] == "gpt-5"
        assert data["reasoning_effort"] == "high"
        assert data["verbosity"] == "concise"
        assert data["max_tokens"] == 4096
        assert data["temperature"] == 0.7
        assert data["stream"] is True

    def test_config_deserialization(self) -> None:
        """Test GPT5Config deserialization from dict."""
        data = {
            "model_name": "gpt-5",
            "reasoning_effort": "low",
            "verbosity": "verbose",
            "max_tokens": 2048,
            "temperature": 0.5,
            "stream": False,
        }
        config = GPT5Config(**data)

        assert config.model_name == "gpt-5"
        assert config.reasoning_effort == ReasoningEffort.LOW
        assert config.verbosity == Verbosity.VERBOSE
        assert config.max_tokens == 2048
        assert config.temperature == 0.5
        assert config.stream is False


class TestGPT5Request:
    """Test GPT5Request model."""

    def test_simple_request(self) -> None:
        """Test simple GPT5Request."""
        request = GPT5Request(
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"
        assert request.messages[0]["content"] == "Hello"
        assert request.config.reasoning_effort == ReasoningEffort.MEDIUM
        assert request.config.stream is True

    def test_request_with_custom_config(self) -> None:
        """Test GPT5Request with custom config."""
        config = GPT5Config(
            reasoning_effort=ReasoningEffort.HIGH,
            temperature=0.9,
        )
        request = GPT5Request(
            messages=[{"role": "user", "content": "Complex question"}],
            config=config,
        )
        assert request.config.reasoning_effort == ReasoningEffort.HIGH
        assert request.config.temperature == 0.9

    def test_request_with_system_message(self) -> None:
        """Test GPT5Request with system and user messages."""
        request = GPT5Request(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2?"},
            ],
        )
        assert len(request.messages) == 2
        assert request.messages[0]["role"] == "system"
        assert request.messages[1]["role"] == "user"

    def test_request_validation_empty_messages(self) -> None:
        """Test that empty messages raises validation error."""
        with pytest.raises(ValidationError):
            GPT5Request(messages=[])


class TestGPT5Response:
    """Test GPT5Response model."""

    def test_simple_response(self) -> None:
        """Test simple GPT5Response."""
        response = GPT5Response(
            content="Hello! How can I help?",
            reasoning_effort=ReasoningEffort.MEDIUM,
            tokens_used=15,
            model="gpt-5",
        )
        assert response.content == "Hello! How can I help?"
        assert response.reasoning_effort == ReasoningEffort.MEDIUM
        assert response.tokens_used == 15
        assert response.model == "gpt-5"
        assert response.finish_reason == "stop"

    def test_response_with_finish_reason(self) -> None:
        """Test GPT5Response with custom finish reason."""
        response = GPT5Response(
            content="Partial response...",
            reasoning_effort=ReasoningEffort.LOW,
            tokens_used=100,
            model="gpt-5",
            finish_reason="length",
        )
        assert response.finish_reason == "length"

    def test_response_serialization(self) -> None:
        """Test GPT5Response serialization."""
        response = GPT5Response(
            content="Test response",
            reasoning_effort=ReasoningEffort.HIGH,
            tokens_used=25,
            model="gpt-5",
        )
        data = response.model_dump()

        assert data["content"] == "Test response"
        assert data["reasoning_effort"] == "high"
        assert data["tokens_used"] == 25
        assert data["model"] == "gpt-5"
        assert data["finish_reason"] == "stop"
