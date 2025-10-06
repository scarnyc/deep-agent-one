"""Unit tests for error handling."""
import pytest

from backend.deep_agent.core.errors import (
    DeepAgentError,
    ConfigurationError,
    LLMError,
    ToolError,
    MCPError,
    AuthenticationError,
    DatabaseError,
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_deep_agent_error_base_class(self) -> None:
        """Test base DeepAgentError exception."""
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
