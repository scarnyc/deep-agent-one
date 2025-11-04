"""
Multi-turn conversation WebSocket test.

Tests error handling during tool execution in a real conversation flow:
1. User asks: "what's the weather in Queens, NYC today?"
2. AI responds (may request HITL approval)
3. User confirms: "yes"
4. Tool execution happens (web search)
5. Verify error handling works correctly

This test validates the on_error event handler implementation.
"""
import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("❌ Error: websockets library not installed")
    print("📦 Install with: pip install websockets")
    sys.exit(1)


async def test_multiturn_conversation():
    """Test multi-turn conversation with tool execution."""
    uri = "ws://localhost:8000/api/v1/ws"

    print("=" * 70)
    print("🧪 MULTI-TURN CONVERSATION TEST")
    print("=" * 70)
    print(f"📡 Connecting to: {uri}")
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()

    try:
        async with websockets.connect(uri) as websocket:
            thread_id = f"test-multiturn-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # ==========================================
            # TURN 1: User asks about weather
            # ==========================================
            print("🔵 " + "="*66)
            print("👤 TURN 1: User asks about weather")
            print("🔵 " + "="*66)

            message1 = {
                "type": "chat",
                "message": "what's the weather in Queens, NYC today?",
                "thread_id": thread_id
            }

            print(f"📤 Sending: {message1['message']}")
            await websocket.send(json.dumps(message1))

            # Collect all events from turn 1
            turn1_events = []
            turn1_complete = False
            turn1_errors = []

            print("📥 Receiving events...")

            while not turn1_complete:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    event = json.loads(response)
                    turn1_events.append(event)

                    event_type = event.get('event', 'unknown')

                    # Log interesting events
                    if event_type == 'on_chain_start':
                        print(f"  ▶️  Chain started: {event.get('name', 'unknown')}")
                    elif event_type == 'on_chat_model_stream':
                        # Don't log every token
                        pass
                    elif event_type == 'on_chat_model_end':
                        print(f"  ✅ Chat model finished")
                    elif event_type in ['on_error', 'on_chain_error', 'on_llm_error', 'error']:
                        turn1_errors.append(event)
                        print(f"  ❌ ERROR: {event_type}")
                        error_data = event.get('data') or event.get('error')
                        print(f"     Details: {error_data}")

                    # Check for completion
                    if event_type in ['on_chain_end', 'on_llm_end']:
                        print(f"  🏁 Turn 1 complete")
                        turn1_complete = True

                except asyncio.TimeoutError:
                    print("  ⏱️  Timeout waiting for response (30s)")
                    break
                except Exception as e:
                    print(f"  ❌ Error receiving event: {e}")
                    break

            print(f"\n📊 Turn 1 Summary:")
            print(f"   Events received: {len(turn1_events)}")
            print(f"   Errors: {len(turn1_errors)}")

            if turn1_errors:
                print(f"\n⚠️  Turn 1 had errors - stopping test")
                return {
                    "success": False,
                    "tool_executed": False,
                    "error_occurred": True,
                    "turn": 1,
                    "error_events": turn1_errors
                }

            # Wait before turn 2
            await asyncio.sleep(2)

            # ==========================================
            # TURN 2: User confirms
            # ==========================================
            print("\n🟢 " + "="*66)
            print("👤 TURN 2: User confirms")
            print("🟢 " + "="*66)

            message2 = {
                "type": "chat",
                "message": "yes",
                "thread_id": thread_id
            }

            print(f"📤 Sending: {message2['message']}")
            await websocket.send(json.dumps(message2))

            # Collect all events from turn 2 (tool execution)
            turn2_events = []
            turn2_complete = False
            turn2_errors = []
            tool_executed = False
            tools_called = []

            print("📥 Receiving events...")

            while not turn2_complete:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60)
                    event = json.loads(response)
                    turn2_events.append(event)

                    event_type = event.get('event', 'unknown')

                    # Log interesting events
                    if event_type == 'on_chain_start':
                        print(f"  ▶️  Chain started: {event.get('name', 'unknown')}")
                    elif event_type == 'on_tool_start':
                        tool_executed = True
                        tool_name = event.get('name', 'unknown')
                        tools_called.append(tool_name)
                        print(f"  🔧 Tool started: {tool_name}")
                    elif event_type == 'on_tool_end':
                        print(f"  ✅ Tool completed")
                    elif event_type == 'on_chat_model_stream':
                        # Don't log every token
                        pass
                    elif event_type == 'on_chat_model_end':
                        print(f"  ✅ Chat model finished")
                    elif event_type in ['on_error', 'on_chain_error', 'on_llm_error', 'error']:
                        turn2_errors.append(event)
                        print(f"  ❌ ERROR: {event_type}")
                        error_data = event.get('data') or event.get('error')
                        print(f"     Details: {error_data}")

                    # Check for completion
                    if event_type in ['on_chain_end', 'on_llm_end']:
                        print(f"  🏁 Turn 2 complete")
                        turn2_complete = True

                except asyncio.TimeoutError:
                    print("  ⏱️  Timeout waiting for response (60s)")
                    break
                except Exception as e:
                    print(f"  ❌ Error receiving event: {e}")
                    break

            print(f"\n📊 Turn 2 Summary:")
            print(f"   Events received: {len(turn2_events)}")
            print(f"   Tools executed: {len(tools_called)}")
            if tools_called:
                for tool in tools_called:
                    print(f"     - {tool}")
            print(f"   Errors: {len(turn2_errors)}")

            # ==========================================
            # FINAL RESULTS
            # ==========================================
            print("\n" + "=" * 70)
            print("📊 TEST RESULTS")
            print("=" * 70)

            total_events = len(turn1_events) + len(turn2_events)
            total_errors = len(turn1_errors) + len(turn2_errors)

            print(f"Total events: {total_events}")
            print(f"  Turn 1: {len(turn1_events)} events")
            print(f"  Turn 2: {len(turn2_events)} events")
            print()
            print(f"Tool execution: {'✅ YES' if tool_executed else '❌ NO'}")
            if tools_called:
                print(f"  Tools called: {', '.join(tools_called)}")
            print()
            print(f"Errors: {total_errors}")

            if total_errors > 0:
                print("\n⚠️  ERROR DETAILS:")
                for i, error in enumerate(turn1_errors + turn2_errors, 1):
                    print(f"\n  Error {i}:")
                    print(f"    Event: {error.get('event')}")
                    print(f"    Data: {error.get('data') or error.get('error')}")

            print("\n" + "=" * 70)

            # Determine success
            success = (total_errors == 0) or (tool_executed and total_errors == 0)

            if success:
                print("✅ TEST PASSED")
            else:
                print("❌ TEST FAILED")
                if total_errors > 0:
                    print("   Reason: Errors occurred")
                if not tool_executed:
                    print("   Reason: Tool not executed")

            print("=" * 70)

            return {
                "success": success,
                "tool_executed": tool_executed,
                "tools_called": tools_called,
                "error_occurred": total_errors > 0,
                "turn1_events": len(turn1_events),
                "turn2_events": len(turn2_events),
                "total_errors": total_errors,
                "error_events": turn1_errors + turn2_errors
            }

    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket connection failed: {e}")
        print("\n💡 Make sure the backend is running:")
        print("   cd backend && uvicorn deep_agent.main:app --reload --port 8000")
        return {
            "success": False,
            "error": str(e),
            "connection_failed": True
        }
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    try:
        result = asyncio.run(test_multiturn_conversation())

        print("\n" + "=" * 70)
        print("🎯 FINAL RESULT")
        print("=" * 70)
        print(json.dumps(result, indent=2))
        print("=" * 70)

        # Exit with appropriate code
        sys.exit(0 if result.get("success") else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
