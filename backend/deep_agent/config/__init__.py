"""Configuration module for Deep Agent AGI.

This module provides centralized configuration management using Pydantic settings
with environment variable support and comprehensive validation.

The configuration system supports:
- Environment-specific settings (local/dev/staging/prod/test)
- Type validation and coercion
- Default values with environment variable overrides
- Singleton pattern for efficient settings access
- Structured logging and monitoring configuration

Example:
    Basic usage with singleton pattern::

        from deep_agent.config import get_settings

        settings = get_settings()
        print(settings.OPENAI_API_KEY)
        print(settings.ENV)

    Testing with custom settings::

        from deep_agent.config import Settings

        test_settings = Settings(
            OPENAI_API_KEY="test-key",
            ENV="test",
            DEBUG=True
        )

Attributes:
    Settings: Main settings class with all configuration parameters
    get_settings: Factory function returning singleton Settings instance

Environment Variables:
    Required:
        OPENAI_API_KEY: OpenAI API key for GPT-5 access

    Optional:
        LANGSMITH_API_KEY: LangSmith tracing API key
        PERPLEXITY_API_KEY: Perplexity search API key
        ENV: Environment name (default: "local")
        DEBUG: Debug mode flag (default: False)

    See Settings class for complete list of environment variables.

Related:
    - deep_agent.core: Core functionality using these settings
    - deep_agent.services: Services configured by these settings
"""

from deep_agent.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
