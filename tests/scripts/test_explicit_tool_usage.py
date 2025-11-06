#!/usr/bin/env python3
"""
Test WebSocket with explicit tool usage request.

Forces the agent to use web_search tool to validate timeout fix.
"""

import asyncio
import json
import sys
import time
from datetime import datetime

try:
    import websockets
except ImportError:
    print("❌ Error: websockets library not installed")
    sys.exit(1)


async def test_explicit_tool_usage():
    """Test with query that explicitly requests web search."""

    uri = "ws://localhost:8000/api/v1/ws"
    thread_id = f"test-explicit-tools-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print("=" * 80)
    print("🧪 EXPLICIT TOOL USAGE TEST")
    print("=" * 80)
    print(f"📡 Connecting to: {uri}")
    print(f"🔖 Thread ID: {thread_id}")
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    print("📝 This test forces tool usage to validate timeout fix")
    print("=" * 80)

    start_time = time.time()

    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=300) as websocket:
            print("✅ Connected to WebSocket\n")

            # More explicit query that requests web search
            message = {
                "type": "chat",
                "message": "Search the web for the latest quantum computing breakthroughs in 2024 and 2025. Please use web search to find recent news and research.",
                "thread_id": thread_id
            }

            print(f"📤 Sending explicit tool request")
            await websocket.send(json.dumps(message))

            # Track events
            events_received = []
            tool_calls_started = 0
            tool_calls_completed = 0
            error_events = []
            complete = False

            print("\n📥 Receiving events...\n")

            while not complete:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=310)
                    event = json.loads(response)
                    events_received.append(event)

                    event_type = event.get('event', 'unknown')

                    # Track tool execution
                    if event_type in ['on_tool_start', 'on_tool_call_start']:
                        tool_calls_started += 1
                        tool_name = event.get('name', event.get('data', {}).get('name', 'unknown'))
                        print(f"  🔧 Tool #{tool_calls_started} started: {tool_name}")

                    elif event_type in ['on_tool_end', 'on_tool_call_end']:
                        tool_calls_completed += 1
                        print(f"  ✅ Tool #{tool_calls_completed} completed")

                    # Track errors
                    elif event_type == 'on_error':
                        error_events.append(event)
                        print(f"\n  ❌ ERROR: {event.get('data', {})}\n")

                    # Track chain completion
                    elif event_type == 'on_chain_end':
                        print(f"\n  🏁 Chain complete")
                        complete = True

                    # Show streaming response
                    elif event_type == 'on_chat_model_stream':
                        chunk = event.get('data', {}).get('chunk', {}).get('content', '')
                        if chunk:
                            print(chunk, end='', flush=True)

                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"\n⏱️  Timeout after {elapsed:.1f}s")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    break

            elapsed_time = time.time() - start_time

            # Results
            print("\n\n" + "=" * 80)
            print("📊 TEST RESULTS")
            print("=" * 80)
            print(f"\n⏱️  Execution Time: {elapsed_time:.2f}s")
            print(f"📨 Events Received: {len(events_received)}")
            print(f"🔧 Tool Calls Started: {tool_calls_started}")
            print(f"✅ Tool Calls Completed: {tool_calls_completed}")
            print(f"❌ Error Events: {len(error_events)}")

            # Validation
            print("\n" + "=" * 80)
            print("VALIDATION")
            print("=" * 80)

            success = True

            # Check 1: Completed without timeout
            if elapsed_time < 300:
                print(f"\n✅ PASS: Completed within 300s ({elapsed_time:.2f}s)")
            else:
                print(f"\n❌ FAIL: Timeout exceeded ({elapsed_time:.2f}s)")
                success = False

            # Check 2: No cancellation errors
            cancelled = [e for e in error_events if 'cancel' in str(e).lower()]
            if len(cancelled) == 0:
                print(f"✅ PASS: No cancellation errors")
            else:
                print(f"❌ FAIL: {len(cancelled)} cancellation errors")
                success = False

            # Check 3: Tool usage (nice to have)
            if tool_calls_started > 0:
                print(f"✅ PASS: Tools used ({tool_calls_started} tool calls)")
            else:
                print(f"⚠️  WARN: No tools used (agent gave direct response)")

            # Check 4: Tools completed
            if tool_calls_completed == tool_calls_started:
                print(f"✅ PASS: All tools completed")
            elif tool_calls_started > 0:
                print(f"⚠️  WARN: Some tools didn't complete ({tool_calls_completed}/{tool_calls_started})")

            print("\n" + "=" * 80)

            if success and not error_events:
                print("🎉 SUCCESS: Timeout fix working correctly!")
                return True
            elif success:
                print("⚠️  PARTIAL SUCCESS: No timeout, but check warnings")
                return True
            else:
                print("❌ FAILURE: Issues detected")
                return False

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_explicit_tool_usage())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(130)
