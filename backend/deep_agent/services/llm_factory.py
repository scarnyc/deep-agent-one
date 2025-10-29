"""Factory for creating LangChain LLM instances configured for GPT-5."""
from typing import Any

from langchain_openai import ChatOpenAI

from backend.deep_agent.core.logging import get_logger
from backend.deep_agent.models.gpt5 import GPT5Config

logger = get_logger(__name__)


def create_gpt5_llm(
    api_key: str,
    config: GPT5Config | None = None,
    **kwargs: Any,
) -> ChatOpenAI:
    """
    Create a configured ChatOpenAI instance for GPT-5.

    This factory function creates LangChain-compatible ChatOpenAI instances
    configured for GPT-5 with reasoning effort and verbosity settings.

    Args:
        api_key: OpenAI API key
        config: GPT5Config with model settings (uses defaults if None)
        **kwargs: Additional arguments to pass to ChatOpenAI (override config)

    Returns:
        Configured ChatOpenAI instance ready for use with DeepAgents

    Raises:
        ValueError: If API key is empty

    Example:
        >>> from backend.deep_agent.models.gpt5 import GPT5Config, ReasoningEffort
        >>> config = GPT5Config(reasoning_effort=ReasoningEffort.HIGH)
        >>> llm = create_gpt5_llm(api_key="sk-...", config=config)
        >>> # Use with DeepAgents:
        >>> agent = create_deep_agent(model=llm, tools=[...])
    """
    if not api_key:
        raise ValueError("API key is required")

    # Issue 7 fix: Validate API key format
    if not api_key.startswith("sk-"):
        logger.warning(
            "API key format may be invalid",
            expected_prefix="sk-",
            actual_prefix=api_key[:5] if len(api_key) >= 5 else api_key,
        )

    # Use default config if none provided
    if config is None:
        config = GPT5Config()

    # Prepare ChatOpenAI parameters
    # GPT-5 uses reasoning_effort parameter and max_completion_tokens (not max_tokens)
    # GPT-5 only supports temperature=1.0 - must explicitly set to override ChatOpenAI's default of 0.7
    llm_params = {
        "model": kwargs.get("model", config.model_name),
        "api_key": api_key,
        "max_completion_tokens": kwargs.get("max_completion_tokens", config.max_tokens),
        "reasoning_effort": config.reasoning_effort.value,
        "temperature": 1.0,  # GPT-5 requirement: must be 1.0 (overrides ChatOpenAI's default 0.7)
        "streaming": True,  # Enable streaming for real-time responses
    }

    # Add any additional kwargs (allows overriding config values)
    for key, value in kwargs.items():
        if key not in llm_params:
            llm_params[key] = value

    logger.info(
        "Creating GPT-5 LLM",
        model=llm_params["model"],
        reasoning_effort=config.reasoning_effort.value,
        max_completion_tokens=llm_params["max_completion_tokens"],
    )

    return ChatOpenAI(**llm_params)
