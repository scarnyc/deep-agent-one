"""Custom exception classes for Deep Agent AGI."""
from typing import Any


class DeepAgentError(Exception):
    """Base exception class for all Deep Agent errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """
        Initialize exception with message and optional context.

        Args:
            message: Error message
            **kwargs: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.context = kwargs

    def __str__(self) -> str:
        """Return string representation of error."""
        return self.message


class ConfigurationError(DeepAgentError):
    """Raised when there's a configuration error."""

    pass


class LLMError(DeepAgentError):
    """Raised when there's an LLM-related error (API, rate limits, etc.)."""

    pass


class ToolError(DeepAgentError):
    """Raised when a tool execution fails."""

    pass


class MCPError(DeepAgentError):
    """Raised when there's an MCP server connection or execution error."""

    pass


class AuthenticationError(DeepAgentError):
    """Raised when authentication fails."""

    pass


class DatabaseError(DeepAgentError):
    """Raised when there's a database operation error."""

    pass
