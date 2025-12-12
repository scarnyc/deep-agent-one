"""
Unit tests for version management.

Tests the get_version() function and __version__ constant, ensuring proper
loading from package metadata and fallback behavior when not installed.
"""

from unittest.mock import patch

import pytest


class TestVersion:
    """Test version loading functionality."""

    def test_get_version_returns_string(self) -> None:
        """
        Test that get_version() returns a string.

        Scenario:
            Call get_version() function

        Expected:
            Returns a non-empty string
        """
        from backend.deep_agent.version import get_version

        # Clear cache to ensure fresh call
        get_version.cache_clear()

        version = get_version()

        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_module_constant(self) -> None:
        """
        Test that __version__ module attribute is available and matches get_version().

        Scenario:
            Import __version__ from version module

        Expected:
            __version__ is a non-empty string equal to get_version()
        """
        from backend.deep_agent.version import __version__, get_version

        # Don't clear cache - verify __version__ equals get_version()
        # Both should return the same cached value
        assert isinstance(__version__, str)
        assert len(__version__) > 0
        assert __version__ == get_version()

    def test_version_dynamic_after_cache_clear(self) -> None:
        """
        Test that __version__ remains consistent with get_version() after cache clear.

        Scenario:
            Clear cache and verify __version__ still equals get_version()

        Expected:
            __version__ always equals get_version(), even after cache_clear()
        """
        import importlib.metadata

        from backend.deep_agent.version import get_version

        # Clear cache and verify consistency
        get_version.cache_clear()

        # Import __version__ fresh after cache clear
        from backend.deep_agent import version

        assert version.__version__ == get_version()

        # Mock a different version and verify consistency
        with patch.object(importlib.metadata, "version", return_value="9.9.9"):
            get_version.cache_clear()
            # Both should now return the mocked version
            assert version.__version__ == get_version()
            assert version.__version__ == "9.9.9"

    def test_version_follows_semver_pattern(self) -> None:
        """
        Test that version follows semantic versioning pattern.

        Scenario:
            Get version from module

        Expected:
            Version string matches x.y.z or x.y.z-suffix pattern
        """
        import re

        from backend.deep_agent.version import get_version

        get_version.cache_clear()
        version = get_version()

        # Semantic versioning pattern: major.minor.patch with optional suffix
        # Matches: 0.1.0, 1.0.0, 0.0.0-dev, 1.2.3-beta.1
        semver_pattern = r"^\d+\.\d+\.\d+(-[\w.]+)?$"

        assert re.match(semver_pattern, version), (
            f"Version '{version}' does not follow semantic versioning pattern"
        )

    def test_version_fallback_when_not_installed(self) -> None:
        """
        Test fallback to dev version when package not installed.

        Scenario:
            Mock PackageNotFoundError from importlib.metadata

        Expected:
            Returns DEV_VERSION ("0.0.0-dev")
        """
        import importlib.metadata

        from backend.deep_agent.version import DEV_VERSION, PACKAGE_NAME, get_version

        get_version.cache_clear()

        with patch.object(
            importlib.metadata,
            "version",
            side_effect=importlib.metadata.PackageNotFoundError(PACKAGE_NAME),
        ):
            # Clear cache again since we're mocking
            get_version.cache_clear()
            version = get_version()

        assert version == DEV_VERSION
        assert version == "0.0.0-dev"

    def test_version_from_installed_package(self) -> None:
        """
        Test reading version from installed package metadata.

        Scenario:
            Mock importlib.metadata.version to return specific version

        Expected:
            Returns the mocked version
        """
        import importlib.metadata

        from backend.deep_agent.version import get_version

        get_version.cache_clear()

        with patch.object(importlib.metadata, "version", return_value="1.2.3"):
            get_version.cache_clear()
            version = get_version()

        assert version == "1.2.3"

    def test_version_is_cached(self) -> None:
        """
        Test that version is cached for performance.

        Scenario:
            Call get_version() multiple times

        Expected:
            importlib.metadata.version called only once (cached)
        """
        import importlib.metadata

        from backend.deep_agent.version import get_version

        get_version.cache_clear()

        with patch.object(
            importlib.metadata, "version", return_value="0.1.0"
        ) as mock_version:
            get_version.cache_clear()

            # Call multiple times
            _ = get_version()
            _ = get_version()
            _ = get_version()

            # Should only be called once due to caching
            mock_version.assert_called_once()

    def test_package_name_constant(self) -> None:
        """
        Test PACKAGE_NAME constant matches pyproject.toml.

        Scenario:
            Check PACKAGE_NAME constant value

        Expected:
            PACKAGE_NAME equals "deep-agent-agi"
        """
        from backend.deep_agent.version import PACKAGE_NAME

        assert PACKAGE_NAME == "deep-agent-agi"

    def test_dev_version_constant(self) -> None:
        """
        Test DEV_VERSION constant value.

        Scenario:
            Check DEV_VERSION constant value

        Expected:
            DEV_VERSION equals "0.0.0-dev"
        """
        from backend.deep_agent.version import DEV_VERSION

        assert DEV_VERSION == "0.0.0-dev"


class TestVersionIntegration:
    """Integration tests for version in FastAPI app."""

    def test_fastapi_app_uses_dynamic_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that FastAPI app uses dynamic version.

        Scenario:
            Import the FastAPI app

        Expected:
            App version matches __version__ from version module
        """
        # Set required environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")

        # Clear caches to force reload with new env vars
        from backend.deep_agent.config.settings import clear_settings_cache

        clear_settings_cache()

        from backend.deep_agent.main import create_app
        from backend.deep_agent.version import __version__

        app = create_app()

        assert app.version == __version__

    def test_version_in_openapi_schema(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test version appears in OpenAPI schema.

        Scenario:
            Get OpenAPI schema from app

        Expected:
            Schema info.version matches __version__
        """
        # Set required environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")

        # Clear caches to force reload with new env vars
        from backend.deep_agent.config.settings import clear_settings_cache

        clear_settings_cache()

        from backend.deep_agent.main import create_app
        from backend.deep_agent.version import __version__

        app = create_app()
        schema = app.openapi()

        assert schema["info"]["version"] == __version__
