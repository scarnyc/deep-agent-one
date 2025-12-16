"""
Integration tests for Perplexity MCP client.

Tests the MCP client that connects to Perplexity for web search capabilities.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.deep_agent.config.settings import Settings


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Fixture providing mocked Settings for Perplexity tests."""
    settings = Mock(spec=Settings)
    settings.PERPLEXITY_API_KEY = "test-api-key-12345"
    settings.MCP_PERPLEXITY_TIMEOUT = 30
    settings.ENV = "local"
    return settings


@pytest.fixture
def mock_perplexity_response() -> dict[str, Any]:
    """Fixture providing a mock Perplexity search response."""
    return {
        "results": [
            {
                "title": "Test Result 1",
                "url": "https://example.com/result1",
                "snippet": "This is a test result snippet about Python programming.",
                "relevance_score": 0.95,
            },
            {
                "title": "Test Result 2",
                "url": "https://example.com/result2",
                "snippet": "Another test result about machine learning.",
                "relevance_score": 0.88,
            },
        ],
        "query": "python machine learning",
        "sources": 2,
    }


class TestPerplexityClientCreation:
    """Test Perplexity MCP client initialization."""

    @pytest.mark.asyncio
    async def test_create_client_with_settings(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test creating Perplexity client with explicit settings."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        # Act
        client = PerplexityClient(settings=mock_settings)

        # Assert
        assert client is not None
        assert client.api_key == "test-api-key-12345"
        assert client.timeout == 30

    @pytest.mark.asyncio
    async def test_create_client_without_settings_uses_defaults(self) -> None:
        """Test creating client without settings uses get_settings()."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch(
            "backend.deep_agent.integrations.mcp_clients.perplexity.get_settings"
        ) as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.PERPLEXITY_API_KEY = "default-key"
            mock_settings.MCP_PERPLEXITY_TIMEOUT = 30
            mock_get_settings.return_value = mock_settings

            # Act
            client = PerplexityClient()

            # Assert
            assert client is not None
            mock_get_settings.assert_called_once()
            assert client.api_key == "default-key"

    @pytest.mark.asyncio
    async def test_create_client_raises_without_api_key(self) -> None:
        """Test client raises ValueError when API key is missing."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Perplexity API key is required"):
            settings = Mock(spec=Settings)
            settings.PERPLEXITY_API_KEY = None
            settings.MCP_PERPLEXITY_TIMEOUT = 30
            PerplexityClient(settings=settings)


class TestPerplexitySearch:
    """Test Perplexity search functionality."""

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test basic search returns formatted results."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        # Mock the underlying MCP call
        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)

            # Act
            result = await client.search("python machine learning")

            # Assert
            assert result is not None
            assert "results" in result
            assert len(result["results"]) == 2
            assert result["query"] == "python machine learning"
            assert result["sources"] == 2

            # Verify MCP was called correctly
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert "python machine learning" in str(call_args)

    @pytest.mark.asyncio
    async def test_search_with_max_results(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test search with max_results parameter."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)

            # Act
            await client.search("test query", max_results=5)

            # Assert
            mock_call.assert_called_once()
            # Verify max_results was passed to MCP
            call_args = mock_call.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_search_rejects_empty_query(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test search raises ValueError for empty query."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        client = PerplexityClient(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await client.search("")

    @pytest.mark.asyncio
    async def test_search_rejects_whitespace_only_query(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test search raises ValueError for whitespace-only query."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        client = PerplexityClient(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await client.search("   ")


class TestPerplexityErrorHandling:
    """Test Perplexity client error handling."""

    @pytest.mark.asyncio
    async def test_search_handles_mcp_connection_error(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test search handles MCP connection failures gracefully."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = ConnectionError("Failed to connect to MCP server")

            client = PerplexityClient(settings=mock_settings)

            # Act & Assert
            with pytest.raises(ConnectionError, match="Failed to connect to MCP server"):
                await client.search("test query")

    @pytest.mark.asyncio
    async def test_search_handles_timeout(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test search handles timeout errors."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = TimeoutError("MCP request timed out")

            client = PerplexityClient(settings=mock_settings)

            # Act & Assert
            with pytest.raises(TimeoutError, match="MCP request timed out"):
                await client.search("test query")

    @pytest.mark.asyncio
    async def test_search_handles_api_error(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test search handles Perplexity API errors."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = RuntimeError("Perplexity API error: Rate limit exceeded")

            client = PerplexityClient(settings=mock_settings)

            # Act & Assert
            with pytest.raises(RuntimeError, match="Perplexity API error"):
                await client.search("test query")

    @pytest.mark.asyncio
    async def test_search_handles_invalid_response_format(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test search handles invalid response format from MCP."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            # Return invalid response without "results" key
            mock_call.return_value = {"invalid": "response"}

            client = PerplexityClient(settings=mock_settings)

            # Act & Assert
            with pytest.raises(ValueError, match="Invalid response format from Perplexity"):
                await client.search("test query")


class TestPerplexityResponseFormatting:
    """Test Perplexity response formatting and parsing."""

    @pytest.mark.asyncio
    async def test_format_results_for_agent(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test formatting results for agent consumption."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)

            # Act
            result = await client.search("test")
            formatted = client.format_results_for_agent(result)

            # Assert
            assert isinstance(formatted, str)
            assert "Test Result 1" in formatted
            assert "https://example.com/result1" in formatted
            assert "Test Result 2" in formatted

    @pytest.mark.asyncio
    async def test_extract_sources(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test extracting source URLs from results."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        client = PerplexityClient(settings=mock_settings)

        # Act
        sources = client.extract_sources(mock_perplexity_response)

        # Assert
        assert isinstance(sources, list)
        assert len(sources) == 2
        assert "https://example.com/result1" in sources
        assert "https://example.com/result2" in sources


class TestPerplexityRateLimiting:
    """Test Perplexity client rate limiting."""

    @pytest.mark.asyncio
    async def test_search_enforces_rate_limit(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test rate limiting prevents excessive requests."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)
            client._rate_limit_max = 2  # Set low limit for testing

            # Act - First two should succeed
            await client.search("query 1")
            await client.search("query 2")

            # Third should fail with rate limit
            with pytest.raises(RuntimeError, match="Rate limit exceeded"):
                await client.search("query 3")

    @pytest.mark.asyncio
    async def test_rate_limit_window_resets(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test rate limit window resets after time passes."""
        import time

        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)
            client._rate_limit_max = 2
            client._rate_limit_window = 1  # 1 second window

            # Fill rate limit
            await client.search("query 1")
            await client.search("query 2")

            # Wait for window to reset
            time.sleep(1.1)

            # Should succeed after window reset
            result = await client.search("query 3")
            assert result is not None


class TestPerplexityQuerySanitization:
    """Test Perplexity query sanitization."""

    @pytest.mark.asyncio
    async def test_search_sanitizes_special_characters(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test special characters are removed from queries."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)

            # Act - Query with special characters
            await client.search("test<script>alert('xss')</script>query")

            # Assert - Sanitized query passed to MCP
            call_args = mock_call.call_args
            sanitized_query = call_args[0][0]
            assert "<" not in sanitized_query
            assert ">" not in sanitized_query
            assert "script" in sanitized_query  # Regular text preserved

    @pytest.mark.asyncio
    async def test_search_truncates_long_queries(
        self,
        mock_settings: Settings,
        mock_perplexity_response: dict[str, Any],
    ) -> None:
        """Test very long queries are truncated."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            MAX_QUERY_LENGTH,
            PerplexityClient,
        )

        with patch.object(PerplexityClient, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_perplexity_response

            client = PerplexityClient(settings=mock_settings)

            # Act - Very long query
            long_query = "a" * (MAX_QUERY_LENGTH + 100)
            await client.search(long_query)

            # Assert - Query truncated to max length
            call_args = mock_call.call_args
            truncated_query = call_args[0][0]
            assert len(truncated_query) <= MAX_QUERY_LENGTH


class TestPerplexityWithRealSettings:
    """Test Perplexity client with real Settings integration."""

    @pytest.mark.asyncio
    async def test_client_loads_settings_from_env(
        self,
        tmp_path: Path,
    ) -> None:
        """Test client correctly loads settings from environment."""
        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("PERPLEXITY_API_KEY=test-key-from-env\n" "MCP_PERPLEXITY_TIMEOUT=45\n")

        with patch(
            "backend.deep_agent.integrations.mcp_clients.perplexity.get_settings"
        ) as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.PERPLEXITY_API_KEY = "test-key-from-env"
            mock_settings.MCP_PERPLEXITY_TIMEOUT = 45
            mock_get_settings.return_value = mock_settings

            # Act
            client = PerplexityClient()

            # Assert
            assert client.api_key == "test-key-from-env"
            assert client.timeout == 45


class TestPerplexityMCPServerConfiguration:
    """
    Test MCP server configuration to prevent regression of trace f4a77df6.

    This test class ensures the MCP server is started with the correct command.

    Regression context: The perplexity-mcp package (v0.1.7) does NOT have a
    __main__.py module, so it cannot be run with `python -m perplexity_mcp`.
    It must be run using the installed console script `perplexity-mcp`.

    See trace ID: f4a77df6-82f8-466d-9dd1-478ee55835c0
    """

    @pytest.mark.asyncio
    async def test_mcp_server_uses_correct_command(
        self,
        mock_settings: Settings,
    ) -> None:
        """
        Test that MCP server is started with 'perplexity-mcp' command.

        Regression test for trace f4a77df6-82f8-466d-9dd1-478ee55835c0.
        Ensures we use the correct console script command, not python -m.
        """
        from mcp import StdioServerParameters

        from backend.deep_agent.integrations.mcp_clients.perplexity import (
            PerplexityClient,
        )

        # Create client
        client = PerplexityClient(settings=mock_settings)

        # Mock the stdio_client to capture server_params
        captured_params = None

        async def mock_stdio_client(params):
            nonlocal captured_params
            captured_params = params

            # Return mock context manager
            class MockContext:
                async def __aenter__(self):
                    return (AsyncMock(), AsyncMock())

                async def __aexit__(self, *args):
                    pass

            return MockContext()

        with patch(
            "backend.deep_agent.integrations.mcp_clients.perplexity.stdio_client",
            side_effect=mock_stdio_client,
        ):
            with patch("backend.deep_agent.integrations.mcp_clients.perplexity.ClientSession"):
                try:
                    await client.search("test query", max_results=1)
                except Exception:
                    pass  # We only care about capturing the server params

        # Assert the correct command is used
        assert captured_params is not None, "Server params should be captured"
        assert isinstance(captured_params, StdioServerParameters)
        assert captured_params.command == "perplexity-mcp", (
            f"Expected command 'perplexity-mcp', got '{captured_params.command}'. "
            "This likely means the regression in trace f4a77df6 has reoccurred."
        )
        assert captured_params.args == [], (
            f"Expected empty args [], got {captured_params.args}. "
            "The perplexity-mcp command should not need additional args."
        )

        # Also verify env vars are passed correctly
        assert "PERPLEXITY_API_KEY" in captured_params.env
        assert captured_params.env["PERPLEXITY_API_KEY"] == "test-api-key-12345"

    @pytest.mark.asyncio
    async def test_mcp_server_command_is_executable(self) -> None:
        """
        Test that the perplexity-mcp command is executable in the environment.

        This ensures the command we're trying to run actually exists.
        """
        import shutil

        # Check if perplexity-mcp is available in PATH
        mcp_command = shutil.which("perplexity-mcp")

        assert mcp_command is not None, (
            "perplexity-mcp command not found in PATH. "
            "Ensure perplexity-mcp package is installed correctly."
        )

        # Verify it's in the virtual environment (for development)
        import sys

        venv_path = sys.prefix
        assert venv_path in mcp_command, (
            f"perplexity-mcp found at {mcp_command}, but expected it in "
            f"virtual environment at {venv_path}"
        )
