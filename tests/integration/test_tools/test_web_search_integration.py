"""Integration tests for Web Search Tool.

Tests real tool invocation, error handling, and MCP client integration.
Focuses on business logic and real behavior, not trivial signature checks.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest


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


class TestWebSearchExecution:
    """Test successful web search execution with MCP client."""

    @pytest.mark.asyncio
    async def test_search_executes_and_formats_results(
        self,
        mock_search_results: dict[str, Any],
        mock_formatted_results: str,
    ) -> None:
        """Test that search executes via MCP client and returns formatted results."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value=mock_formatted_results)
            MockClient.return_value = mock_client

            # Execute search
            result = await web_search.ainvoke({"query": "python tutorial"})

            # Verify execution flow
            assert isinstance(result, str)
            assert "Python Tutorial" in result
            assert "https://example.com/python" in result
            mock_client.search.assert_called_once_with(query="python tutorial", max_results=5)
            mock_client.format_results_for_agent.assert_called_once_with(mock_search_results)

    @pytest.mark.asyncio
    async def test_search_passes_custom_max_results_parameter(
        self,
        mock_search_results: dict[str, Any],
        mock_formatted_results: str,
    ) -> None:
        """Test that max_results parameter flows through to MCP client."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value=mock_formatted_results)
            MockClient.return_value = mock_client

            # Execute with custom max_results
            result = await web_search.ainvoke({"query": "python tutorial", "max_results": 10})

            assert isinstance(result, str)
            mock_client.search.assert_called_once_with(query="python tutorial", max_results=10)

    @pytest.mark.asyncio
    async def test_search_handles_complex_query(
        self,
        mock_search_results: dict[str, Any],
    ) -> None:
        """Test search with complex multi-word query."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value="Results")
            MockClient.return_value = mock_client

            # Execute complex query
            complex_query = "how to implement async web scraping in Python 3.11"
            result = await web_search.ainvoke({"query": complex_query})

            assert isinstance(result, str)
            mock_client.search.assert_called_once_with(query=complex_query, max_results=5)


class TestWebSearchErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.mark.asyncio
    async def test_search_handles_empty_query_error(self) -> None:
        """Test that empty query returns user-friendly error."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(side_effect=ValueError("Search query cannot be empty"))
            MockClient.return_value = mock_client

            result = await web_search.ainvoke({"query": ""})

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

            result = await web_search.ainvoke({"query": "test query"})

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

            result = await web_search.ainvoke({"query": "test query"})

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

            result = await web_search.ainvoke({"query": "test query"})

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

            result = await web_search.ainvoke({"query": "test query"})

            assert isinstance(result, str)
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_unexpected_exception(self) -> None:
        """Test that unexpected exceptions are caught and returned as error messages."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(side_effect=Exception("Unexpected error"))
            MockClient.return_value = mock_client

            result = await web_search.ainvoke({"query": "test query"})

            assert isinstance(result, str)
            assert "error" in result.lower()


class TestWebSearchLogging:
    """Test logging behavior during search operations."""

    @pytest.mark.asyncio
    async def test_search_logs_operations(
        self,
        mock_search_results: dict[str, Any],
    ) -> None:
        """Test that search operations are logged for observability."""
        from backend.deep_agent.tools.web_search import web_search

        with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=mock_search_results)
            mock_client.format_results_for_agent = Mock(return_value="Results")
            MockClient.return_value = mock_client

            # Patch logger to verify logging
            with patch("backend.deep_agent.tools.web_search.logger") as mock_logger:
                await web_search.ainvoke({"query": "test query"})

                # Verify logger was called (info, debug, or error)
                assert mock_logger.info.called or mock_logger.debug.called
