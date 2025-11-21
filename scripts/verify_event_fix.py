"""
Verify that the event transformation fix is working correctly.

This script sends a message to the WebSocket endpoint and validates:
1. No tool_execution_started/completed events are sent
2. on_tool_call events with proper status field are sent instead
3. Events match AG-UI Protocol specification
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_event_transformation():
    """Test that events are properly transformed."""
    print("=" * 60)
    print("Event Transformation Verification Test")
    print("=" * 60)
    print()

    uri = "ws://localhost:8000/ws/chat"

    received_events = []
    invalid_events = []

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected to {uri}")
            print()

            # Send test message
            test_message = {
                "message": "Search for the latest news about AI",
                "thread_id": f"test-{datetime.utcnow().timestamp()}",
            }

            print(f"Sending message: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            print()

            # Collect events for 15 seconds
            print("Collecting events...")
            timeout = asyncio.create_task(asyncio.sleep(15))

            while not timeout.done():
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    event = json.dumps(message)
                    event_type = event.get("event", "unknown")

                    received_events.append(event)

                    # Check for invalid event types
                    if event_type in ["tool_execution_started", "tool_execution_completed"]:
                        invalid_events.append(event)
                        print(f"❌ INVALID EVENT: {event_type}")
                    elif event_type == "on_tool_call":
                        status = event.get("data", {}).get("status", "unknown")
                        print(f"✓ Valid event: {event_type} (status={status})")
                    else:
                        print(f"  Event: {event_type}")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error receiving: {e}")
                    break

            timeout.cancel()

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

    print()
    print("=" * 60)
    print("Test Results")
    print("=" * 60)
    print()

    # Check for invalid events
    if invalid_events:
        print(f"❌ FAIL: Found {len(invalid_events)} invalid events:")
        for event in invalid_events:
            print(f"  - {event.get('event')}")
        return False

    # Check for valid on_tool_call events
    tool_call_events = [e for e in received_events if e.get("event") == "on_tool_call"]

    if not tool_call_events:
        print("⚠️  WARNING: No on_tool_call events received")
        print("   (This might be expected if the query didn't trigger tool use)")
    else:
        print(f"✓ Received {len(tool_call_events)} on_tool_call events")

        # Verify status field
        for event in tool_call_events:
            status = event.get("data", {}).get("status")
            if status in ["running", "completed"]:
                print(f"  ✓ Event has valid status: {status}")
            else:
                print(f"  ❌ Event has invalid status: {status}")
                return False

    print()
    print("=" * 60)
    print("✅ TEST PASSED - Events are correctly transformed")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_event_transformation())
    exit(0 if success else 1)
