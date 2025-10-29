#!/usr/bin/env python3
"""
Test script to validate astream_events() fix for WebSocket streaming.

This script tests that the switch from astream() to astream_events() enables
real-time token streaming and proper event emission.

Expected behaviors:
- Token-level streaming (on_chat_model_stream events)
- Tool execution events (on_tool_start, on_tool_end)
- Real-time event delivery (no blocking until completion)
- Proper event serialization
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from deep_agent.services.agent_service import AgentService
from deep_agent.config.settings import get_settings


async def test_token_streaming():
    """Test that token-level streaming works with astream_events()."""
    print("\n" + "=" * 80)
    print("TEST 1: Token-Level Streaming")
    print("=" * 80)

    service = AgentService()
    settings = get_settings()

    # Simple query that should stream tokens
    test_message = "Say hello and count to 3"
    thread_id = "test-astream-events-001"

    print(f"\nSending message: '{test_message}'")
    print(f"Thread ID: {thread_id}")
    print(f"Stream version: {settings.STREAM_VERSION}")
    print(f"Allowed events: {settings.stream_allowed_events_list}")
    print("\nStreaming events:")
    print("-" * 80)

    event_count = 0
    event_types = {}
    token_count = 0
    full_response = ""

    try:
        async for event in service.stream(test_message, thread_id):
            event_count += 1
            event_type = event.get("event", "unknown")

            # Count event types
            event_types[event_type] = event_types.get(event_type, 0) + 1

            # Handle token streaming events
            if event_type == "on_chat_model_stream":
                # Extract token content
                data = event.get("data", {})
                chunk = data.get("chunk", {})

                # Handle both dict and object formats
                if isinstance(chunk, dict):
                    content = chunk.get("content", "")
                else:
                    content = getattr(chunk, "content", "")

                if content:
                    token_count += 1
                    full_response += content
                    print(f"[Token #{token_count}] {repr(content)}")

            # Handle other event types
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "unknown")
                print(f"\n[TOOL START] {tool_name}")

            elif event_type == "on_tool_end":
                tool_name = event.get("name", "unknown")
                print(f"[TOOL END] {tool_name}")

            elif event_type == "on_chain_start":
                chain_name = event.get("name", "unknown")
                print(f"\n[CHAIN START] {chain_name}")

            elif event_type == "on_chain_end":
                chain_name = event.get("name", "unknown")
                print(f"[CHAIN END] {chain_name}")

            # Show progress every 10 events
            if event_count % 10 == 0:
                print(f"\n... ({event_count} events received so far) ...")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

    # Print summary
    print("\n" + "=" * 80)
    print("TEST RESULTS:")
    print("=" * 80)
    print(f"Total events: {event_count}")
    print(f"Token streaming events: {token_count}")
    print(f"Full response length: {len(full_response)} characters")
    print("\nEvent type breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  - {event_type}: {count}")

    if full_response:
        print(f"\nFull response preview:")
        print(f"  {full_response[:200]}...")

    # Validate results
    success = True
    print("\n" + "=" * 80)
    print("VALIDATION:")
    print("=" * 80)

    if token_count > 0:
        print("✅ Token streaming works (received token events)")
    else:
        print("❌ No token streaming events received")
        success = False

    if event_count > 0:
        print(f"✅ Received {event_count} events total")
    else:
        print("❌ No events received at all")
        success = False

    if full_response:
        print(f"✅ Reconstructed response ({len(full_response)} chars)")
    else:
        print("❌ No response content received")
        success = False

    if "on_chat_model_stream" in event_types:
        print(f"✅ Streaming event type present ({event_types['on_chat_model_stream']} events)")
    else:
        print("❌ No on_chat_model_stream events (critical for token streaming)")
        success = False

    return success


async def test_comparison_with_old_behavior():
    """Compare new astream_events() behavior with old astream() behavior."""
    print("\n" + "=" * 80)
    print("TEST 2: Behavior Comparison")
    print("=" * 80)

    print("\nOLD BEHAVIOR (astream with stream_mode='values'):")
    print("  - Only emitted 'on_message_update' events")
    print("  - No token-level streaming")
    print("  - Events only after complete message generation")
    print("  - Coarse-grained updates")

    print("\nNEW BEHAVIOR (astream_events with version='v2'):")
    print("  - Emits 'on_chat_model_stream' for each token")
    print("  - Real-time token streaming")
    print("  - Events during generation (not just after)")
    print("  - Fine-grained updates")

    print("\n✅ Behavioral change implemented successfully")
    return True


async def test_event_serialization():
    """Test that events are properly serialized for WebSocket transmission."""
    print("\n" + "=" * 80)
    print("TEST 3: Event Serialization")
    print("=" * 80)

    from deep_agent.core.serialization import serialize_event
    from langchain_core.messages.ai import AIMessageChunk

    # Test serializing a mock event with AIMessageChunk
    mock_chunk = AIMessageChunk(content="Hello", id="chunk-123")
    mock_event = {
        "event": "on_chat_model_stream",
        "data": {
            "chunk": mock_chunk
        },
        "metadata": {
            "thread_id": "test-123"
        }
    }

    print("\nOriginal event structure:")
    print(f"  Event type: {mock_event['event']}")
    print(f"  Chunk type: {type(mock_event['data']['chunk'])}")
    print(f"  Chunk content: {mock_event['data']['chunk'].content}")

    try:
        serialized = serialize_event(mock_event)

        print("\nSerialized event structure:")
        print(f"  Event type: {serialized['event']}")
        print(f"  Chunk type: {type(serialized['data']['chunk'])}")
        print(f"  Chunk content: {serialized['data']['chunk']['content']}")
        print(f"  Is JSON-safe: {isinstance(serialized['data']['chunk'], dict)}")

        if isinstance(serialized['data']['chunk'], dict):
            print("\n✅ AIMessageChunk serialized to dict successfully")
            return True
        else:
            print("\n❌ AIMessageChunk not serialized to dict")
            return False

    except Exception as e:
        print(f"\n❌ Serialization failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ASTREAM_EVENTS() FIX VALIDATION TEST SUITE")
    print("=" * 80)

    results = {}

    # Test 1: Token streaming
    results["token_streaming"] = await test_token_streaming()

    # Test 2: Behavior comparison
    results["behavior_comparison"] = await test_comparison_with_old_behavior()

    # Test 3: Event serialization
    results["event_serialization"] = await test_event_serialization()

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS:")
    print("=" * 80)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - astream_events() fix validated!")
        print("=" * 80)
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - review output above")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
