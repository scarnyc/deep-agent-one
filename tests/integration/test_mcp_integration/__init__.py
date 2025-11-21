"""Integration tests for Model Context Protocol (MCP) integrations.

This module tests MCP client implementations that connect to external
services via the MCP standard. Tests verify client behavior, error handling,
and response formatting.

MCP Clients Tested:
    - PerplexityClient: Web search via Perplexity API

Components Tested:
    - Client initialization (API key validation)
    - Search functionality (query processing)
    - Response formatting (agent-consumable format)
    - Error handling (connection, timeout, API errors)
    - Rate limiting (client-side throttling)
    - Query sanitization (XSS prevention, length limits)

Mocking Strategy:
    - Mock _call_mcp internal method (MCP protocol layer)
    - Mock Settings for configuration
    - Real validation logic
    - Real response formatting

Test Coverage:
    - Client creation and configuration
    - Successful searches
    - Input validation (empty queries, special characters)
    - Error scenarios (connection, timeout, API errors)
    - Response parsing and formatting
    - Rate limiting enforcement
    - Query sanitization

Future MCP Integrations:
    - Gmail MCP client
    - Calendar MCP client
    - GitHub MCP client
"""
