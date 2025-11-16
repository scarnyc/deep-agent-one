"""Application settings and configuration management.

This module defines the complete configuration schema for Deep Agent AGI using
Pydantic settings with environment variable support, type validation, and
sensible defaults.

The Settings class provides:
- Comprehensive environment variable mapping
- Type validation and coercion
- Default values for all optional settings
- Field-level documentation
- Custom validators for complex types
- Environment-specific behavior

Environment variables are loaded from .env file and can be overridden by
system environment variables.

Example:
    Load settings from environment::

        from deep_agent.config import get_settings

        settings = get_settings()

        # Access settings
        api_key = settings.OPENAI_API_KEY
        is_debug = settings.DEBUG
        cors_origins = settings.cors_origins_list

    Create custom settings for testing::

        from deep_agent.config import Settings

        test_settings = Settings(
            OPENAI_API_KEY="sk-test-key",
            ENV="test",
            DEBUG=True,
            MOCK_EXTERNAL_APIS=True
        )

Attributes:
    Settings: Main configuration class with all application settings
    get_settings: Singleton factory function for Settings instance

Related:
    - deep_agent.core.llm: LLM configuration consumers
    - deep_agent.services: Service configuration consumers
    - deep_agent.api: API configuration consumers
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    This class uses Pydantic BaseSettings to automatically load configuration
    from environment variables and .env files with type validation and
    conversion. Settings are immutable after initialization.

    All settings can be overridden via environment variables matching the
    attribute name. For example, OPENAI_API_KEY environment variable will
    override the OPENAI_API_KEY setting.

    Attributes:
        ENV: Environment name (local/dev/staging/prod/test). Controls
            environment-specific behavior like logging and validation.
        DEBUG: Debug mode flag. Enables verbose logging and development features.

        OPENAI_API_KEY: OpenAI API key (required). Used for GPT-5 access.
        GPT5_MODEL_NAME: GPT-5 model identifier.
        GPT5_DEFAULT_REASONING_EFFORT: Default reasoning effort level.
        GPT5_DEFAULT_VERBOSITY: Default response verbosity.
        GPT5_MAX_TOKENS: Maximum tokens per completion.
        GPT5_TEMPERATURE: Sampling temperature (0.0-2.0).

        ENABLE_DYNAMIC_REASONING: Enable dynamic reasoning effort adjustment.
        REASONING_MINIMAL_TIMEOUT: Timeout for minimal reasoning (seconds).
        REASONING_LOW_TIMEOUT: Timeout for low reasoning (seconds).
        REASONING_MEDIUM_TIMEOUT: Timeout for medium reasoning (seconds).
        REASONING_HIGH_TIMEOUT: Timeout for high reasoning (seconds).
        TRIGGER_PHRASES: Comma-separated phrases triggering high reasoning.
        COMPLEXITY_THRESHOLD_HIGH: Complexity score threshold for high reasoning.
        COMPLEXITY_THRESHOLD_MEDIUM: Complexity score threshold for medium reasoning.

        ENABLE_RESPONSE_CHAINING: Enable multi-turn response chaining.
        MAX_CHAIN_LENGTH: Maximum chained responses.
        ENABLE_CONTEXT_COMPRESSION: Enable context compression.

        PERPLEXITY_API_KEY: Perplexity API key for web search (optional).

        LANGSMITH_API_KEY: LangSmith API key for tracing (optional).
        LANGSMITH_PROJECT: LangSmith project name.
        LANGSMITH_ENDPOINT: LangSmith API endpoint.
        LANGSMITH_TRACING_V2: Enable LangSmith v2 tracing.

        OPIK_API_KEY: Opik API key for prompt optimization (optional).
        OPIK_WORKSPACE: Opik workspace name (optional).
        OPIK_PROJECT: Opik project name.

        DATABASE_URL: PostgreSQL connection URL (Phase 1, optional).
        POSTGRES_USER: PostgreSQL username (Phase 1, optional).
        POSTGRES_PASSWORD: PostgreSQL password (Phase 1, optional).
        POSTGRES_DB: PostgreSQL database name (Phase 1, optional).
        ENABLE_PGVECTOR: Enable pgvector extension for embeddings.

        CHECKPOINT_DB_PATH: SQLite path for LangGraph checkpoints.
        CHECKPOINT_CLEANUP_DAYS: Days to retain old checkpoints.

        STREAM_VERSION: LangGraph streaming version (v1/v2).
        STREAM_TIMEOUT_SECONDS: WebSocket streaming timeout.
        STREAM_ALLOWED_EVENTS: Comma-separated allowed stream events.

        REDIS_URL: Redis connection URL (Phase 2, optional).
        REDIS_PASSWORD: Redis password (Phase 2, optional).
        CACHE_TTL: Cache time-to-live (seconds).

        API_HOST: FastAPI bind host.
        API_PORT: FastAPI bind port.
        API_RELOAD: Enable auto-reload on code changes.
        CORS_ORIGINS: Comma-separated CORS allowed origins.
        API_VERSION: API version string.

        PLAYWRIGHT_HEADLESS: Run Playwright in headless mode.
        PLAYWRIGHT_BROWSERS_PATH: Playwright browser installation path.
        MCP_PERPLEXITY_TIMEOUT: Perplexity MCP timeout (seconds).
        MCP_PLAYWRIGHT_TIMEOUT: Playwright MCP timeout (seconds).

        TOOL_EXECUTION_TIMEOUT: Tool execution timeout (seconds).
        WEB_SEARCH_TIMEOUT: Web search tool timeout (seconds).
        MAX_TOOL_CALLS_PER_INVOCATION: Maximum tool calls per agent invocation.

        SECRET_KEY: Application secret key (optional).
        JWT_SECRET: JWT signing secret (optional).
        JWT_ALGORITHM: JWT algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration.
        BCRYPT_ROUNDS: Bcrypt hashing rounds.

        RATE_LIMIT_REQUESTS: Rate limit requests per period.
        RATE_LIMIT_PERIOD: Rate limit period (seconds).
        RATE_LIMIT_REASONING_HIGH: High reasoning rate limit.
        RATE_LIMIT_REASONING_PERIOD: High reasoning rate limit period.

        AUDITOR_ENABLED: Enable TheAuditor security scanning.
        AUDITOR_AUTO_SCAN: Auto-run security scans.
        AUDITOR_SCAN_ON_DEPLOY: Run security scan on deployment.

        LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL).
        LOG_FORMAT: Log format (json/standard).
        ENABLE_STRUCTURED_LOGGING: Enable structured JSON logging.
        LOG_REASONING_DECISIONS: Log reasoning effort decisions.

        MAX_CONCURRENT_REQUESTS: Maximum concurrent HTTP requests.
        REQUEST_TIMEOUT: HTTP request timeout (seconds).
        REASONING_QUEUE_SIZE: Reasoning request queue size.
        ENABLE_ASYNC_PROCESSING: Enable async request processing.

        ENABLE_HITL: Enable human-in-the-loop workflows.
        ENABLE_SUB_AGENTS: Enable sub-agent delegation.
        ENABLE_RESEARCH_MODE: Enable deep research mode (Phase 2).
        ENABLE_COST_TRACKING: Enable cost tracking and logging.
        ENABLE_MEMORY_SYSTEM: Enable memory system (Phase 1).

        ENABLE_DEBUG_TOOLBAR: Enable debug toolbar in API.
        ENABLE_PROFILING: Enable performance profiling.
        MOCK_EXTERNAL_APIS: Mock external API calls for testing.

        REPL_SLUG: Replit slug (optional).
        REPL_OWNER: Replit owner username (optional).

    Example:
        Load settings from .env file::

            # .env
            OPENAI_API_KEY=sk-proj-abc123
            ENV=production
            DEBUG=false
            LOG_LEVEL=INFO

            # Python code
            settings = get_settings()
            print(settings.ENV)  # "production"
            print(settings.DEBUG)  # False

        Override with environment variables::

            $ ENV=test DEBUG=true python app.py

    Note:
        Settings are cached using lru_cache in get_settings() for performance.
        Use Settings() directly only for testing with custom values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment Configuration
    ENV: Literal["local", "dev", "staging", "prod", "test"] = "local"
    DEBUG: bool = False

    # GPT-5 Configuration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key (required)")
    GPT5_MODEL_NAME: str = "gpt-5"
    GPT5_DEFAULT_REASONING_EFFORT: Literal["minimal", "low", "medium", "high"] = (
        "medium"
    )
    GPT5_DEFAULT_VERBOSITY: str = "medium"
    GPT5_MAX_TOKENS: int = 4096
    GPT5_TEMPERATURE: float = 0.7

    # Reasoning System Configuration
    ENABLE_DYNAMIC_REASONING: bool = True
    REASONING_MINIMAL_TIMEOUT: int = 5
    REASONING_LOW_TIMEOUT: int = 15
    REASONING_MEDIUM_TIMEOUT: int = 30
    REASONING_HIGH_TIMEOUT: int = 60
    TRIGGER_PHRASES: str = "think harder,deep dive,analyze carefully,be thorough"
    COMPLEXITY_THRESHOLD_HIGH: float = 0.8
    COMPLEXITY_THRESHOLD_MEDIUM: float = 0.5

    # Token Conservation Settings
    ENABLE_RESPONSE_CHAINING: bool = True
    MAX_CHAIN_LENGTH: int = 3
    ENABLE_CONTEXT_COMPRESSION: bool = True

    # Other AI Services
    PERPLEXITY_API_KEY: str | None = None

    # Monitoring & Tracing
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "deep-agent-agi"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_TRACING_V2: bool = True

    # Prompt Optimization
    OPIK_API_KEY: str | None = None
    OPIK_WORKSPACE: str | None = None
    OPIK_PROJECT: str = "deep-agent-reasoning"

    # Database Configuration (Phase 1)
    DATABASE_URL: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    ENABLE_PGVECTOR: bool = True

    # Checkpointer Configuration (LangGraph State Persistence)
    CHECKPOINT_DB_PATH: str = "data/checkpoints.db"
    CHECKPOINT_CLEANUP_DAYS: int = 30

    # Streaming Configuration
    STREAM_VERSION: Literal["v1", "v2"] = "v2"
    # Increased from 60s to 300s (5 min) to support parallel tool operations
    # With 10 parallel tool calls @ 45s each, 60s was insufficient
    # 300s provides safety margin for rate limits, retries, cold starts
    STREAM_TIMEOUT_SECONDS: int = 300
    # Include both LangGraph v1 (on_tool_*) and v2 (on_tool_call_*) event patterns
    # Plus LLM events for reasoning visibility
    STREAM_ALLOWED_EVENTS: str = "on_chat_model_stream,on_tool_start,on_tool_end,on_tool_call_start,on_tool_call_end,on_chain_start,on_chain_end,on_llm_start,on_llm_end"

    # Redis Cache (Phase 2)
    REDIS_URL: str | None = None
    REDIS_PASSWORD: str | None = None
    CACHE_TTL: int = 3600

    # FastAPI Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    API_VERSION: str = "v1"

    # MCP Server Configuration
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_BROWSERS_PATH: str = "~/.cache/ms-playwright"
    MCP_PERPLEXITY_TIMEOUT: int = 30
    MCP_PLAYWRIGHT_TIMEOUT: int = 60

    # Tool Execution Timeouts
    # NOTE: Tool timeout must be < STREAM_TIMEOUT_SECONDS to prevent race conditions
    TOOL_EXECUTION_TIMEOUT: int = 45  # 45s per tool call (< 60s stream timeout)
    WEB_SEARCH_TIMEOUT: int = 30  # Perplexity search timeout (matches MCP_PERPLEXITY_TIMEOUT)
    # Maximum tool calls per agent invocation
    # Used to calculate LangGraph recursion_limit: (max_tool_calls * 2) + 1
    # Default: 12 tool calls = 25 recursion steps (each tool = 2 steps: LLM call + tool execution)
    MAX_TOOL_CALLS_PER_INVOCATION: int = 12

    # Security Configuration
    SECRET_KEY: str | None = None
    JWT_SECRET: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BCRYPT_ROUNDS: int = 12

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    RATE_LIMIT_REASONING_HIGH: int = 10
    RATE_LIMIT_REASONING_PERIOD: int = 3600

    # TheAuditor Security
    AUDITOR_ENABLED: bool = True
    AUDITOR_AUTO_SCAN: bool = False
    AUDITOR_SCAN_ON_DEPLOY: bool = True

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "standard"] = "json"
    ENABLE_STRUCTURED_LOGGING: bool = True
    LOG_REASONING_DECISIONS: bool = True

    # Performance Configuration
    MAX_CONCURRENT_REQUESTS: int = 50
    REQUEST_TIMEOUT: int = 300
    REASONING_QUEUE_SIZE: int = 10
    ENABLE_ASYNC_PROCESSING: bool = True

    # Feature Flags
    ENABLE_HITL: bool = True
    ENABLE_SUB_AGENTS: bool = True
    ENABLE_RESEARCH_MODE: bool = False  # Phase 2
    ENABLE_COST_TRACKING: bool = True
    ENABLE_MEMORY_SYSTEM: bool = False  # Phase 1

    # Development Tools
    ENABLE_DEBUG_TOOLBAR: bool = False
    ENABLE_PROFILING: bool = False
    MOCK_EXTERNAL_APIS: bool = False

    # Replit Specific
    REPL_SLUG: str | None = None
    REPL_OWNER: str | None = None

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Convert log level to uppercase.

        Args:
            v: Log level string (case-insensitive).

        Returns:
            Uppercase log level string.

        Example:
            >>> validate_log_level("info")
            "INFO"
        """
        return v.upper()

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string.

        Returns:
            List of CORS origin URLs with whitespace stripped.

        Example:
            >>> settings = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:8000")
            >>> settings.cors_origins_list
            ["http://localhost:3000", "http://localhost:8000"]
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def stream_allowed_events_list(self) -> list[str]:
        """Parse allowed stream events from comma-separated string.

        Returns:
            List of allowed LangGraph event names with whitespace stripped.

        Example:
            >>> settings.stream_allowed_events_list
            ["on_chat_model_stream", "on_tool_start", "on_tool_end", ...]
        """
        return [event.strip() for event in self.STREAM_ALLOWED_EVENTS.split(",")]

    @field_validator("TRIGGER_PHRASES", mode="before")
    @classmethod
    def parse_trigger_phrases(cls, v: str | list[str]) -> str:
        """Ensure trigger phrases remain as comma-separated string.

        Args:
            v: Trigger phrases as comma-separated string or list.

        Returns:
            Comma-separated string of trigger phrases.

        Example:
            >>> parse_trigger_phrases(["think harder", "deep dive"])
            "think harder,deep dive"
        """
        if isinstance(v, list):
            return ",".join(v)
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern).

    Returns singleton Settings instance loaded from environment variables.
    Subsequent calls return the same cached instance for performance.

    Returns:
        Cached Settings instance with all configuration loaded.

    Example:
        >>> settings = get_settings()
        >>> settings.OPENAI_API_KEY
        "sk-proj-abc123..."

        >>> # Same instance returned on subsequent calls
        >>> settings2 = get_settings()
        >>> settings is settings2
        True

    Note:
        For testing with custom values, instantiate Settings() directly
        instead of using this cached function.
    """
    return Settings()
