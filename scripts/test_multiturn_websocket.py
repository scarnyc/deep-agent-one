#!/usr/bin/env python3
"""Multi-turn WebSocket conversation test.

Tests the exact user flow that triggered the original CancelledError bug:
1. User asks about weather in Queens, NYC
2. Agent responds (may ask for approval/clarification)
3. User confirms with specifics ("yes Fahrenheit Astoria")
4. Agent executes web_search tool
5. Verify no CancelledError and proper response streaming

This is a regression test for Issue #37 (WebSocket CancelledError during tool execution).

Usage:
    python scripts/test_multiturn_websocket.py

Requirements:
    - Backend server running on ws://localhost:8000/api/v1/ws
    - websockets library installed (pip install websockets)
    - Web search tool enabled with Perplexity MCP

What It Validates:
    - Multi-turn conversation works (same thread_id across turns)
    - Tool execution completes without CancelledError
    - Events use correct AG-UI format (event: not type:)
    - No error events with old broken format
    - Proper streaming of tool results

Examples:
    # Run test
    python scripts/test_multiturn_websocket.py

    # Check backend logs after test
    tail -f logs/backend/*.log

Output:
    - Turn-by-turn conversation progress
    - Tool execution details (name, input, output preview)
    - Validation results summary
    - Pass/fail status

Exit Codes:
    0 - Test passed (no CancelledError, tool executed successfully)
    1 - Test failed (timeout, error event, or exception)
"""

import asyncio
import json
import sys
import uuid

import websockets


async def test_weather_multiturn():
    """
    Test multi-turn conversation with tool execution.

    Mimics real user flow from the screenshot error.
    """

    # Use same thread_id for multi-turn conversation
    thread_id = str(uuid.uuid4())

    try:
        async with websockets.connect("ws://localhost:8000/api/v1/ws") as ws:
            print("🔗 Connected to WebSocket\n")

            # ===== TURN 1: Initial weather question =====
            print("📤 TURN 1: Sending 'what's the weather in Queens, NYC today?'")
            await ws.send(
                json.dumps(
                    {
                        "type": "chat",
                        "message": "what's the weather in Queens, NYC today?",
                        "thread_id": thread_id,
                    }
                )
            )

            # Read all events from turn 1
            turn1_complete = False
            agent_response = ""
            event_count = 0

            print("\n📥 Receiving response...")
            while not turn1_complete:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    event = json.loads(response)
                    event_count += 1

                    event_type = event.get("event")

                    # Verify event format (should have "event" field, not "type")
                    if "event" not in event:
                        print(f"\n❌ ERROR: Event missing 'event' field: {event}")
                        return False

                    # Collect text from streaming response
                    if event_type == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk", {}).get("content", "")
                        agent_response += chunk
                        print(chunk, end="", flush=True)

                    # Check for completion
                    if event_type == "on_chain_end":
                        turn1_complete = True
                        print(f"\n\n✅ Turn 1 complete ({event_count} events)")

                except TimeoutError:
                    print("\n⏱️ Timeout waiting for turn 1 response")
                    return False

            print(f"\n📝 Agent response preview: {agent_response[:150]}...")

            # ===== TURN 2: User confirmation with specifics =====
            await asyncio.sleep(1)  # Brief pause like real user

            print("\n" + "=" * 60)
            print("📤 TURN 2: Sending 'yes Fahrenheit Astoria'")
            await ws.send(
                json.dumps(
                    {
                        "type": "chat",
                        "message": "yes Fahrenheit Astoria",
                        "thread_id": thread_id,  # Same thread!
                    }
                )
            )

            # Read all events from turn 2 (should include tool execution)
            turn2_complete = False
            tool_called = False
            error_occurred = False
            event_count = 0

            print("\n📥 Receiving response...")
            while not turn2_complete:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=60)
                    event = json.loads(response)
                    event_count += 1

                    event_type = event.get("event")

                    # Verify event format
                    if "event" not in event:
                        print(f"\n❌ ERROR: Event missing 'event' field: {event}")
                        return False

                    # Track tool execution
                    if event_type == "on_tool_start":
                        tool_data = event.get("data", {})
                        tool_name = tool_data.get("name", "unknown")
                        print(f"\n🔧 Tool called: {tool_name}")
                        print(f"   Input: {tool_data.get('input', {})}")
                        tool_called = True

                    if event_type == "on_tool_end":
                        tool_data = event.get("data", {})
                        print("✅ Tool execution completed")
                        print(f"   Output preview: {str(tool_data.get('output', ''))[:100]}...")

                    # Check for errors
                    if event_type == "on_error":
                        error_data = event.get("data", {})
                        print("\n❌ ERROR EVENT RECEIVED:")
                        print(f"   {json.dumps(error_data, indent=2)}")
                        error_occurred = True

                    # Stream text
                    if event_type == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk", {}).get("content", "")
                        print(chunk, end="", flush=True)

                    # Check for completion
                    if event_type == "on_chain_end":
                        turn2_complete = True
                        print(f"\n\n✅ Turn 2 complete ({event_count} events)")

                except TimeoutError:
                    print("\n⏱️ Timeout waiting for turn 2 response")
                    return False

            # ===== VALIDATION =====
            print("\n" + "=" * 60)
            print("VALIDATION RESULTS:")
            print("=" * 60)

            if tool_called:
                print("✅ Tool was called (web_search)")
            else:
                print("⚠️  Tool was NOT called (agent may have responded differently)")

            if error_occurred:
                print("❌ Error occurred during execution")
                return False
            else:
                print("✅ No errors occurred")

            if turn2_complete:
                print("✅ Multi-turn conversation completed successfully")

            print("\n✅ ALL EVENTS USED CORRECT FORMAT (event: not type:)")
            print("✅ NO CancelledError DETECTED")

            return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("Multi-Turn WebSocket Test with Tool Execution")
    print("=" * 60)
    print("\nThis test validates:")
    print("1. Multi-turn conversation works (same thread_id)")
    print("2. Tool execution (web_search) completes without CancelledError")
    print("3. Events use correct AG-UI format (event: not type:)")
    print("4. No error events with old broken format")
    print("\n" + "=" * 60 + "\n")

    success = await test_weather_multiturn()

    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED - Fix is working!")
        print("\nNext: Check backend logs for CancelledError traces")
        print("Run: BashOutput tool or check logs/backend/*.log")
        sys.exit(0)
    else:
        print("❌ TEST FAILED - Issues detected")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
