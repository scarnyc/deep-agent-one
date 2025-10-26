"""
Web Search Tool for DeepAgents.

Provides web search capabilities to agents via the Perplexity MCP client.
"""

from langchain_core.tools import tool

from backend.deep_agent.core.logging import get_logger
from backend.deep_agent.integrations.mcp_clients.perplexity import PerplexityClient

logger = get_logger(__name__)


@tool
async def web_search(
    query: str,
    max_results: int = 5,
) -> str:
    """
    Search the web for information using Perplexity MCP.

    Performs a web search and returns formatted results with titles, URLs,
    and snippets. Useful for finding current information, research, fact-checking,
    and answering questions that require up-to-date knowledge.

    Args:
        query: The search query string (e.g., "Python async programming tutorial")
        max_results: Maximum number of search results to return (default: 5)

    Returns:
        Formatted string with search results including titles, URLs, and snippets.
        Returns error message string if search fails.

    Example:
        >>> results = await web_search("latest AI research papers")
        >>> print(results)
        Found 5 sources for "latest AI research papers":

        1. AI Research Papers 2024
           https://example.com/ai-papers
           Latest breakthroughs in artificial intelligence...

    Note:
        - Queries are automatically sanitized for security
        - Rate limiting: 10 requests per minute (raises error if exceeded)
        - Timeout: 30 seconds (configurable)
        - Retries automatically on transient failures (3 attempts with exponential backoff)
    """
    logger.info("Web search tool invoked", query=query, max_results=max_results)

    try:
        # Initialize Perplexity client with settings
        client = PerplexityClient()

        logger.debug(
            "Calling Perplexity MCP client",
            query=query,
            max_results=max_results,
        )

        # Perform search
        results = await client.search(query=query, max_results=max_results)

        logger.info(
            "Search completed successfully",
            query=query,
            result_count=len(results.get("results", [])),
            sources=results.get("sources", 0),
        )

        # Format results for agent consumption
        formatted_results = client.format_results_for_agent(results)

        logger.debug(
            "Returning formatted results to agent",
            result_length=len(formatted_results),
            query=query,
        )

        return formatted_results

    except ValueError as e:
        # Handle empty query or validation errors
        error_msg = f"Search error: {str(e)}"
        logger.warning(
            "Search validation failed",
            query=query,
            error=str(e),
        )
        return error_msg

    except ConnectionError as e:
        # Handle MCP connection failures
        error_msg = f"Connection error: Unable to connect to search service. {str(e)}"
        logger.error(
            "Search connection failed",
            query=query,
            error=str(e),
        )
        return error_msg

    except TimeoutError as e:
        # Handle request timeouts
        error_msg = f"Search timeout: Request took too long. {str(e)}"
        logger.error(
            "Search timed out",
            query=query,
            error=str(e),
        )
        return error_msg

    except RuntimeError as e:
        # Handle API errors (rate limits, API failures)
        error_str = str(e)
        if "rate limit" in error_str.lower():
            error_msg = f"Rate limit error: Too many searches. Please try again later. {error_str}"
        else:
            error_msg = f"Search API error: {error_str}"

        logger.error(
            "Search runtime error",
            query=query,
            error=error_str,
            is_rate_limit="rate limit" in error_str.lower(),
        )
        return error_msg

    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected search error: {str(e)}"
        logger.error(
            "Unexpected error during search",
            query=query,
            error=str(e),
            error_type=type(e).__name__,
        )
        return error_msg
