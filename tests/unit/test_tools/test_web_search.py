"""
Unit tests for Web Search Tool.

Tests the LangChain tool wrapper that provides web search capabilities
to agents via the Perplexity MCP client.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.deep_agent.config.settings import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Fixture providing mocked Settings for tool tests."""
    settings = Mock(spec=Settings)
    settings.PERPLEXITY_API_KEY = "test-api-key-12345"
    settings.MCP_PERPLEXITY_TIMEOUT = 30
    settings.ENV = "local"
    return settings


@pytest.fixture
def mock_search_results() -> dict[str, Any]:
    """Fixture providing mock search results from Perplexity client."""
    return {
        "results": [
            {
                "title": "Python Tutorial",
                "url": "https://example.com/python",
                "snippet": "Learn Python programming basics and advanced concepts.",
                "relevance_score": 0.95,
            },
            {
                "title": "Python Documentation",
                "url": "https://docs.python.org",
                "snippet": "Official Python documentation and guides.",
                "relevance_score": 0.92,
            },
        ],
        "query": "python tutorial",
        "sources": 2,
    }


@pytest.fixture
def mock_formatted_results() -> str:
    """Fixture providing formatted search results string."""
    return """Found 2 sources for "python tutorial":

1. Python Tutorial
   https://example.com/python
   Learn Python programming basics and advanced concepts.

2. Python Documentation
   https://docs.python.org
   Official Python documentation and guides.

"""


class TestToolSignature:
    """Test Web Search Tool signature and metadata."""

    @pytest.mark.asyncio
    async def test_tool_is_decorated_with_tool_decorator(self) -> None:
        """Test that web_search is decorated with @tool."""
        from backend.deep_agent.tools.web_search import web_search

        # Tool decorator adds metadata attributes
        assert hasattr(web_search, "name")
        assert hasattr(web_search, "description")
        assert web_search.name == "web_search"

    @pytest.mark.asyncio
    async def test_tool_has_description(self) -> None:
        """Test that tool has descriptive docstring for agent."""
        from backend.deep_agent.tools.web_search import web_search

        assert web_search.description is not None
        assert len(web_search.description) > 20
        assert "search" in web_search.description.lower()

    @pytest.mark.asyncio
    async def test_tool_signature_accepts_query_parameter(self) -> None:
        """Test that tool accepts query parameter."""
        from backend.deep_agent.tools.web_search import web_search

        # Check tool args_schema
        assert "query" in web_search.args_schema.model_fields
        assert web_search.args_schema.model_fields["query"].annotation is str

    @pytest.mark.asyncio
    async def test_tool_signature_accepts_max_results_parameter(self) -> None:
        """Test that tool accepts optional max_results parameter."""
        from backend.deep_agent.tools.web_search import web_search

        # Check tool args_schema
        assert "max_results" in web_search.args_schema.model_fields
        field = web_search.args_schema.model_fields["max_results"]
        assert field.annotation is int
        assert field.default == 5


class TestSearchSuccess:
    """Test successful web search operations."""

    @pytest.mark.asyncio
    async def test_search_with_valid_query_returns_formatted_results(
        self,
        mock_settings: Settings,
        mock_search_results: dict[str, Any],
        mock_formatted_results: str,
    ) -> None:
        """Test that valid search returns formatted results string."""
        from backend.deep_agent.tools.web_search import web_search

        # Mock PerplexityClient
        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value=mock_formatted_results)
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "python tutorial"})

            # Assert
            assert isinstance(result, str)
            assert "Python Tutorial" in result
            assert "https://example.com/python" in result
            mock_client.search.assert_called_once_with(query="python tutorial", max_results=5)
            mock_client.format_results_for_agent.assert_called_once_with(mock_search_results)

    @pytest.mark.asyncio
    async def test_search_with_custom_max_results(
        self,
        mock_settings: Settings,
        mock_search_results: dict[str, Any],
        mock_formatted_results: str,
    ) -> None:
        """Test that max_results parameter is passed to client."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value=mock_formatted_results)
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "python tutorial", "max_results": 10})

            # Assert
            assert isinstance(result, str)
            mock_client.search.assert_called_once_with(query="python tutorial", max_results=10)

    @pytest.mark.asyncio
    async def test_search_with_complex_query(
        self,
        mock_settings: Settings,
        mock_search_results: dict[str, Any],
        mock_formatted_results: str,
    ) -> None:
        """Test search with complex multi-word query."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value="Results")
            MockClient.return_value = mock_client

            # Act
            complex_query = "how to implement async web scraping in Python 3.11"
            result = await web_search.ainvoke({"query": complex_query})

            # Assert
            assert isinstance(result, str)
            mock_client.search.assert_called_once_with(query=complex_query, max_results=5)

    @pytest.mark.asyncio
    async def test_search_initializes_client_with_settings(
        self,
        mock_settings: Settings,
        mock_search_results: dict[str, Any],
    ) -> None:
        """Test that PerplexityClient is initialized with get_settings()."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value="Results")
            MockClient.return_value = mock_client

            # Act
            await web_search.ainvoke({"query": "test query"})

            # Assert - Client was instantiated (settings loaded internally)
            MockClient.assert_called_once()


class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.mark.asyncio
    async def test_search_with_empty_query_returns_error_message(self) -> None:
        """Test that empty query returns user-friendly error."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(side_effect=ValueError("Search query cannot be empty"))
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": ""})

            # Assert
            assert isinstance(result, str)
            assert "error" in result.lower() or "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_connection_error(self) -> None:
        """Test that ConnectionError is handled gracefully."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(
                side_effect=ConnectionError("Failed to connect to MCP server")
            )
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "test query"})

            # Assert
            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "connection" in result.lower() or "connect" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_timeout_error(self) -> None:
        """Test that TimeoutError is handled gracefully."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(side_effect=TimeoutError("Request timed out"))
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "test query"})

            # Assert
            assert isinstance(result, str)
            assert "timeout" in result.lower() or "timed out" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_rate_limit_error(self) -> None:
        """Test that rate limit RuntimeError is handled gracefully."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(
                side_effect=RuntimeError("Rate limit exceeded: 10 requests per 60s")
            )
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "test query"})

            # Assert
            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "rate limit" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_generic_runtime_error(self) -> None:
        """Test that generic RuntimeError is handled gracefully."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(side_effect=RuntimeError("API error occurred"))
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "test query"})

            # Assert
            assert isinstance(result, str)
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_unexpected_exception(self) -> None:
        """Test that unexpected exceptions are caught and logged."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(side_effect=Exception("Unexpected error"))
            MockClient.return_value = mock_client

            # Act
            result = await web_search.ainvoke({"query": "test query"})

            # Assert
            assert isinstance(result, str)
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_search_logs_operations(
        self,
        mock_settings: Settings,
        mock_search_results: dict[str, Any],
    ) -> None:
        """Test that search operations are logged."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value="Results")
            MockClient.return_value = mock_client

            # Patch logger
            with patch("backend.deep_agent.tools.web_search.logger") as mock_logger:
                # Act
                await web_search.ainvoke({"query": "test query"})

                # Assert - Logger was called (info, debug, or error)
                assert mock_logger.info.called or mock_logger.debug.called
