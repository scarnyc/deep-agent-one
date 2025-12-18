"""
Integration tests for configuration management.

Tests the Settings class and get_settings() function with real environment
variable loading, validation of required fields, default values, and
singleton pattern behavior.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.deep_agent.config.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """
    Clear the settings cache before each test.

    Ensures each test starts with a fresh Settings instance by clearing
    the lru_cache on get_settings().
    """
    get_settings.cache_clear()


class TestSettingsIntegration:
    """Integration tests for Settings class initialization and validation."""

    def test_settings_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that settings load from environment variables.

        Scenario:
            Set environment variables for all core settings

        Expected:
            Settings instance reflects environment variable values
        """
        # Set test environment variables
        monkeypatch.setenv("ENV", "local")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")  # pragma: allowlist secret
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-123")  # pragma: allowlist secret
        monkeypatch.setenv("API_HOST", "127.0.0.1")
        monkeypatch.setenv("API_PORT", "8000")

        settings = Settings()

        assert settings.ENV == "local"
        assert settings.DEBUG is True
        assert settings.OPENAI_API_KEY == "test-key-123"  # pragma: allowlist secret
        assert settings.GOOGLE_API_KEY == "test-google-key-123"  # pragma: allowlist secret
        assert settings.API_HOST == "127.0.0.1"
        assert settings.API_PORT == 8000

    def test_settings_required_fields(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """
        Test that required fields must be provided.

        Scenario:
            Create Settings without OPENAI_API_KEY environment variable

        Expected:
            ValidationError raised with OPENAI_API_KEY in error message
        """
        # Create empty .env file to prevent reading from actual .env
        empty_env = tmp_path / ".env"
        empty_env.write_text("")

        # Patch env_file to use empty file and delete OPENAI_API_KEY from env
        monkeypatch.setattr(
            "backend.deep_agent.config.settings.Settings.model_config",
            {
                "env_file": str(empty_env),
                "env_file_encoding": "utf-8",
                "case_sensitive": True,
                "extra": "ignore",
            },
        )
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_settings_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that default values are applied correctly.

        Scenario:
            Create Settings with only required fields

        Expected:
            Optional fields use documented default values
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        # Explicitly set to defaults to override any .env file values
        monkeypatch.setenv("ENV", "prod")
        monkeypatch.setenv("DEBUG", "false")

        settings = Settings()

        # Check defaults
        assert settings.ENV == "prod"
        assert settings.DEBUG is False
        assert settings.GPT_MODEL_NAME == "gpt-5.1-2025-11-13"
        assert settings.GPT_DEFAULT_REASONING_EFFORT == "medium"
        assert settings.API_HOST == "0.0.0.0"
        assert settings.API_PORT == 8000

    def test_settings_reasoning_effort_validation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that reasoning effort must be valid value.

        Scenario:
            Set GPT_DEFAULT_REASONING_EFFORT to invalid value

        Expected:
            ValidationError raised
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.setenv("GPT_DEFAULT_REASONING_EFFORT", "invalid")

        with pytest.raises(ValidationError):
            Settings()

    def test_settings_cors_origins_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that CORS origins are parsed from comma-separated string.

        Scenario:
            Set CORS_ORIGINS as comma-separated string

        Expected:
            cors_origins_list property returns list containing expected URLs
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")

        settings = Settings()

        # Check expected values are present (environment may add more)
        assert "http://localhost:3000" in settings.cors_origins_list
        assert "http://localhost:8000" in settings.cors_origins_list

    def test_get_settings_singleton(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that get_settings returns same instance.

        Scenario:
            Call get_settings() multiple times

        Expected:
            Same Settings instance returned (singleton pattern via lru_cache)
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_log_level_conversion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that log level string is converted to uppercase.

        Scenario:
            Set LOG_LEVEL to lowercase string

        Expected:
            Settings.LOG_LEVEL is uppercase
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.setenv("LOG_LEVEL", "info")

        settings = Settings()

        assert settings.LOG_LEVEL == "INFO"

    def test_settings_database_url_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that database URL is properly formatted.

        Scenario:
            Set DATABASE_URL environment variable

        Expected:
            Settings.DATABASE_URL matches environment value
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        # pragma: allowlist secret
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb"
        )

        settings = Settings()

        assert (
            settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/testdb"
        )  # pragma: allowlist secret

    def test_settings_feature_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that feature flags parse correctly.

        Scenario:
            Set boolean feature flag environment variables

        Expected:
            Settings converts string values to boolean correctly
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.setenv("ENABLE_HITL", "true")
        monkeypatch.setenv("ENABLE_SUB_AGENTS", "false")
        monkeypatch.setenv("ENABLE_MEMORY_SYSTEM", "true")

        settings = Settings()

        assert settings.ENABLE_HITL is True
        assert settings.ENABLE_SUB_AGENTS is False
        assert settings.ENABLE_MEMORY_SYSTEM is True
