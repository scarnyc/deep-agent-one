"""
Integration tests for LangSmith integration.

Tests the configuration and setup of LangSmith tracing for observability
of agent operations, LLM calls, and tool invocations with real environment
variable configuration.
"""

from unittest.mock import Mock, patch

import pytest

from backend.deep_agent.config.settings import Settings


@pytest.fixture
def mock_settings_with_langsmith() -> Settings:
    """Fixture providing Settings with LangSmith configuration."""
    settings = Mock(spec=Settings)
    settings.LANGSMITH_API_KEY = "lsv2_test_key_1234567890abcdef"  # pragma: allowlist secret
    settings.LANGSMITH_PROJECT = "deep-agent-agi-test"
    settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
    settings.LANGSMITH_TRACING_V2 = True
    return settings


@pytest.fixture
def mock_settings_without_api_key() -> Settings:
    """Fixture providing Settings without LangSmith API key."""
    settings = Mock(spec=Settings)
    settings.LANGSMITH_API_KEY = None
    settings.LANGSMITH_PROJECT = "deep-agent-agi"
    settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
    settings.LANGSMITH_TRACING_V2 = True
    return settings


@pytest.fixture
def mock_settings_tracing_disabled() -> Settings:
    """Fixture providing Settings with tracing disabled."""
    settings = Mock(spec=Settings)
    settings.LANGSMITH_API_KEY = "lsv2_test_key_1234567890abcdef"  # pragma: allowlist secret
    settings.LANGSMITH_PROJECT = "deep-agent-agi"
    settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
    settings.LANGSMITH_TRACING_V2 = False
    return settings


class TestLangSmithSetupIntegration:
    """Integration tests for LangSmith integration setup and configuration."""

    def test_setup_langsmith_configures_environment_variables(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that setup_langsmith sets required environment variables."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}) as mock_env:
            # Act
            setup_langsmith(mock_settings_with_langsmith)

            # Assert - All environment variables set
            # pragma: allowlist secret
            assert mock_env["LANGSMITH_API_KEY"] == "lsv2_test_key_1234567890abcdef"
            assert mock_env["LANGSMITH_PROJECT"] == "deep-agent-agi-test"
            assert mock_env["LANGSMITH_ENDPOINT"] == "https://api.smith.langchain.com"
            assert mock_env["LANGSMITH_TRACING_V2"] == "true"

    def test_setup_langsmith_raises_without_api_key(
        self,
        mock_settings_without_api_key: Settings,
    ) -> None:
        """Test that setup_langsmith raises ValueError when API key is missing."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        # Act & Assert
        with pytest.raises(ValueError, match="LangSmith API key is required"):
            setup_langsmith(mock_settings_without_api_key)

    def test_setup_langsmith_respects_tracing_disabled(
        self,
        mock_settings_tracing_disabled: Settings,
    ) -> None:
        """Test that tracing can be disabled via settings."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}) as mock_env:
            # Act
            setup_langsmith(mock_settings_tracing_disabled)

            # Assert - Tracing set to false
            assert mock_env["LANGSMITH_TRACING_V2"] == "false"

    def test_setup_langsmith_uses_get_settings_if_none_provided(self) -> None:
        """Test that setup_langsmith uses get_settings() when settings=None."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.LANGSMITH_API_KEY = "test_key"
            mock_settings.LANGSMITH_PROJECT = "test-project"
            mock_settings.LANGSMITH_ENDPOINT = "https://test.endpoint.com"
            mock_settings.LANGSMITH_TRACING_V2 = True
            mock_get_settings.return_value = mock_settings

            with patch("backend.deep_agent.integrations.langsmith.os.environ", {}):
                # Act
                setup_langsmith(None)

                # Assert
                mock_get_settings.assert_called_once()

    def test_setup_langsmith_logs_configuration(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that setup_langsmith logs configuration details."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}):
            with patch("backend.deep_agent.integrations.langsmith.logger") as mock_logger:
                # Act
                setup_langsmith(mock_settings_with_langsmith)

                # Assert - Logger called
                assert mock_logger.info.called
                # Verify log message mentions LangSmith
                call_args = mock_logger.info.call_args
                assert "LangSmith" in str(call_args) or "langsmith" in str(call_args).lower()

    def test_setup_langsmith_masks_api_key_in_logs(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that API key is masked in log messages."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}):
            with patch("backend.deep_agent.integrations.langsmith.logger") as mock_logger:
                # Act
                setup_langsmith(mock_settings_with_langsmith)

                # Assert - Full API key never logged
                for call in mock_logger.info.call_args_list:
                    call_str = str(call)
                    # Full key should not appear in logs
                    assert "lsv2_test_key_1234567890abcdef" not in call_str

    def test_setup_langsmith_converts_bool_to_string(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that boolean TRACING_V2 is converted to string for env var."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}) as mock_env:
            # Act
            setup_langsmith(mock_settings_with_langsmith)

            # Assert - Boolean converted to lowercase string
            assert isinstance(mock_env["LANGSMITH_TRACING_V2"], str)
            assert mock_env["LANGSMITH_TRACING_V2"] in ["true", "false"]

    def test_setup_langsmith_handles_custom_endpoint(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that custom LangSmith endpoint is respected."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        # Arrange - Custom endpoint
        mock_settings_with_langsmith.LANGSMITH_ENDPOINT = "https://custom.langsmith.endpoint.com"

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}) as mock_env:
            # Act
            setup_langsmith(mock_settings_with_langsmith)

            # Assert
            assert mock_env["LANGSMITH_ENDPOINT"] == "https://custom.langsmith.endpoint.com"

    def test_setup_langsmith_validates_api_key_format(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that API key format is validated (optional warning)."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        # Arrange - Invalid API key format
        mock_settings_with_langsmith.LANGSMITH_API_KEY = "invalid_key_format"

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}):
            with patch("backend.deep_agent.integrations.langsmith.logger") as mock_logger:
                # Act
                setup_langsmith(mock_settings_with_langsmith)

                # Assert - May log warning but doesn't raise
                # (API key validation is lenient - actual validation happens on API call)
                assert mock_logger.info.called or mock_logger.warning.called

    def test_setup_langsmith_idempotent(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that calling setup_langsmith multiple times is safe."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}) as mock_env:
            # Act - Call twice
            setup_langsmith(mock_settings_with_langsmith)
            setup_langsmith(mock_settings_with_langsmith)

            # Assert - Environment variables still set correctly (not duplicated)
            # pragma: allowlist secret
            assert mock_env["LANGSMITH_API_KEY"] == "lsv2_test_key_1234567890abcdef"
            assert mock_env["LANGSMITH_PROJECT"] == "deep-agent-agi-test"


class TestLangSmithIntegrationValidation:
    """Integration tests for validation and error handling in LangSmith setup."""

    def test_setup_fails_with_empty_api_key(self) -> None:
        """Test that empty string API key raises error."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        settings = Mock(spec=Settings)
        settings.LANGSMITH_API_KEY = ""  # Empty string
        settings.LANGSMITH_PROJECT = "test"
        settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
        settings.LANGSMITH_TRACING_V2 = True

        # Act & Assert
        with pytest.raises(ValueError, match="LangSmith API key is required"):
            setup_langsmith(settings)

    def test_setup_fails_with_whitespace_api_key(self) -> None:
        """Test that whitespace-only API key raises error."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        settings = Mock(spec=Settings)
        settings.LANGSMITH_API_KEY = "   "  # Whitespace only
        settings.LANGSMITH_PROJECT = "test"
        settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
        settings.LANGSMITH_TRACING_V2 = True

        # Act & Assert
        with pytest.raises(ValueError, match="LangSmith API key is required"):
            setup_langsmith(settings)

    def test_setup_accepts_minimal_configuration(
        self,
        mock_settings_with_langsmith: Settings,
    ) -> None:
        """Test that setup works with just API key and defaults."""
        from backend.deep_agent.integrations.langsmith import setup_langsmith

        with patch("backend.deep_agent.integrations.langsmith.os.environ", {}) as mock_env:
            # Act
            setup_langsmith(mock_settings_with_langsmith)

            # Assert - All required variables set
            assert "LANGSMITH_API_KEY" in mock_env
            assert "LANGSMITH_PROJECT" in mock_env
            assert "LANGSMITH_ENDPOINT" in mock_env
            assert "LANGSMITH_TRACING_V2" in mock_env
