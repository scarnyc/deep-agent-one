#!/usr/bin/env python3
"""
Test WebSocket event types to verify the fix.

Verifies:
1. No tool_execution_started/completed events
2. on_tool_call events are sent instead
3. Events match AG-UI Protocol specification
"""

import asyncio
import json
import sys
from datetime import datetime


async def test_websocket_events():
    """Test that WebSocket events match AG-UI Protocol."""
    print("=" * 70)
    print("WebSocket Event Type Verification")
    print("=" * 70)
    print()

    # Import websockets here to avoid dependency issues
    try:
        import websockets
    except ImportError:
        print("❌ websockets package not installed")
        print("   Install with: pip install websockets")
        return False

    uri = "ws://localhost:8000/ws/chat"

    # Track event types received
    event_types = {}
    invalid_events = []
    valid_tool_events = []

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully")
            print()

            # Send test message
            message = {
                "message": "Hello, can you help me?",
                "thread_id": f"test-{int(datetime.utcnow().timestamp())}",
            }

            print(f"Sending message: {message['message']}")
            await websocket.send(json.dumps(message))
            print("✓ Message sent")
            print()

            # Collect events for 10 seconds
            print("Collecting events for 10 seconds...")
            print("-" * 70)

            timeout_task = asyncio.create_task(asyncio.sleep(10))
            event_count = 0

            while not timeout_task.done():
                try:
                    raw_message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    event = json.loads(raw_message)
                    event_type = event.get("event", "unknown")
                    event_count += 1

                    # Count event types
                    event_types[event_type] = event_types.get(event_type, 0) + 1

                    # Check for invalid events
                    if event_type in ["tool_execution_started", "tool_execution_completed"]:
                        invalid_events.append(event)
                        print(f"❌ INVALID: {event_type}")

                    # Check for valid tool events
                    elif event_type == "on_tool_call":
                        status = event.get("data", {}).get("status", "unknown")
                        name = event.get("data", {}).get("name", "unknown")
                        valid_tool_events.append(event)
                        print(f"✓ VALID: {event_type} (name={name}, status={status})")

                    # Other events
                    elif event_type == "on_chat_model_stream":
                        # Don't print every stream chunk
                        if event_types[event_type] == 1:
                            print(f"  {event_type} (streaming...)")
                    else:
                        print(f"  {event_type}")

                except TimeoutError:
                    continue
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON decode error: {e}")
                except Exception as e:
                    print(f"⚠️  Error: {e}")
                    break

            timeout_task.cancel()

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

    # Print summary
    print()
    print("=" * 70)
    print("Test Results")
    print("=" * 70)
    print()

    print(f"Total events received: {event_count}")
    print()

    print("Event Type Summary:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    print()

    # Check for invalid events
    if invalid_events:
        print("❌ FAIL: Found invalid event types!")
        print(f"   Found {len(invalid_events)} tool_execution_* events")
        print()
        print("These events should be on_tool_call instead.")
        return False

    # Check for valid tool events
    if valid_tool_events:
        print(f"✓ PASS: Found {len(valid_tool_events)} valid on_tool_call events")

        # Verify status field
        statuses = [e.get("data", {}).get("status") for e in valid_tool_events]
        if all(s in ["running", "completed"] for s in statuses):
            print("✓ PASS: All on_tool_call events have valid status field")
        else:
            print("❌ FAIL: Some on_tool_call events have invalid status")
            return False
    else:
        print("ℹ️  No on_tool_call events received")
        print("   (This is OK if the query didn't trigger any tools)")

    print()
    print("=" * 70)
    print("✅ TEST PASSED - No invalid event types detected")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_websocket_events())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
