"""
Configuration API Pydantic models for public settings exposure.

This module provides models for safely exposing non-sensitive configuration
settings to the frontend client. All API keys, secrets, and credentials
are excluded for security.

Models:
    PublicConfig: Public-safe configuration settings for frontend consumption

Security Notes:
    - NEVER include API keys, passwords, or database credentials
    - Only expose settings needed for frontend functionality
    - All sensitive data filtered via explicit field selection

Example:
    >>> from deep_agent.models.config import PublicConfig
    >>> from deep_agent.config import get_settings
    >>> settings = get_settings()
    >>> config = PublicConfig(
    ...     env=settings.ENV,
    ...     debug=settings.DEBUG,
    ...     api_version=settings.API_VERSION,
    ...     app_version="0.1.0",
    ...     websocket_path="/api/v1/ws",
    ...     stream_timeout_seconds=settings.STREAM_TIMEOUT_SECONDS,
    ...     heartbeat_interval_seconds=settings.HEARTBEAT_INTERVAL_SECONDS,
    ...     enable_hitl=settings.ENABLE_HITL,
    ...     enable_reasoning_ui=True,
    ...     enable_cost_tracking=settings.ENABLE_COST_TRACKING,
    ...     is_replit=settings.is_replit,
    ...     replit_dev_domain=settings.REPLIT_DEV_DOMAIN
    ... )
"""

from pydantic import BaseModel, Field


class PublicConfig(BaseModel):
    """
    Public configuration settings safe for frontend exposure.

    Contains only non-sensitive settings needed by the frontend client
    for proper operation. All API keys, secrets, and credentials are
    explicitly excluded for security.

    Attributes:
        env: Deployment environment (local/dev/staging/prod/test)
        debug: Debug mode enabled (enables verbose logging, dev features)
        api_version: API version string (e.g., "v1")
        app_version: Application version from package metadata
        websocket_path: WebSocket endpoint path for real-time communication
        stream_timeout_seconds: Maximum streaming operation timeout
        heartbeat_interval_seconds: WebSocket keep-alive interval
        enable_hitl: Human-in-the-loop workflows enabled
        enable_reasoning_ui: Show reasoning effort indicators in UI
        enable_cost_tracking: Track and display API usage costs
        is_replit: Running in Replit environment
        replit_dev_domain: Replit development domain (if applicable)

    Example:
        >>> config = PublicConfig(
        ...     env="prod",
        ...     debug=False,
        ...     api_version="v1",
        ...     app_version="0.1.0",
        ...     websocket_path="/api/v1/ws",
        ...     stream_timeout_seconds=180,
        ...     heartbeat_interval_seconds=5,
        ...     enable_hitl=True,
        ...     enable_reasoning_ui=True,
        ...     enable_cost_tracking=True,
        ...     is_replit=False,
        ...     replit_dev_domain=None
        ... )
        >>> print(config.env, config.api_version)
        prod v1
    """

    env: str = Field(
        description="Deployment environment (local/dev/staging/prod/test)",
    )
    debug: bool = Field(
        description="Debug mode enabled",
    )
    api_version: str = Field(
        description="API version string (e.g., 'v1')",
    )
    app_version: str = Field(
        description="Application version from package metadata",
    )
    websocket_path: str = Field(
        default="/api/v1/ws",
        description="WebSocket endpoint path for real-time communication",
    )
    stream_timeout_seconds: int = Field(
        description="Maximum streaming operation timeout in seconds",
    )
    heartbeat_interval_seconds: int = Field(
        default=5,
        description="WebSocket keep-alive interval in seconds",
    )
    enable_hitl: bool = Field(
        description="Human-in-the-loop workflows enabled",
    )
    enable_reasoning_ui: bool = Field(
        description="Show reasoning effort indicators in UI",
    )
    enable_cost_tracking: bool = Field(
        description="Track and display API usage costs",
    )
    is_replit: bool = Field(
        description="Running in Replit environment",
    )
    replit_dev_domain: str | None = Field(
        default=None,
        description="Replit development domain (if applicable)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "env": "prod",
                "debug": False,
                "api_version": "v1",
                "app_version": "0.1.0",
                "websocket_path": "/api/v1/ws",
                "stream_timeout_seconds": 180,
                "heartbeat_interval_seconds": 5,
                "enable_hitl": True,
                "enable_reasoning_ui": True,
                "enable_cost_tracking": True,
                "is_replit": False,
                "replit_dev_domain": None,
            }
        }
    }
