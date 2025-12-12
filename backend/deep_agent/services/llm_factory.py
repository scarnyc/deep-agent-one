"""Factory for creating LangChain LLM instances for multiple providers.

Supports:
    - Gemini 3 Pro (primary model via ChatGoogleGenerativeAI)
    - GPT-5.1 (fallback model via ChatOpenAI)

IMPORTANT: Uses lazy imports for langchain_google_genai to prevent
import-time blocking issues with gRPC/protobuf compilation.

PERFORMANCE OPTIMIZATION:
    - gRPC/protobuf compilation in langchain_google_genai blocks for 8-12 seconds
    - This module provides async versions that run imports in thread pool
    - Pre-warming functions allow background initialization at server startup
"""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from httpx import Timeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from deep_agent.core.logging import get_logger
from deep_agent.models.llm import THINKING_LEVEL_TO_BUDGET, GeminiConfig, GPTConfig

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Thread pool for background initialization (prevents blocking event loop)
_init_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="llm-init")

# Cache for pre-warmed imports (None = not started, class = completed)
_gemini_class_cache: Any = None
_openai_class_cache: tuple[Any, Any] | None = None
_prewarm_started = False


def _lazy_import_openai():
    """
    Lazy import of langchain_openai and openai to avoid blocking at module load time.

    Returns:
        Tuple of (ChatOpenAI, AsyncOpenAI) classes
    """
    global _openai_class_cache

    # Return cached if available
    if _openai_class_cache is not None:
        return _openai_class_cache

    try:
        from langchain_openai import ChatOpenAI
        from openai import AsyncOpenAI

        _openai_class_cache = (ChatOpenAI, AsyncOpenAI)
        return _openai_class_cache
    except ImportError as e:
        logger.error("Failed to import langchain_openai/openai", error=str(e))
        raise


def _lazy_import_google_genai():
    """
    Lazy import of langchain_google_genai to avoid blocking at module load time.

    The langchain_google_genai import can block during initialization due to:
    - gRPC/protobuf compilation (8-12 seconds)
    - SSL certificate validation
    - Network initialization

    Returns:
        ChatGoogleGenerativeAI class
    """
    global _gemini_class_cache

    # Return cached if available
    if _gemini_class_cache is not None:
        return _gemini_class_cache

    try:
        logger.debug("Starting Gemini import (may take 8-12 seconds for gRPC compilation)")
        from langchain_google_genai import ChatGoogleGenerativeAI

        _gemini_class_cache = ChatGoogleGenerativeAI
        logger.debug("Gemini import completed")
        return _gemini_class_cache
    except ImportError as e:
        error_msg = f"Failed to import langchain_google_genai: {str(e)}"
        # Defensive logging - use stderr if logger might not be configured
        try:
            logger.error("Failed to import langchain_google_genai", error=str(e))
        except Exception:
            print(f"ERROR: {error_msg}", file=sys.stderr)
        # Also print to stderr as a safety net during startup
        print(f"ERROR: {error_msg}", file=sys.stderr)
        print("HINT: Install with: pip install langchain-google-genai", file=sys.stderr)
        raise


async def async_import_google_genai(timeout_seconds: float = 30.0) -> Any:
    """
    Async import of langchain_google_genai using thread pool.

    Runs the blocking gRPC/protobuf compilation in a thread pool to avoid
    blocking the async event loop during first request.

    Args:
        timeout_seconds: Maximum time to wait for import (default 30s)

    Returns:
        ChatGoogleGenerativeAI class

    Raises:
        asyncio.TimeoutError: If import takes longer than timeout
        ImportError: If module cannot be imported
    """
    global _gemini_class_cache

    # Return cached immediately if available
    if _gemini_class_cache is not None:
        return _gemini_class_cache

    logger.info("Starting async Gemini import (thread pool)")

    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(_init_executor, _lazy_import_google_genai),
            timeout=timeout_seconds,
        )
        logger.info("Async Gemini import completed")
        return result
    except TimeoutError:
        logger.error(
            "Gemini import timed out",
            timeout_seconds=timeout_seconds,
        )
        raise RuntimeError(f"Gemini initialization timed out after {timeout_seconds}s")


async def async_import_openai(timeout_seconds: float = 15.0) -> tuple[Any, Any]:
    """
    Async import of langchain_openai using thread pool.

    Args:
        timeout_seconds: Maximum time to wait for import (default 15s)

    Returns:
        Tuple of (ChatOpenAI, AsyncOpenAI) classes
    """
    global _openai_class_cache

    # Return cached immediately if available
    if _openai_class_cache is not None:
        return _openai_class_cache

    logger.info("Starting async OpenAI import (thread pool)")

    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(_init_executor, _lazy_import_openai),
            timeout=timeout_seconds,
        )
        logger.info("Async OpenAI import completed")
        return result
    except TimeoutError:
        logger.error("OpenAI import timed out", timeout_seconds=timeout_seconds)
        raise RuntimeError(f"OpenAI initialization timed out after {timeout_seconds}s")


async def prewarm_llm_imports() -> None:
    """
    Pre-warm LLM imports in background during server startup.

    Call this from lifespan handler to start gRPC compilation immediately
    rather than waiting for first request. This reduces first-request latency
    from 8-12 seconds to near-instant (if pre-warming completes first).

    This function is fire-and-forget safe - errors are logged but not raised.
    """
    global _prewarm_started

    if _prewarm_started:
        logger.debug("LLM pre-warming already started, skipping")
        return

    _prewarm_started = True
    logger.info("Pre-warming LLM imports in background (non-blocking)")

    try:
        # Run both imports concurrently in thread pool
        results = await asyncio.gather(
            async_import_google_genai(timeout_seconds=60.0),  # Longer timeout for cold start
            async_import_openai(timeout_seconds=30.0),
            return_exceptions=True,  # Don't fail if one import fails
        )

        # Check results and log specific errors (don't silently swallow them)
        import_names = ["Gemini", "OpenAI"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"{import_names[i]} import failed: {result}"
                logger.error(
                    f"{import_names[i]} pre-warming failed",
                    error=str(result),
                    error_type=type(result).__name__,
                )
                # Also print to stderr for visibility during startup
                print(f"ERROR: {error_msg}", file=sys.stderr)
            else:
                logger.info(f"{import_names[i]} pre-warming completed")

        logger.info("LLM pre-warming process completed")
    except Exception as e:
        # Log but don't raise - pre-warming is best-effort
        error_msg = f"LLM pre-warming failed (will retry on first request): {str(e)}"
        logger.warning(
            "LLM pre-warming failed (will retry on first request)",
            error=str(e),
            error_type=type(e).__name__,
        )
        print(f"WARNING: {error_msg}", file=sys.stderr)


def is_prewarm_complete() -> bool:
    """Check if pre-warming has completed (both caches populated)."""
    return _gemini_class_cache is not None and _openai_class_cache is not None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
)
def create_gemini_llm(
    api_key: str,
    config: GeminiConfig | None = None,
    **kwargs: Any,
) -> Any:  # Returns ChatGoogleGenerativeAI but using Any to avoid import
    """
    Create a configured ChatGoogleGenerativeAI instance for Gemini 3 Pro (primary model).

    This factory function creates LangChain-compatible ChatGoogleGenerativeAI instances
    configured for Gemini 3 Pro with thinking level and temperature settings.

    Uses lazy import to prevent blocking during module initialization.

    Args:
        api_key: Google API key
        config: GeminiConfig with model settings (uses defaults if None)
        **kwargs: Additional arguments to pass to ChatGoogleGenerativeAI

    Returns:
        Configured ChatGoogleGenerativeAI instance ready for use with DeepAgents

    Raises:
        ValueError: If API key is empty
        ImportError: If langchain_google_genai cannot be imported

    Example:
        >>> from deep_agent.models.llm import GeminiConfig, ThinkingLevel
        >>> config = GeminiConfig(thinking_level=ThinkingLevel.HIGH)
        >>> llm = create_gemini_llm(api_key="...", config=config)
        >>> # Use with DeepAgents:
        >>> agent = create_deep_agent(model=llm, tools=[...])
    """
    if not api_key:
        raise ValueError("Google API key is required")

    # Use default config if none provided
    if config is None:
        config = GeminiConfig()

    # Map thinking_level to thinking_budget tokens
    # This is required because google-ai-generativelanguage v0.9.0 ThinkingConfig
    # only supports `thinking_budget` (token count), not `thinking_level` (string)
    thinking_level_str = kwargs.get("thinking_level", config.thinking_level.value)
    thinking_budget = THINKING_LEVEL_TO_BUDGET.get(thinking_level_str, 8192)  # Default to high

    logger.info(
        "Creating Gemini LLM (primary model) with lazy import",
        model=config.model_name,
        temperature=config.temperature,
        thinking_level=thinking_level_str,
        thinking_budget=thinking_budget,
        max_output_tokens=config.max_output_tokens,
    )

    # Lazy import to avoid blocking at module load time
    ChatGoogleGenerativeAI = _lazy_import_google_genai()

    return ChatGoogleGenerativeAI(
        model=kwargs.get("model", config.model_name),
        google_api_key=api_key,
        temperature=kwargs.get("temperature", config.temperature),
        thinking_budget=thinking_budget,  # Use token budget instead of level string
        max_output_tokens=kwargs.get("max_output_tokens", config.max_output_tokens),
        streaming=config.streaming,
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "model",
                "temperature",
                "max_output_tokens",
                "thinking_level",
                "thinking_budget",
            ]
        },
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
)
def create_gpt_llm(
    api_key: str,
    config: GPTConfig | None = None,
    **kwargs: Any,
) -> Any:  # Returns ChatOpenAI but using Any to avoid import
    """
    Create a configured ChatOpenAI instance for GPT-5.1 (fallback model).

    This factory function creates LangChain-compatible ChatOpenAI instances
    configured for GPT models with reasoning effort and verbosity settings.

    Args:
        api_key: OpenAI API key
        config: GPTConfig with model settings (uses defaults if None)
        **kwargs: Additional arguments to pass to ChatOpenAI (override config)

    Returns:
        Configured ChatOpenAI instance ready for use with DeepAgents

    Raises:
        ValueError: If API key is empty

    Example:
        >>> from deep_agent.models.llm import GPTConfig, ReasoningEffort
        >>> config = GPTConfig(reasoning_effort=ReasoningEffort.HIGH)
        >>> llm = create_gpt_llm(api_key="sk-...", config=config)
        >>> # Use with DeepAgents (fallback):
        >>> middleware = [ModelFallbackMiddleware(llm)]
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
        config = GPTConfig()

    # Lazy import to avoid blocking at module load time
    ChatOpenAI, AsyncOpenAI = _lazy_import_openai()

    # Create custom AsyncOpenAI client with extended timeouts
    # Default timeout is 60s which causes BrokenResourceError at 45s
    # Increase to 120s to handle long-running parallel tool executions
    http_client = AsyncOpenAI(
        api_key=api_key,
        timeout=Timeout(
            connect=10.0,  # Connection timeout
            read=120.0,  # Read timeout (increased from default 60s)
            write=10.0,  # Write timeout
            pool=10.0,  # Pool timeout
        ),
        max_retries=2,  # Built-in retry for transient failures
    )

    # Prepare ChatOpenAI parameters
    # GPT models use reasoning_effort parameter and max_completion_tokens (not max_tokens)
    # Note: temperature parameter deprecated for GPT-5+ reasoning models
    llm_params = {
        "model": kwargs.get("model", config.model_name),
        "client": http_client,  # Use custom client with extended timeouts
        "api_key": api_key,
        "max_completion_tokens": kwargs.get("max_completion_tokens", config.max_tokens),
        "reasoning_effort": config.reasoning_effort.value,
        "streaming": True,  # Enable streaming for real-time responses
        "request_timeout": 120,  # Request-level timeout (matches read timeout)
    }

    # Add any additional kwargs (allows overriding config values)
    for key, value in kwargs.items():
        if key not in llm_params:
            llm_params[key] = value

    logger.info(
        "Creating GPT LLM (fallback model) with extended timeout configuration",
        model=llm_params["model"],
        reasoning_effort=config.reasoning_effort.value,
        max_completion_tokens=llm_params["max_completion_tokens"],
        read_timeout=120,
        request_timeout=120,
    )

    return ChatOpenAI(**llm_params)
