"""
Core utilities and shared functionality for Deep Agent AGI.

This module provides foundational components used throughout the framework:
- Structured logging with JSON output
- Custom exception hierarchy
- Security utilities for sanitizing secrets
- Event serialization for WebSocket streaming
- Common patterns and utilities

Key exports:
    - get_logger: Get structured logger instance
    - DeepAgentError: Base exception class
    - sanitize_error_message: Prevent secret leakage in logs
    - serialize_event: Convert LangChain objects to JSON

Example:
    >>> from deep_agent.core import get_logger, DeepAgentError
    >>> logger = get_logger(__name__)
    >>> logger.info("Agent started", thread_id="123")
    >>> raise DeepAgentError("Something went wrong", context={"step": 1})
"""
