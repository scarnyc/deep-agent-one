"""Application settings and configuration management."""
from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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
    PERPLEXITY_API_KEY: Optional[str] = None

    # Monitoring & Tracing
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "deep-agent-agi"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_TRACING_V2: bool = True

    # Prompt Optimization
    OPIK_API_KEY: Optional[str] = None
    OPIK_WORKSPACE: Optional[str] = None
    OPIK_PROJECT: str = "deep-agent-reasoning"

    # Database Configuration (Phase 1)
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    ENABLE_PGVECTOR: bool = True

    # Checkpointer Configuration (LangGraph State Persistence)
    CHECKPOINT_DB_PATH: str = "data/checkpoints.db"
    CHECKPOINT_CLEANUP_DAYS: int = 30

    # Streaming Configuration
    STREAM_VERSION: Literal["v1", "v2"] = "v2"
    STREAM_TIMEOUT_SECONDS: int = 60
    STREAM_ALLOWED_EVENTS: str = "on_chat_model_stream,on_tool_start,on_tool_end,on_chain_start,on_chain_end"

    # Redis Cache (Phase 2)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
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

    # Security Configuration
    SECRET_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
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
    REPL_SLUG: Optional[str] = None
    REPL_OWNER: Optional[str] = None

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Convert log level to uppercase."""
        return v.upper()

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def stream_allowed_events_list(self) -> list[str]:
        """Parse allowed stream events from comma-separated string."""
        return [event.strip() for event in self.STREAM_ALLOWED_EVENTS.split(",")]

    @field_validator("TRIGGER_PHRASES", mode="before")
    @classmethod
    def parse_trigger_phrases(cls, v: str | list[str]) -> str:
        """Ensure trigger phrases remain as comma-separated string."""
        if isinstance(v, list):
            return ",".join(v)
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
