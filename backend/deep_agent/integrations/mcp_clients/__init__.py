"""
Model Context Protocol (MCP) client implementations.

This module provides client implementations for various MCP servers that
enable the agent framework to interact with external services like web search,
data retrieval, and specialized APIs.

MCP standardizes how agents communicate with external tools by providing:
- Unified interface across different service providers
- Async/await patterns for high-performance I/O operations
- Built-in retry logic and error handling
- Standardized request/response formats

Available Clients:
    PerplexityClient: Web search using Perplexity AI's search API

Usage:
    >>> from deep_agent.integrations.mcp_clients import PerplexityClient
    >>>
    >>> client = PerplexityClient()
    >>> results = await client.search("AI agent frameworks")
    >>> formatted = client.format_results_for_agent(results)

See Also:
    - MCP Specification: https://modelcontextprotocol.io/
    - Perplexity MCP: https://github.com/perplexityai/modelcontextprotocol
"""

from deep_agent.integrations.mcp_clients.perplexity import PerplexityClient

__all__ = [
    "PerplexityClient",
]
