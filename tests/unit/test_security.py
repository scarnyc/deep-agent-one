"""
Unit tests for security utilities.

Tests error message sanitization functions to prevent secret leakage
in logs and API responses.
"""

from backend.deep_agent.core.security import (
    SECRET_PATTERNS,
    SanitizationResult,
    mask_api_key,
    sanitize_error_message,
    sanitize_error_with_metadata,
)


class TestSanitizeErrorMessage:
    """Test error message sanitization."""

    def test_safe_message_unchanged(self) -> None:
        """Test that safe messages are returned unchanged."""
        safe_messages = [
            "Connection failed",
            "Invalid request format",
            "User not found",
            "Timeout exceeded",
        ]
        for msg in safe_messages:
            assert sanitize_error_message(msg) == msg

    def test_message_with_openai_key_redacted(self) -> None:
        """Test that OpenAI API keys are redacted."""
        msg = "Invalid API key: sk-1234567890abcdef"
        assert sanitize_error_message(msg) == "[REDACTED: Potential secret in error message]"

    def test_message_with_langsmith_token_redacted(self) -> None:
        """Test that LangSmith tokens are redacted."""
        msg = "Auth failed with token lsv2_pt_abc123xyz"
        assert sanitize_error_message(msg) == "[REDACTED: Potential secret in error message]"

    def test_message_with_password_parameter_redacted(self) -> None:
        """Test that password parameters are redacted."""
        msg = "Connection string: password=secret123"
        assert sanitize_error_message(msg) == "[REDACTED: Potential secret in error message]"

    def test_message_with_token_parameter_redacted(self) -> None:
        """Test that token parameters are redacted."""
        msg = "Request failed: token=abc123"
        assert sanitize_error_message(msg) == "[REDACTED: Potential secret in error message]"

    def test_all_secret_patterns_detected(self) -> None:
        """Test that all configured secret patterns are detected."""
        for pattern in SECRET_PATTERNS:
            msg = f"Error message containing {pattern}some_value"
            assert sanitize_error_message(msg) == "[REDACTED: Potential secret in error message]"


class TestSanitizeErrorWithMetadata:
    """Test error message sanitization with metadata."""

    def test_safe_message_returns_false_sanitized(self) -> None:
        """Test that safe messages return was_sanitized=False."""
        result = sanitize_error_with_metadata("Connection failed")
        assert isinstance(result, SanitizationResult)
        assert result.message == "Connection failed"
        assert result.was_sanitized is False
        assert result.original_error_type is None

    def test_unsafe_message_returns_true_sanitized(self) -> None:
        """Test that unsafe messages return was_sanitized=True."""
        result = sanitize_error_with_metadata("API key: sk-1234567890")
        assert result.message == "[REDACTED: Potential secret in error message]"
        assert result.was_sanitized is True

    def test_error_type_captured(self) -> None:
        """Test that error type is captured from exception."""
        error = ValueError("test error")
        result = sanitize_error_with_metadata("Some error", error)
        assert result.original_error_type == "ValueError"

    def test_various_error_types(self) -> None:
        """Test that various error types are captured correctly."""
        errors = [
            (TypeError("type error"), "TypeError"),
            (KeyError("key error"), "KeyError"),
            (AttributeError("attr error"), "AttributeError"),
            (RuntimeError("runtime error"), "RuntimeError"),
        ]
        for error, expected_type in errors:
            result = sanitize_error_with_metadata("test", error)
            assert result.original_error_type == expected_type

    def test_none_error_returns_none_type(self) -> None:
        """Test that None error returns None for type."""
        result = sanitize_error_with_metadata("test message", None)
        assert result.original_error_type is None

    def test_named_tuple_unpacking(self) -> None:
        """Test that SanitizationResult can be unpacked."""
        result = sanitize_error_with_metadata("test", ValueError("x"))
        msg, sanitized, error_type = result
        assert msg == "test"
        assert sanitized is False
        assert error_type == "ValueError"


class TestMaskApiKey:
    """Test API key masking."""

    def test_long_key_shows_prefix_suffix(self) -> None:
        """Test that long keys show prefix and suffix."""
        key = "sk-proj-1234567890abcdefghijklmnop"
        result = mask_api_key(key)
        assert result.startswith("sk-proj-")
        assert "..." in result
        assert result.endswith("mnop")

    def test_short_key_fully_masked(self) -> None:
        """Test that very short keys are fully masked."""
        key = "short"
        result = mask_api_key(key)
        assert result == "***"

    def test_medium_key_partial_mask(self) -> None:
        """Test that medium-length keys are partially masked."""
        key = "abcdefghij"  # 10 chars, > 8 but <= 12
        result = mask_api_key(key)
        assert "..." in result
        assert "***" in result

    def test_custom_prefix_suffix_lengths(self) -> None:
        """Test custom prefix and suffix lengths."""
        key = "abcdefghijklmnopqrstuvwxyz"  # 26 chars
        result = mask_api_key(key, prefix_len=4, suffix_len=2)
        assert result.startswith("abcd")
        assert result.endswith("yz")
        assert "..." in result
