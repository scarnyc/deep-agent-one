"""
External Service Integrations.

This module provides integrations with external services including:
- LangSmith: Agent tracing and observability
- Opik: Prompt optimization and A/B testing (Phase 1)
- MCP Clients: Model Context Protocol servers (Perplexity search)

The module implements lazy loading for optional Phase 1 dependencies
(Opik) to prevent blocking Phase 0 startup when packages are not installed.

Typical usage:
    >>> from deep_agent.integrations import setup_langsmith
    >>> setup_langsmith()  # Enable LangSmith tracing
    >>>
    >>> # Lazy loading - only loads when accessed
    >>> from deep_agent.integrations import OpikClient
    >>> client = OpikClient()

Lazy Loading Pattern:
    Phase 1 dependencies are loaded lazily via __getattr__ to allow
    Phase 0 to run without installing optional packages. This prevents
    ImportError crashes during startup.

    Immediate imports:
        - setup_langsmith (Phase 0 required)

    Lazy imports:
        - OpikClient (Phase 1 optional)
        - OptimizerAlgorithm (Phase 1 optional)
        - ALGORITHM_SELECTION_GUIDE (Phase 1 optional)
        - get_opik_client (Phase 1 optional)
"""

from deep_agent.integrations.langsmith import setup_langsmith

__all__ = [
    "setup_langsmith",
    "OpikClient",
    "OptimizerAlgorithm",
    "ALGORITHM_SELECTION_GUIDE",
    "get_opik_client",
]


def __getattr__(name):
    """
    Lazy import for optional Phase 1 dependencies.

    This prevents Opik-related imports from blocking Phase 0 startup
    when opik/opik-optimizer packages are not installed. The imports
    only trigger when these features are actually accessed.

    Args:
        name: Attribute name being accessed

    Returns:
        The requested attribute from opik_client module

    Raises:
        AttributeError: If the requested attribute is not available

    Example:
        >>> from deep_agent.integrations import OpikClient
        >>> # Import only happens here, not at module load time
        >>> client = OpikClient()
    """
    if name in ("OpikClient", "OptimizerAlgorithm", "ALGORITHM_SELECTION_GUIDE", "get_opik_client"):
        from deep_agent.integrations.opik_client import (
            ALGORITHM_SELECTION_GUIDE,
            OpikClient,
            OptimizerAlgorithm,
            get_opik_client,
        )

        # Cache the imports in module globals
        globals().update(
            {
                "OpikClient": OpikClient,
                "OptimizerAlgorithm": OptimizerAlgorithm,
                "ALGORITHM_SELECTION_GUIDE": ALGORITHM_SELECTION_GUIDE,
                "get_opik_client": get_opik_client,
            }
        )
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
