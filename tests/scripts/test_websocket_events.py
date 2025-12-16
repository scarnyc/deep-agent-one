#!/usr/bin/env python3
"""Test script to verify WebSocket event streaming with tool calls."""

import asyncio
import json
import uuid

import websockets


async def test_web_search_events():
    """Send a multi-turn conversation to trigger web search."""
    uri = "ws://localhost:8000/api/v1/ws"
    thread_id = str(uuid.uuid4())  # Same thread for both messages

    print("🔌 Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket\n")

        # ===== TURN 1: Initial query =====
        print("=" * 80)
        print("TURN 1: Initial query (agent may not use tools)")
        print("=" * 80)

        message1 = {
            "type": "chat",
            "message": "what's the latest trends in quantum?",
            "thread_id": thread_id,
            "request_id": str(uuid.uuid4()),
        }

        print(f"📤 Sending: {message1['message']}")
        await websocket.send(json.dumps(message1))

        # Consume events from turn 1
        turn1_events = 0
        async for raw_message in websocket:
            try:
                event = json.loads(raw_message)
                turn1_events += 1
                event_type = event.get("event", "unknown")

                if event_type == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {}).get("content", "")
                    if content:
                        print(f"💬 {content[:60]}...", end="", flush=True)
                elif event_type == "on_chain_end":
                    print(f"\n✅ Turn 1 complete ({turn1_events} events)")
                    break
                elif event_type == "on_error":
                    print(f"\n❌ Error in turn 1: {event}")
                    break
            except Exception:
                pass

        # ===== TURN 2: Explicit tool request =====
        print("\n" + "=" * 80)
        print("TURN 2: Explicit web search request (should trigger tool)")
        print("=" * 80)

        message2 = {
            "type": "chat",
            "message": "Please use the web_search tool to find current information about quantum computing trends. Actually call the tool.",
            "thread_id": thread_id,  # SAME THREAD
            "request_id": str(uuid.uuid4()),
        }

        print(f"📤 Sending: {message2['message']}\n")
        await websocket.send(json.dumps(message2))

        # Track event types received in turn 2
        event_types_received = set()
        event_count = 0
        tool_events_found = False

        print("📥 Turn 2 Events:\n")
        print("-" * 80)

        try:
            async for raw_message in websocket:
                try:
                    event = json.loads(raw_message)
                    event_count += 1
                    event_type = event.get("event", "unknown")
                    event_types_received.add(event_type)

                    # Check for tool events
                    if "tool" in event_type.lower():
                        tool_events_found = True
                        print(f"🔧 TOOL EVENT FOUND: {event_type}")
                        print(f"   Event #{event_count}: {json.dumps(event, indent=2)[:200]}...")
                    elif event_type in ["on_chain_start", "on_chain_end"]:
                        print(f"🔗 {event_type}")
                    elif event_type == "on_chat_model_stream":
                        content = event.get("data", {}).get("chunk", {}).get("content", "")
                        if content:
                            print(f"💬 Streaming: {content[:50]}...")
                    elif event_type == "on_error":
                        print(f"❌ ERROR EVENT: {json.dumps(event, indent=2)}")
                    else:
                        print(f"📌 {event_type} (event #{event_count})")

                    # Stop after streaming completes or error
                    if event_type in ["on_chain_end", "on_error"]:
                        print("\n" + "-" * 80)
                        break

                except json.JSONDecodeError:
                    print(f"⚠️  Failed to parse message: {raw_message[:100]}")
                except Exception as exc:
                    print(f"⚠️  Error processing message: {exc}")

        except websockets.exceptions.ConnectionClosed:
            print("\n🔌 WebSocket connection closed")

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total events received: {event_count}")
        print(f"Event types received: {sorted(event_types_received)}")
        print(f"\n🔧 Tool events found: {'✅ YES' if tool_events_found else '❌ NO'}")

        # Verdict
        if tool_events_found:
            print("\n✅ SUCCESS: Tool events are being streamed to frontend!")
        else:
            print("\n❌ FAILURE: Tool events are NOT being streamed to frontend")
            print("   Check backend logs for filtered events")

        print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("WebSocket Event Streaming Test")
    print("Testing: Web search tool event visibility")
    print("=" * 80 + "\n")

    try:
        asyncio.run(test_web_search_events())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
