"""
LangSmith integration for agent tracing and observability.

Provides configuration and setup for LangSmith tracing of agent operations,
LLM calls, tool invocations, and error states. LangChain/LangGraph automatically
send traces to LangSmith when environment variables are configured.
"""

import os

from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.logging import get_logger
from deep_agent.core.security import mask_api_key

logger = get_logger(__name__)


def setup_langsmith(settings: Settings | None = None) -> None:
    """
    Configure LangSmith tracing for agent observability.

    Sets environment variables required for LangChain/LangGraph automatic tracing.
    Once configured, all agent operations, LLM calls, and tool invocations are
    automatically traced to LangSmith without manual instrumentation.

    Args:
        settings: Configuration settings. If None, uses get_settings().

    Raises:
        ValueError: If LANGSMITH_API_KEY is missing or empty. Note that this
            only validates the key exists - authentication with LangSmith API
            is verified when actual tracing occurs (lazy validation).

    Example:
        >>> from deep_agent.integrations.langsmith import setup_langsmith
        >>> setup_langsmith()  # Uses settings from environment
        >>> # All subsequent LangChain/LangGraph operations will be traced

    Environment Variables Set:
        - LANGSMITH_API_KEY: Authentication for LangSmith API
        - LANGSMITH_PROJECT: Project name for organizing traces
        - LANGSMITH_ENDPOINT: API endpoint (default: api.smith.langchain.com)
        - LANGSMITH_TRACING_V2: Enable/disable tracing (true/false)

    What Gets Traced (Automatic):
        - Agent execution (state changes, decisions, HITL)
        - LLM calls (prompts, completions, tokens, reasoning effort)
        - Tool invocations (name, arguments, results, errors)
        - Performance metrics (latency, token usage)
        - Error states and stack traces

    Note:
        - LangSmith SDK must be installed (langsmith>=0.4.0)
        - Tracing is automatic - no manual instrumentation needed
        - API key is masked in logs for security
        - Safe to call multiple times (idempotent)
    """
    # Get settings
    if settings is None:
        settings = get_settings()

    # Validate API key
    api_key = settings.LANGSMITH_API_KEY
    if not api_key or not api_key.strip():
        logger.error("LangSmith API key is missing or empty")
        raise ValueError(
            "LangSmith API key is required for tracing. "
            "Set LANGSMITH_API_KEY in environment or .env file."
        )

    api_key = api_key.strip()

    # Mask API key for logging (using shared security utility)
    masked_key = mask_api_key(api_key)

    # Set environment variables for automatic tracing
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_TRACING_V2"] = str(settings.LANGSMITH_TRACING_V2).lower()

    logger.info(
        "LangSmith tracing configured",
        project=settings.LANGSMITH_PROJECT,
        endpoint=settings.LANGSMITH_ENDPOINT,
        tracing_enabled=settings.LANGSMITH_TRACING_V2,
        api_key_masked=masked_key,
    )

    # Log warning if API key format seems unusual (but don't block)
    if not api_key.startswith("lsv2_") and not api_key.startswith("ls__"):
        logger.warning(
            "LangSmith API key format may be invalid",
            expected_prefix="lsv2_ or ls__",
            actual_prefix=api_key[:5] if len(api_key) >= 5 else api_key,
        )

    logger.debug(
        "LangSmith environment variables set",
        env_vars_configured=[
            "LANGSMITH_API_KEY",
            "LANGSMITH_PROJECT",
            "LANGSMITH_ENDPOINT",
            "LANGSMITH_TRACING_V2",
        ],
    )
