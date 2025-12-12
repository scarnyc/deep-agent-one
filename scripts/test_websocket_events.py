#!/usr/bin/env python3
"""
Test WebSocket event streaming to validate on_chat_model_end events.

This script:
1. Connects to the WebSocket endpoint
2. Sends a test message
3. Monitors all events received
4. Validates that on_chat_model_end events are present
"""

import asyncio
import json
import sys
from datetime import datetime

import websockets


async def test_websocket_events():
    """Test WebSocket event streaming."""
    uri = "ws://localhost:8000/api/v1/ws"

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to {uri}...")

    events_received = []

    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Connected")

            # Send test message
            test_message = {
                "type": "chat",
                "message": "What is 2+2?",
                "thread_id": "test-validation-thread",
                "request_id": "test-validation-request",
            }

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending test message...")
            await websocket.send(json.dumps(test_message))
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Message sent\n")

            print("=" * 80)
            print("MONITORING EVENTS (press Ctrl+C to stop)")
            print("=" * 80)

            # Monitor events
            async for message in websocket:
                try:
                    event = json.loads(message)
                    event_type = event.get("event", "unknown")
                    events_received.append(event_type)

                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    # Highlight important events
                    if event_type == "on_chat_model_end":
                        print(f"\n{'='*80}")
                        print(f"🎯 [{timestamp}] *** on_chat_model_end EVENT RECEIVED ***")
                        print(f"{'='*80}\n")
                    elif event_type == "on_chat_model_stream":
                        token = event.get("data", {}).get("chunk", {}).get("content", "")
                        print(f"[{timestamp}] {event_type}: {repr(token)}")
                    else:
                        print(f"[{timestamp}] {event_type}")

                    # Stop after we get a completion event
                    if event_type in ["on_chain_end", "on_llm_end"]:
                        print(f"\n[{timestamp}] Agent run completed, stopping...")
                        break

                except json.JSONDecodeError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Non-JSON message: {message}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")

    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nTotal events received: {len(events_received)}")
    print("\nEvent types received:")
    for event_type in sorted(set(events_received)):
        count = events_received.count(event_type)
        print(f"  - {event_type}: {count}x")

    # Check for on_chat_model_end
    has_chat_model_end = "on_chat_model_end" in events_received

    print(f"\n{'='*80}")
    if has_chat_model_end:
        print("✅ SUCCESS: on_chat_model_end events ARE being sent!")
        print(f"   Found {events_received.count('on_chat_model_end')} on_chat_model_end event(s)")
    else:
        print("❌ FAILURE: on_chat_model_end events NOT found!")
        print("   Available events:", sorted(set(events_received)))
    print(f"{'='*80}\n")

    return has_chat_model_end


if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket_events())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
