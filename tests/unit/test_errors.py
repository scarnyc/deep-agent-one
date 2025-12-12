"""
Unit tests for error handling.

Tests the custom exception hierarchy for Deep Agent AGI, ensuring proper
inheritance, error message handling, and raise/catch behavior for all
exception types. Also tests error handling utilities for safe validation
errors and structured error responses.
"""
import pytest

from backend.deep_agent.core.errors import (
    DeepAgentError,
    ConfigurationError,
    LLMError,
    ToolError,
    MCPError,
    AuthenticationError,
    DatabaseError,
    ErrorCode,
    SAFE_VALIDATION_ERRORS,
    safe_validation_error,
    build_structured_error,
)


class TestCustomExceptions:
    """Test custom exception classes and inheritance chain."""

    def test_deep_agent_error_base_class(self) -> None:
        """
        Test base DeepAgentError exception.

        Scenario:
            Create DeepAgentError with message

        Expected:
            Error message matches input, inherits from Exception
        """
        error = DeepAgentError("Test error")

        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_configuration_error(self) -> None:
        """Test ConfigurationError for configuration issues."""
        error = ConfigurationError("Invalid config")

        assert str(error) == "Invalid config"
        assert isinstance(error, DeepAgentError)

    def test_llm_error(self) -> None:
        """Test LLMError for LLM-related issues."""
        error = LLMError("API rate limit exceeded")

        assert str(error) == "API rate limit exceeded"
        assert isinstance(error, DeepAgentError)

    def test_tool_error(self) -> None:
        """Test ToolError for tool execution failures."""
        error = ToolError("Tool execution failed")

        assert str(error) == "Tool execution failed"
        assert isinstance(error, DeepAgentError)

    def test_mcp_error(self) -> None:
        """Test MCPError for MCP server issues."""
        error = MCPError("MCP server connection failed")

        assert str(error) == "MCP server connection failed"
        assert isinstance(error, DeepAgentError)

    def test_authentication_error(self) -> None:
        """Test AuthenticationError for auth issues."""
        error = AuthenticationError("Invalid API key")

        assert str(error) == "Invalid API key"
        assert isinstance(error, DeepAgentError)

    def test_database_error(self) -> None:
        """Test DatabaseError for database issues."""
        error = DatabaseError("Connection pool exhausted")

        assert str(error) == "Connection pool exhausted"
        assert isinstance(error, DeepAgentError)

    def test_error_with_context(self) -> None:
        """Test that errors can include context information."""
        error = LLMError("Token limit exceeded", model="gpt-5", tokens=8000)

        assert "Token limit exceeded" in str(error)
        # Verify error can be raised and caught
        with pytest.raises(LLMError):
            raise error

    def test_error_inheritance_chain(self) -> None:
        """Test that all custom errors inherit from DeepAgentError."""
        errors = [
            ConfigurationError("test"),
            LLMError("test"),
            ToolError("test"),
            MCPError("test"),
            AuthenticationError("test"),
            DatabaseError("test"),
        ]

        for error in errors:
            assert isinstance(error, DeepAgentError)
            assert isinstance(error, Exception)

    def test_raise_and_catch_custom_error(self) -> None:
        """Test raising and catching custom errors."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Missing required setting")

        assert "Missing required setting" in str(exc_info.value)

    def test_error_can_be_caught_as_base_class(self) -> None:
        """Test that specific errors can be caught as DeepAgentError."""
        with pytest.raises(DeepAgentError):
            raise LLMError("Test error")


class TestSafeValidationError:
    """Test safe validation error whitelist functionality."""

    def test_whitelisted_message_returned_unchanged(self) -> None:
        """Test that whitelisted messages are returned unchanged."""
        for msg in SAFE_VALIDATION_ERRORS:
            assert safe_validation_error(msg) == msg

    def test_non_whitelisted_message_returns_generic(self) -> None:
        """Test that non-whitelisted messages return generic error."""
        non_whitelisted = [
            "Internal database constraint violated",
            "SQL syntax error at line 42",
            "KeyError: 'secret_key'",
            "File not found: /etc/passwd",
        ]
        for msg in non_whitelisted:
            assert safe_validation_error(msg) == "Validation failed"

    def test_empty_string_returns_generic(self) -> None:
        """Test that empty string returns generic error."""
        assert safe_validation_error("") == "Validation failed"

    def test_common_validation_messages_whitelisted(self) -> None:
        """Test that common validation messages are whitelisted."""
        common_messages = [
            "Message cannot be empty",
            "Value cannot be empty or whitespace-only",
            "Value must be a string",
            "Thread ID is required",
        ]
        for msg in common_messages:
            assert safe_validation_error(msg) == msg


class TestBuildStructuredError:
    """Test structured error response builder."""

    def test_basic_error_structure(self) -> None:
        """Test basic error structure with code and message."""
        result = build_structured_error(
            ErrorCode.VALIDATION_ERROR,
            "Test message",
        )
        assert result == {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Test message",
            }
        }

    def test_error_with_request_id(self) -> None:
        """Test error structure includes request_id when provided."""
        result = build_structured_error(
            ErrorCode.AGENT_EXECUTION_ERROR,
            "Agent failed",
            request_id="req-123-abc",
        )
        assert result["error"]["code"] == "AGENT_EXECUTION_ERROR"
        assert result["error"]["message"] == "Agent failed"
        assert result["error"]["request_id"] == "req-123-abc"

    def test_error_with_details(self) -> None:
        """Test error structure includes details when provided."""
        details = {"field": "email", "reason": "Invalid format"}
        result = build_structured_error(
            ErrorCode.VALIDATION_ERROR,
            "Validation failed",
            details=details,
        )
        assert result["error"]["details"] == details

    def test_error_with_all_fields(self) -> None:
        """Test error structure with all optional fields."""
        result = build_structured_error(
            ErrorCode.INTERNAL_ERROR,
            "Something went wrong",
            request_id="req-xyz",
            details={"retry_after": 30},
        )
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert result["error"]["message"] == "Something went wrong"
        assert result["error"]["request_id"] == "req-xyz"
        assert result["error"]["details"] == {"retry_after": 30}


class TestErrorCode:
    """Test ErrorCode constants."""

    def test_all_error_codes_are_strings(self) -> None:
        """Test that all error codes are string constants."""
        error_codes = [
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.AGENT_EXECUTION_ERROR,
            ErrorCode.INTERNAL_ERROR,
            ErrorCode.RATE_LIMIT_ERROR,
            ErrorCode.AUTHENTICATION_ERROR,
            ErrorCode.AUTHORIZATION_ERROR,
            ErrorCode.NOT_FOUND_ERROR,
            ErrorCode.TIMEOUT_ERROR,
            ErrorCode.WEBSOCKET_ERROR,
            ErrorCode.JSON_DECODE_ERROR,
        ]
        for code in error_codes:
            assert isinstance(code, str)
            assert code.isupper()  # All codes should be uppercase
            assert "_" in code or code.isalpha()  # Valid constant naming
