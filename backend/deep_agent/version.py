"""Dynamic version loading from package metadata.

This module provides the single source of truth for the application version
by reading from package metadata (populated from pyproject.toml during installation).

The version is loaded dynamically at runtime using importlib.metadata,
ensuring consistency across the entire application without manual updates.

Example:
    Get the current version::

        from deep_agent.version import get_version, __version__

        # Using the function
        version = get_version()
        print(f"Running Deep Agent AGI v{version}")

        # Using the module constant
        print(f"Version: {__version__}")

Note:
    During development (when package is not installed), returns "0.0.0-dev".
    In production, returns the version from pyproject.toml.
"""

import importlib.metadata
from functools import lru_cache

# Package name as defined in pyproject.toml [tool.poetry] name
PACKAGE_NAME = "deep-agent-agi"

# Development fallback version
DEV_VERSION = "0.0.0-dev"


@lru_cache(maxsize=1)
def get_version() -> str:
    """Get the package version from metadata.

    Attempts to read the version from installed package metadata.
    Falls back to development version if package is not installed
    (e.g., running directly from source without installation).

    Returns:
        Version string from pyproject.toml if installed,
        otherwise "0.0.0-dev" for development environments.

    Example:
        >>> from deep_agent.version import get_version
        >>> version = get_version()
        >>> print(version)  # "0.1.0" or "0.0.0-dev"
    """
    try:
        return importlib.metadata.version(PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        # Package not installed (running from source)
        return DEV_VERSION


# Module-level dynamic __version__ attribute
# Uses __getattr__ to ensure __version__ always reflects get_version()
# even after cache_clear() is called (e.g., in tests)
def __getattr__(name: str) -> str:
    """Provide dynamic module attributes.

    This ensures __version__ always returns the current get_version() result,
    maintaining consistency even if the cache is cleared.

    Args:
        name: Attribute name being accessed.

    Returns:
        The version string if name is "__version__".

    Raises:
        AttributeError: If name is not a recognized attribute.
    """
    if name == "__version__":
        return get_version()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
