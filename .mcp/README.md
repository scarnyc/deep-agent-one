# MCP Server Configuration

This directory contains configuration files for Model Context Protocol (MCP) servers used by Deep Agent AGI.

**Note:** Playwright is NOT an MCP server - it's used for UI testing only (via `@playwright/test`). See `tests/ui/` directory for Playwright test setup.

## Available MCP Servers

### Perplexity MCP
- **File:** `perplexity.json`
- **Purpose:** Web search capabilities without leaving the MCP ecosystem
- **Command:** `python -m perplexity_mcp`
- **Setup:**
  ```bash
  pip install perplexity-mcp
  # Set PERPLEXITY_API_KEY in .env file
  ```

## Configuration Format

Each MCP server configuration follows this schema:
```json
{
  "name": "server-name",
  "command": "executable",
  "args": ["arg1", "arg2"],
  "env": {
    "ENV_VAR": "value"
  },
  "description": "Server description"
}
```

## Usage

MCP servers are automatically loaded by the Deep Agent framework during initialization. Ensure all required dependencies are installed and environment variables are set in your `.env` file.

## Adding Custom MCP Servers

To add a new MCP server:
1. Create a new JSON file in this directory (e.g., `custom-server.json`)
2. Follow the configuration format above
3. Install any required dependencies
4. Restart the agent framework to load the new server

## Phase 2: Custom MCP Development

In Phase 2, we will build custom MCP servers using `fastmcp` for research-specific tools and multi-source data aggregation.
