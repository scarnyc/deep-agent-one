"""
Config API endpoints for Deep Agent AGI.

Provides REST endpoints for retrieving public configuration settings
that the frontend needs to operate correctly. All sensitive data
(API keys, secrets, credentials) is excluded from responses.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from deep_agent.config.settings import get_settings
from deep_agent.core.logging import get_logger
from deep_agent.models.config import PublicConfig
from deep_agent.version import get_version

logger = get_logger(__name__)

# Create API router
router = APIRouter()


@router.get("/config/public", response_model=PublicConfig)
async def get_public_config(request: Request) -> JSONResponse:
    """
    Get public configuration settings for frontend consumption.

    Returns non-sensitive configuration settings that the frontend
    client needs to operate correctly. All API keys, secrets, and
    database credentials are excluded for security.

    This endpoint is cacheable (5 minutes) as configuration rarely
    changes during runtime.

    Args:
        request: FastAPI request object (for request_id access)

    Returns:
        JSONResponse with PublicConfig data and cache headers

    Example:
        ```python
        # Request
        GET /api/v1/config/public

        # Response (200 OK)
        {
            "env": "prod",
            "debug": false,
            "api_version": "v1",
            "app_version": "0.1.0",
            "websocket_path": "/api/v1/ws",
            "stream_timeout_seconds": 180,
            "heartbeat_interval_seconds": 5,
            "enable_hitl": true,
            "enable_reasoning_ui": true,
            "enable_cost_tracking": true,
            "is_replit": false,
            "replit_dev_domain": null
        }
        ```

    Security:
        - No API keys or secrets exposed
        - No database credentials exposed
        - Only UI-relevant settings included
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "Public config request received",
        request_id=request_id,
    )

    # Load settings
    settings = get_settings()

    # Get application version
    app_version = get_version()

    # Build public config (explicitly selecting safe fields)
    config = PublicConfig(
        env=settings.ENV,
        debug=settings.DEBUG,
        api_version=settings.API_VERSION,
        app_version=app_version,
        websocket_path="/api/v1/ws",
        stream_timeout_seconds=settings.STREAM_TIMEOUT_SECONDS,
        heartbeat_interval_seconds=settings.HEARTBEAT_INTERVAL_SECONDS,
        enable_hitl=settings.ENABLE_HITL,
        enable_reasoning_ui=True,  # Always enabled for UI visibility
        enable_cost_tracking=settings.ENABLE_COST_TRACKING,
        is_replit=settings.is_replit,
        replit_dev_domain=settings.REPLIT_DEV_DOMAIN,
    )

    logger.debug(
        "Public config prepared",
        request_id=request_id,
        env=config.env,
        api_version=config.api_version,
        app_version=config.app_version,
        is_replit=config.is_replit,
    )

    # Return with cache headers (5 minutes)
    return JSONResponse(
        content=config.model_dump(),
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Request-ID": request_id,
        },
    )
