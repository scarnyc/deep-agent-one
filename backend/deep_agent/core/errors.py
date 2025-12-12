"""Custom exception classes and error handling utilities for Deep Agent AGI.

Provides:
- Custom exception classes (DeepAgentError hierarchy)
- Safe validation error whitelisting
- Structured error responses with error codes
"""
from typing import Any


# Whitelist of safe validation error messages that can be returned to clients.
# These provide actionable information without exposing internal implementation.
# Only messages in this set will be returned; all others get a generic message.
SAFE_VALIDATION_ERRORS: frozenset[str] = frozenset({
    # Message validation
    "Message cannot be empty",
    "Message must not be whitespace only",
    "Value cannot be empty or whitespace-only",
    "Value must be a string",
    # Thread validation
    "Thread ID is required",
    "Thread ID cannot be empty",
    # Generic validation
    "Invalid request format",
    "Required field missing",
})


class ErrorCode:
    """
    Standardized error codes for API responses.

    Provides machine-readable error codes for consistent error handling
    across all API endpoints. Clients can use these codes for programmatic
    error handling and i18n.
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AGENT_EXECUTION_ERROR = "AGENT_EXECUTION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    WEBSOCKET_ERROR = "WEBSOCKET_ERROR"
    JSON_DECODE_ERROR = "JSON_DECODE_ERROR"


def safe_validation_error(error_msg: str) -> str:
    """
    Return error message if whitelisted, otherwise return generic message.

    Balances security (no internal details) with usability (actionable errors).
    Only whitelisted validation messages are returned to clients.

    Args:
        error_msg: The validation error message to check

    Returns:
        Original message if whitelisted, "Validation failed" otherwise

    Examples:
        >>> safe_validation_error("Message cannot be empty")
        'Message cannot be empty'

        >>> safe_validation_error("Internal database constraint violated")
        'Validation failed'
    """
    if error_msg in SAFE_VALIDATION_ERRORS:
        return error_msg
    return "Validation failed"


def build_structured_error(
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a structured error response following a consistent format.

    Provides machine-readable error codes and request IDs for debugging.
    This format is extensible for future fields (e.g., docs_url, retry_after).

    Args:
        code: Error code from ErrorCode class
        message: Human-readable error message
        request_id: Optional request ID for tracking/support
        details: Optional additional details (e.g., field-specific errors)

    Returns:
        Structured error dict: {"error": {"code": "...", "message": "...", ...}}

    Examples:
        >>> build_structured_error(ErrorCode.VALIDATION_ERROR, "Message cannot be empty")
        {'error': {'code': 'VALIDATION_ERROR', 'message': 'Message cannot be empty'}}
    """
    error_obj: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if request_id:
        error_obj["request_id"] = request_id

    if details:
        error_obj["details"] = details

    return {"error": error_obj}


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
