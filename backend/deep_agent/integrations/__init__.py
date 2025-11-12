"""External integrations."""

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
    """
    if name in ("OpikClient", "OptimizerAlgorithm", "ALGORITHM_SELECTION_GUIDE", "get_opik_client"):
        from deep_agent.integrations.opik_client import (
            ALGORITHM_SELECTION_GUIDE,
            OpikClient,
            OptimizerAlgorithm,
            get_opik_client,
        )

        # Cache the imports in module globals
        globals().update({
            "OpikClient": OpikClient,
            "OptimizerAlgorithm": OptimizerAlgorithm,
            "ALGORITHM_SELECTION_GUIDE": ALGORITHM_SELECTION_GUIDE,
            "get_opik_client": get_opik_client,
        })
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
