"""Integration tests for public config API endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client.

    Imports app here to avoid circular dependencies and ensure
    fresh app instance for each test.
    """
    from backend.deep_agent.main import app

    return TestClient(app)


class TestPublicConfigEndpoint:
    """Test GET /api/v1/config/public endpoint."""

    def test_get_public_config(self, client: TestClient) -> None:
        """Test that endpoint returns expected structure with all fields."""
        # Act
        response = client.get("/api/v1/config/public")

        # Assert: Response successful
        assert response.status_code == 200

        # Assert: Response is JSON
        data = response.json()
        assert isinstance(data, dict)

        # Assert: All required fields present
        required_fields = [
            "env",
            "debug",
            "api_version",
            "app_version",
            "websocket_path",
            "stream_timeout_seconds",
            "heartbeat_interval_seconds",
            "enable_hitl",
            "enable_reasoning_ui",
            "enable_cost_tracking",
            "is_replit",
            "replit_dev_domain",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Assert: Field types are correct
        assert isinstance(data["env"], str)
        assert isinstance(data["debug"], bool)
        assert isinstance(data["api_version"], str)
        assert isinstance(data["app_version"], str)
        assert isinstance(data["websocket_path"], str)
        assert isinstance(data["stream_timeout_seconds"], int)
        assert isinstance(data["heartbeat_interval_seconds"], int)
        assert isinstance(data["enable_hitl"], bool)
        assert isinstance(data["enable_reasoning_ui"], bool)
        assert isinstance(data["enable_cost_tracking"], bool)
        assert isinstance(data["is_replit"], bool)
        assert data["replit_dev_domain"] is None or isinstance(data["replit_dev_domain"], str)

        # Assert: WebSocket path is correct
        assert data["websocket_path"] == "/api/v1/ws"

        # Assert: Timeouts are positive integers
        assert data["stream_timeout_seconds"] > 0
        assert data["heartbeat_interval_seconds"] > 0

    def test_config_excludes_secrets(self, client: TestClient) -> None:
        """Test that response excludes all API keys, secrets, and passwords."""
        # Act
        response = client.get("/api/v1/config/public")

        # Assert: Response successful
        assert response.status_code == 200

        # Assert: Response data
        data = response.json()

        # Assert: No sensitive fields present (case-insensitive check)
        # Convert all keys to lowercase for checking
        data_str_lower = str(data).lower()

        # Security-sensitive terms that should NEVER appear
        sensitive_terms = [
            "api_key",
            "apikey",
            "secret",
            "password",
            "passwd",
            "pwd",
            "token",
            "credential",
            "database_url",
            "db_url",
            "postgres_password",
            "redis_password",
            "jwt_secret",
            "openai",
            "google",
            "perplexity",
            "langsmith",
        ]

        for term in sensitive_terms:
            assert term not in data_str_lower, f"Sensitive term found in response: {term}"

        # Assert: Specifically verify these sensitive settings are NOT in response
        assert "OPENAI_API_KEY" not in data
        assert "GOOGLE_API_KEY" not in data
        assert "PERPLEXITY_API_KEY" not in data
        assert "LANGSMITH_API_KEY" not in data
        assert "DATABASE_URL" not in data
        assert "POSTGRES_PASSWORD" not in data
        assert "SECRET_KEY" not in data
        assert "JWT_SECRET" not in data

    def test_config_cache_headers(self, client: TestClient) -> None:
        """Test that Cache-Control header is present."""
        # Act
        response = client.get("/api/v1/config/public")

        # Assert: Response successful
        assert response.status_code == 200

        # Assert: Cache-Control header present
        assert "cache-control" in response.headers or "Cache-Control" in response.headers

        # Assert: Cache header value is correct (5 minutes = 300 seconds)
        cache_header = response.headers.get("cache-control") or response.headers.get(
            "Cache-Control"
        )
        assert "public" in cache_header.lower()
        assert "max-age=300" in cache_header.lower()

        # Assert: Request ID header present (for tracing)
        assert (
            "x-request-id" in response.headers
            or "X-Request-ID" in response.headers
            or "request-id" in response.headers
        )

    def test_config_values_match_settings(self, client: TestClient) -> None:
        """Test that config values match backend settings."""
        from backend.deep_agent.config.settings import get_settings
        from backend.deep_agent.version import get_version

        # Arrange
        settings = get_settings()
        app_version = get_version()

        # Act
        response = client.get("/api/v1/config/public")

        # Assert: Response successful
        assert response.status_code == 200

        # Assert: Values match settings
        data = response.json()
        assert data["env"] == settings.ENV
        assert data["debug"] == settings.DEBUG
        assert data["api_version"] == settings.API_VERSION
        assert data["app_version"] == app_version
        assert data["stream_timeout_seconds"] == settings.STREAM_TIMEOUT_SECONDS
        assert data["heartbeat_interval_seconds"] == settings.HEARTBEAT_INTERVAL_SECONDS
        assert data["enable_hitl"] == settings.ENABLE_HITL
        assert data["enable_cost_tracking"] == settings.ENABLE_COST_TRACKING
        assert data["is_replit"] == settings.is_replit
        assert data["replit_dev_domain"] == settings.REPLIT_DEV_DOMAIN

    def test_config_reasoning_ui_always_enabled(self, client: TestClient) -> None:
        """Test that enable_reasoning_ui is always True (hardcoded for UI visibility)."""
        # Act
        response = client.get("/api/v1/config/public")

        # Assert: Response successful
        assert response.status_code == 200

        # Assert: Reasoning UI always enabled
        data = response.json()
        assert data["enable_reasoning_ui"] is True
