"""Security utilities for Deep Agent AGI.

Provides error message sanitization to prevent secret leakage in logs
and API responses.
"""

from typing import NamedTuple

# Secret patterns to detect in error messages and logs
SECRET_PATTERNS: list[str] = [
    "sk-",  # OpenAI API keys
    "lsv2_",  # LangSmith tokens
    "ls__",  # LangSmith legacy tokens
    "key=",  # Generic key parameters
    "token=",  # Generic token parameters
    "password=",  # Passwords
    "api_key=",  # API key parameters
    "secret=",  # Secret parameters
]


class SanitizationResult(NamedTuple):
    """Result of error message sanitization with metadata for enhanced logging."""

    message: str
    was_sanitized: bool
    original_error_type: str | None


def sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages to prevent secret leakage in logs.

    Checks if error message contains common secret patterns and redacts
    the entire message if found. Used to prevent accidental logging of
    API keys, tokens, or passwords in error messages.

    Args:
        error_msg: The error message to sanitize

    Returns:
        Original message if safe, redacted message if patterns found

    Examples:
        >>> sanitize_error_message("Connection failed")
        'Connection failed'

        >>> sanitize_error_message("Invalid API key: sk-1234567890")
        '[REDACTED: Potential secret in error message]'

        >>> sanitize_error_message("Auth failed with token=abc123")
        '[REDACTED: Potential secret in error message]'
    """
    if any(pattern in error_msg for pattern in SECRET_PATTERNS):
        return "[REDACTED: Potential secret in error message]"
    return error_msg


def mask_api_key(api_key: str, prefix_len: int = 8, suffix_len: int = 4) -> str:
    """
    Mask an API key for safe logging.

    Shows prefix and suffix of key, masks the middle. Handles edge cases
    for short keys to avoid exposing too much information.

    Args:
        api_key: The API key to mask
        prefix_len: Number of characters to show at start (default: 8)
        suffix_len: Number of characters to show at end (default: 4)

    Returns:
        Masked API key string (e.g., "sk-abc12...xyz9" or "***" for short keys)

    Examples:
        >>> mask_api_key("sk-proj-1234567890abcdefghij")
        'sk-proj-1...ghij'

        >>> mask_api_key("short")
        '***'

        >>> mask_api_key("lsv2_abcdefghijklmnop")
        'lsv2_abc...mnop'
    """
    api_key_len = len(api_key)

    # For keys longer than prefix_len + suffix_len, show prefix...suffix
    if api_key_len > prefix_len + suffix_len:
        return f"{api_key[:prefix_len]}...{api_key[-suffix_len:]}"

    # For keys longer than just prefix_len, show partial prefix with masking
    elif api_key_len > prefix_len:
        return f"{api_key[:prefix_len//2]}...***"

    # For very short keys, mask completely
    else:
        return "***"


def sanitize_error_with_metadata(
    error_msg: str,
    error: Exception | None = None,
) -> SanitizationResult:
    """
    Sanitize error message and return metadata about the sanitization.

    Provides enhanced logging capabilities by tracking whether sanitization
    was applied and preserving the original error type for debugging.

    Args:
        error_msg: The error message to sanitize
        error: Optional exception object to extract type from

    Returns:
        SanitizationResult with:
        - message: Sanitized error message
        - was_sanitized: True if message contained secret patterns
        - original_error_type: Type name of the exception (e.g., "ValueError")

    Examples:
        >>> result = sanitize_error_with_metadata("Connection failed")
        >>> result.was_sanitized
        False
        >>> result.message
        'Connection failed'

        >>> result = sanitize_error_with_metadata("API key: sk-1234", ValueError("test"))
        >>> result.was_sanitized
        True
        >>> result.original_error_type
        'ValueError'
    """
    was_sanitized = any(pattern in error_msg for pattern in SECRET_PATTERNS)
    sanitized_msg = "[REDACTED: Potential secret in error message]" if was_sanitized else error_msg

    error_type = type(error).__name__ if error else None

    return SanitizationResult(
        message=sanitized_msg,
        was_sanitized=was_sanitized,
        original_error_type=error_type,
    )
