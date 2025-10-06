"""Unit tests for configuration management."""
import os
from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.deep_agent.config.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Clear the settings cache before each test."""
    get_settings.cache_clear()


class TestSettings:
    """Test Settings class."""

    def test_settings_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings load from environment variables."""
        # Set test environment variables
        monkeypatch.setenv("ENV", "local")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("API_HOST", "127.0.0.1")
        monkeypatch.setenv("API_PORT", "8000")

        settings = Settings()

        assert settings.ENV == "local"
        assert settings.DEBUG is True
        assert settings.OPENAI_API_KEY == "test-key-123"
        assert settings.API_HOST == "127.0.0.1"
        assert settings.API_PORT == 8000

    def test_settings_required_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that required fields must be provided."""
        # Clear critical env vars
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_settings_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default values are applied correctly."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings()

        # Check defaults
        assert settings.ENV == "local"
        assert settings.DEBUG is False
        assert settings.GPT5_MODEL_NAME == "gpt-5"
        assert settings.GPT5_DEFAULT_REASONING_EFFORT == "medium"
        assert settings.API_HOST == "0.0.0.0"
        assert settings.API_PORT == 8000

    def test_settings_reasoning_effort_validation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that reasoning effort must be valid value."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GPT5_DEFAULT_REASONING_EFFORT", "invalid")

        with pytest.raises(ValidationError):
            Settings()

    def test_settings_cors_origins_parsing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CORS origins are parsed from comma-separated string."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")

        settings = Settings()

        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://localhost:8000",
        ]

    def test_get_settings_singleton(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_settings returns same instance."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_log_level_conversion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that log level string is converted to uppercase."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LOG_LEVEL", "info")

        settings = Settings()

        assert settings.LOG_LEVEL == "INFO"

    def test_settings_database_url_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that database URL is properly formatted."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb"
        )

        settings = Settings()

        assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/testdb"

    def test_settings_feature_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that feature flags parse correctly."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("ENABLE_HITL", "true")
        monkeypatch.setenv("ENABLE_SUB_AGENTS", "false")
        monkeypatch.setenv("ENABLE_MEMORY_SYSTEM", "true")

        settings = Settings()

        assert settings.ENABLE_HITL is True
        assert settings.ENABLE_SUB_AGENTS is False
        assert settings.ENABLE_MEMORY_SYSTEM is True
