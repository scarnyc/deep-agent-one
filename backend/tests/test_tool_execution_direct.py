"""
Direct tool execution test with response capture.

Tests that tool execution triggers error handling correctly.
More direct approach than multi-turn test.
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


async def test_direct_tool_execution():
    """Test direct tool execution command."""
    uri = "ws://localhost:8000/api/v1/ws"

    print("=" * 70)
    print("🧪 DIRECT TOOL EXECUTION TEST")
    print("=" * 70)
    print(f"📡 Connecting to: {uri}")
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()

    try:
        async with websockets.connect(uri) as websocket:
            thread_id = f"test-direct-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Direct command that should trigger tool use
            print("👤 USER PROMPT:")
            print("   'Search the web for the current weather in New York City'")
            print()

            message = {
                "type": "chat",
                "message": "Search the web for the current weather in New York City",
                "thread_id": thread_id
            }

            await websocket.send(json.dumps(message))

            # Collect all events
            events = []
            complete = False
            tool_executed = False
            tools_called = []
            errors = []
            ai_response = []

            print("📥 Receiving events...")
            print("-" * 70)

            while not complete:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60)
                    event = json.loads(response)
                    events.append(event)

                    event_type = event.get('event', 'unknown')

                    # Capture AI response tokens
                    if event_type == 'on_chat_model_stream':
                        token = event.get('data', {}).get('chunk', {}).get('content', '')
                        if token:
                            ai_response.append(token)

                    # Log important events
                    if event_type == 'on_chain_start':
                        print(f"  ▶️  Chain started: {event.get('name', 'unknown')}")
                    elif event_type == 'on_tool_start':
                        tool_executed = True
                        tool_name = event.get('name', 'unknown')
                        tools_called.append(tool_name)
                        print(f"  🔧 Tool started: {tool_name}")
                        # Print tool arguments if available
                        if 'input' in event:
                            print(f"     Args: {event['input']}")
                    elif event_type == 'on_tool_end':
                        print("  ✅ Tool completed")
                    elif event_type == 'on_chat_model_end':
                        print("  ✅ Chat model finished")
                    elif event_type in ['on_error', 'on_chain_error', 'on_llm_error', 'error']:
                        errors.append(event)
                        print(f"  ❌ ERROR: {event_type}")
                        error_data = event.get('data') or event.get('error')
                        print(f"     Details: {error_data}")
                    elif event_type == 'hitl_request':
                        print(f"  🚦 HITL Request: {event.get('data', {}).get('tool_name', 'unknown')}")

                    # Check for completion
                    if event_type in ['on_chain_end', 'on_llm_end']:
                        print("  🏁 Conversation complete")
                        complete = True

                except TimeoutError:
                    print("  ⏱️  Timeout waiting for response (60s)")
                    break
                except Exception as e:
                    print(f"  ❌ Error receiving event: {e}")
                    break

            print("-" * 70)

            # Display AI response
            if ai_response:
                full_response = ''.join(ai_response)
                print("\n🤖 AI RESPONSE:")
                print("-" * 70)
                print(full_response[:500] + ('...' if len(full_response) > 500 else ''))
                print("-" * 70)

            # Results
            print("\n" + "=" * 70)
            print("📊 TEST RESULTS")
            print("=" * 70)
            print(f"Total events: {len(events)}")
            print(f"Tool execution: {'✅ YES' if tool_executed else '❌ NO'}")
            if tools_called:
                print(f"  Tools called: {', '.join(tools_called)}")
            print(f"Errors: {len(errors)}")

            if errors:
                print("\n⚠️  ERROR DETAILS:")
                for i, error in enumerate(errors, 1):
                    print(f"\n  Error {i}:")
                    print(f"    Event: {error.get('event')}")
                    print(f"    Data: {error.get('data') or error.get('error')}")

            # Event breakdown
            print("\n📋 EVENT BREAKDOWN:")
            event_counts = {}
            for event in events:
                event_type = event.get('event', 'unknown')
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

            for event_type, count in sorted(event_counts.items()):
                print(f"  {event_type}: {count}")

            print("\n" + "=" * 70)

            # Determine success
            success = len(errors) == 0

            if success:
                print("✅ TEST PASSED - No errors occurred")
                if not tool_executed:
                    print("ℹ️  Note: No tools were executed (agent may not have decided to use tools)")
            else:
                print("❌ TEST FAILED - Errors occurred")

            print("=" * 70)

            return {
                "success": success,
                "tool_executed": tool_executed,
                "tools_called": tools_called,
                "error_occurred": len(errors) > 0,
                "total_events": len(events),
                "total_errors": len(errors),
                "error_events": errors,
                "ai_response_preview": ''.join(ai_response)[:200] if ai_response else None
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
        result = asyncio.run(test_direct_tool_execution())

        print("\n" + "=" * 70)
        print("🎯 FINAL RESULT")
        print("=" * 70)
        print(json.dumps({k: v for k, v in result.items() if k != 'error_events'}, indent=2))
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
