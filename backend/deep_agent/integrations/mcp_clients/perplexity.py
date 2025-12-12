"""
Perplexity MCP client for web search capabilities.

Provides integration with Perplexity's Model Context Protocol server
for performing web searches and retrieving real-time information.
"""

import asyncio
import os
import re
import threading
import time
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.logging import get_logger
from deep_agent.core.security import mask_api_key

logger = get_logger(__name__)

# Constants
MOCK_DELAY_SECONDS = 0.01  # For Phase 0 testing
MAX_QUERY_LENGTH = 500  # Prevent DoS attacks
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 10  # 10 requests per minute


class PerplexityClient:
    """
    Client for interacting with Perplexity MCP server.

    Provides async web search capabilities with result formatting
    and error handling for agent consumption.

    Attributes:
        api_key: Perplexity API key for authentication
        timeout: Timeout in seconds for MCP requests
        settings: Configuration settings

    Example:
        >>> client = PerplexityClient()
        >>> results = await client.search("python machine learning")
        >>> formatted = client.format_results_for_agent(results)
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize Perplexity MCP client with rate limiting and security.

        Args:
            settings: Configuration settings. If None, uses get_settings().

        Raises:
            ValueError: If PERPLEXITY_API_KEY is not configured.
        """
        if settings is None:
            settings = get_settings()

        self.settings = settings
        self.api_key = settings.PERPLEXITY_API_KEY
        self.timeout = settings.MCP_PERPLEXITY_TIMEOUT

        # Validate API key
        if not self.api_key:
            logger.error("Perplexity API key is missing")
            raise ValueError("Perplexity API key is required")

        # Rate limiting state (in-memory for Phase 0, Redis for Phase 1+)
        self._request_timestamps: list[float] = []
        self._rate_limit_window = RATE_LIMIT_WINDOW
        self._rate_limit_max = RATE_LIMIT_MAX_REQUESTS
        self._rate_limit_lock = threading.Lock()  # Thread-safe rate limiting

        # Mask API key for logging (security: HIGH-2 fix)
        masked_key = mask_api_key(self.api_key)

        logger.info(
            "Perplexity MCP client initialized",
            api_key_masked=masked_key,
            timeout=self.timeout,
            rate_limit=f"{self._rate_limit_max}/{self._rate_limit_window}s",
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Perform web search using Perplexity MCP with rate limiting and security.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Dictionary containing search results with structure:
            {
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "snippet": str,
                        "relevance_score": float
                    },
                    ...
                ],
                "query": str,
                "sources": int
            }

        Raises:
            ValueError: If query is empty or results format is invalid
            ConnectionError: If MCP server connection fails
            TimeoutError: If request exceeds timeout
            RuntimeError: If Perplexity API returns an error or rate limit exceeded

        Example:
            >>> results = await client.search("climate change impacts")
            >>> print(f"Found {results['sources']} sources")
        """
        # Validate query
        if not query or not query.strip():
            logger.warning("Search called with empty query")
            raise ValueError("Search query cannot be empty")

        query = query.strip()

        # Rate limiting check (security: HIGH-1 fix)
        self._check_rate_limit(query)

        # Sanitize query (security: MEDIUM-2 fix)
        query = self._sanitize_query(query)

        logger.info(
            "Performing Perplexity search",
            query=query,
            max_results=max_results,
        )

        try:
            # Call MCP server with retry logic
            response = await self._call_mcp(query, max_results)

            # Validate response format
            if not isinstance(response, dict) or "results" not in response:
                logger.error(
                    "Invalid response format from Perplexity",
                    response=response,
                )
                raise ValueError("Invalid response format from Perplexity")

            logger.info(
                "Search completed successfully",
                query=query,
                result_count=len(response.get("results", [])),
            )

            return response

        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.error(
                "Search failed",
                query=query,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _check_rate_limit(self, query: str) -> None:
        """
        Check if request is within rate limits (thread-safe).

        Args:
            query: Search query for logging

        Raises:
            RuntimeError: If rate limit is exceeded
        """
        with self._rate_limit_lock:
            now = time.time()

            # Remove timestamps outside the window
            self._request_timestamps = [
                ts for ts in self._request_timestamps if now - ts < self._rate_limit_window
            ]

            # Check if limit exceeded
            if len(self._request_timestamps) >= self._rate_limit_max:
                logger.warning(
                    "Rate limit exceeded for Perplexity search",
                    query=query,
                    requests_in_window=len(self._request_timestamps),
                    limit=self._rate_limit_max,
                )
                raise RuntimeError(
                    f"Rate limit exceeded: {self._rate_limit_max} requests per "
                    f"{self._rate_limit_window}s"
                )

            # Add current timestamp
            self._request_timestamps.append(now)
            logger.debug(
                "Rate limit check passed",
                requests_in_window=len(self._request_timestamps),
                limit=self._rate_limit_max,
            )

    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize search query to prevent injection attacks.

        Args:
            query: Raw search query

        Returns:
            Sanitized query safe for API consumption
        """
        # Remove potentially dangerous characters
        # Keep alphanumeric, spaces, basic punctuation
        sanitized = re.sub(r"[^\w\s\-.,?!']", "", query)

        # Limit length to prevent DoS
        if len(sanitized) > MAX_QUERY_LENGTH:
            logger.warning(
                "Query truncated to max length",
                original_length=len(sanitized),
                max_length=MAX_QUERY_LENGTH,
            )
            sanitized = sanitized[:MAX_QUERY_LENGTH]

        return sanitized.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def _call_mcp(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        """
        Call Perplexity MCP server with retry logic and timeout enforcement.

        Retries up to 3 times with exponential backoff for:
        - ConnectionError: Network issues
        - TimeoutError: Request timeouts

        Does NOT retry RuntimeError (API errors like rate limits).

        This is a private method that handles the actual MCP protocol
        communication. In Phase 0, this is a placeholder that should be
        replaced with actual MCP client implementation.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            Raw response from MCP server

        Raises:
            ConnectionError: If MCP connection fails after retries
            TimeoutError: If request times out after retries
            RuntimeError: If API returns an error
        """
        logger.debug(
            "MCP call placeholder",
            query=query,
            max_results=max_results,
            timeout=self.timeout,
        )

        try:
            # Enforce timeout (security: MEDIUM-3 fix)
            async with asyncio.timeout(self.timeout):
                # Server configuration from .mcp.json (root)
                # Use the installed console script directly (perplexity-mcp package doesn't have __main__.py)
                # See regression test: TestPerplexityMCPServerConfiguration (trace f4a77df6)
                server_params = StdioServerParameters(
                    command="perplexity-mcp",
                    args=[],
                    env={
                        **os.environ,  # Inherit PATH and other env vars
                        "PERPLEXITY_API_KEY": self.api_key,
                        "PERPLEXITY_MODEL": os.getenv("PERPLEXITY_MODEL", "sonar"),
                    },
                )

                logger.debug(
                    "Connecting to Perplexity MCP server",
                    query=query,
                    max_results=max_results,
                )

                # Connect to MCP server via stdio
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        # Initialize MCP session
                        await session.initialize()

                        logger.debug("MCP session initialized, calling tool")

                        # Call perplexity_search_web tool
                        result = await session.call_tool(
                            name="perplexity_search_web",
                            arguments={
                                "query": query,
                                "recency": "month",  # Default: last 30 days
                            },
                        )

                        # Parse result
                        if not result.content or len(result.content) == 0:
                            logger.warning("MCP tool returned empty content")
                            return {
                                "results": [],
                                "query": query,
                                "sources": 0,
                            }

                        # Extract text content from MCP response
                        text_response = result.content[0].text

                        logger.info(
                            "MCP tool call successful",
                            query=query,
                            response_length=len(text_response),
                        )

                        # Parse Perplexity response
                        return self._parse_perplexity_response(text_response, query)

        except TimeoutError as e:
            logger.error(
                "MCP request timed out",
                query=query,
                timeout=self.timeout,
            )
            raise TimeoutError(f"MCP request exceeded {self.timeout}s timeout") from e

        except Exception as e:
            # Handle ExceptionGroup (Python 3.11+) which wraps actual errors from TaskGroup
            error_msg = str(e)
            actual_error = e

            # ExceptionGroup contains the real errors as sub-exceptions
            if isinstance(e, ExceptionGroup):
                if e.exceptions:
                    actual_error = e.exceptions[0]
                    error_msg = f"{type(actual_error).__name__}: {actual_error}"

            if hasattr(actual_error, "__cause__") and actual_error.__cause__:
                error_msg += f" (caused by: {actual_error.__cause__})"

            logger.error(
                "MCP call failed",
                query=query,
                error=error_msg,
                error_type=type(actual_error).__name__,
                command="perplexity-mcp",
            )
            raise ConnectionError(
                f"Failed to connect to Perplexity MCP: {error_msg}. "
                f"Ensure 'perplexity-mcp' is installed and PERPLEXITY_API_KEY is set."
            ) from actual_error

    def _parse_perplexity_response(
        self,
        text: str,
        query: str,
    ) -> dict[str, Any]:
        """
        Parse Perplexity text response into structured results.

        The perplexity_mcp server returns text with citations in format:

        <main content>

        Citations:
        [1] https://example.com/source1
        [2] https://example.com/source2

        Args:
            text: Raw text response from Perplexity MCP
            query: Original search query

        Returns:
            Dictionary with structured results and citations
        """
        lines = text.split("\n")

        # Find where citations start
        citations_start = None
        for i, line in enumerate(lines):
            if line.strip().lower() == "citations:":
                citations_start = i + 1
                break

        # Extract main content and citations
        if citations_start:
            content = "\n".join(lines[: citations_start - 1]).strip()
            citation_lines = lines[citations_start:]
        else:
            content = text.strip()
            citation_lines = []

        # Parse citations
        sources = []
        for line in citation_lines:
            line = line.strip()
            if line.startswith("[") and "]" in line:
                # Format: [1] https://example.com
                url = line.split("]", 1)[1].strip()
                sources.append(url)

        # Create single result with all content
        results = [
            {
                "title": f"Perplexity Search: {query[:50]}",
                "url": sources[0] if sources else "",
                "snippet": content,
                "relevance_score": 1.0,
            }
        ]

        return {
            "results": results,
            "query": query,
            "sources": len(sources),
        }

    def format_results_for_agent(self, results: dict[str, Any]) -> str:
        """
        Format search results for agent consumption.

        Converts structured search results into a readable string format
        that agents can easily parse and present to users.

        Args:
            results: Search results dictionary from search()

        Returns:
            Formatted string with numbered results

        Example:
            >>> formatted = client.format_results_for_agent(results)
            >>> print(formatted)
            Found 3 sources for "python tutorial":

            1. Learn Python Programming
               https://example.com/python
               A comprehensive guide to Python...

            2. ...
        """
        query = results.get("query", "")
        search_results = results.get("results", [])
        source_count = results.get("sources", 0)

        if not search_results:
            return f'No results found for "{query}"'

        lines = [f'Found {source_count} sources for "{query}":', ""]

        for idx, result in enumerate(search_results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            snippet = result.get("snippet", "")

            lines.append(f"{idx}. {title}")
            lines.append(f"   {url}")
            if snippet:
                lines.append(f"   {snippet}")
            lines.append("")  # Blank line between results

        return "\n".join(lines)

    def extract_sources(self, results: dict[str, Any]) -> list[str]:
        """
        Extract source URLs from search results.

        Useful for creating citation lists or tracking information provenance.

        Args:
            results: Search results dictionary from search()

        Returns:
            List of source URLs

        Example:
            >>> sources = client.extract_sources(results)
            >>> print(sources)
            ['https://example.com/1', 'https://example.com/2']
        """
        search_results = results.get("results", [])
        return [result.get("url", "") for result in search_results if result.get("url")]
