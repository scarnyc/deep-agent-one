#!/usr/bin/env python3
"""
Direct test of Perplexity MCP integration (bypasses HITL).

This script tests the Perplexity MCP client directly to verify:
1. MCP subprocess spawns correctly
2. MCP tool is called successfully
3. Real search results are returned from Perplexity API
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from deep_agent.integrations.mcp_clients.perplexity import PerplexityClient


async def test_perplexity_mcp():
    """Test Perplexity MCP client with a real search query."""
    print("=" * 80)
    print("Testing Perplexity MCP Integration")
    print("=" * 80)

    # Create client
    print("\n1. Initializing Perplexity MCP client...")
    client = PerplexityClient()
    print("   ✓ Client initialized")

    # Perform search
    query = "current weather in NYC"
    print(f"\n2. Performing web search: '{query}'")
    print("   (This will spawn MCP subprocess and call Perplexity API)")

    try:
        results = await client.search(query=query, max_results=3)

        print("\n3. Search completed successfully!")
        print(f"   - Query: {results.get('query')}")
        print(f"   - Sources: {results.get('sources')}")
        print(f"   - Results: {len(results.get('results', []))}")

        # Format results
        formatted = client.format_results_for_agent(results)
        print("\n4. Formatted results:")
        print("-" * 80)
        print(formatted)
        print("-" * 80)

        # Extract sources
        sources = client.extract_sources(results)
        print("\n5. Source URLs:")
        for i, url in enumerate(sources, 1):
            print(f"   {i}. {url}")

        print("\n" + "=" * 80)
        print("SUCCESS: Perplexity MCP integration working correctly!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_perplexity_mcp())
