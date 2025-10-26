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

    # Build reasoning parameter for ChatOpenAI
    # LangChain expects: reasoning={"effort": "medium", "summary": "auto"}
    reasoning_param = {
        "effort": config.reasoning_effort.value,
        "summary": "auto",
    }

    # Prepare ChatOpenAI parameters
    llm_params = {
        "model": kwargs.get("model", config.model_name),
        "api_key": api_key,
        "temperature": kwargs.get("temperature", config.temperature),
        "max_tokens": kwargs.get("max_tokens", config.max_tokens),
        "reasoning": reasoning_param,
        "verbosity": config.verbosity.value,
    }

    # Add any additional kwargs (allows overriding config values)
    for key, value in kwargs.items():
        if key not in llm_params:
            llm_params[key] = value

    logger.info(
        "Creating GPT-5 LLM",
        model=llm_params["model"],
        reasoning_effort=config.reasoning_effort.value,
        verbosity=config.verbosity.value,
        temperature=llm_params["temperature"],
        max_tokens=llm_params["max_tokens"],
    )

    return ChatOpenAI(**llm_params)
