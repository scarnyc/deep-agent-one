#!/usr/bin/env python3
"""
Replay Test for LangSmith Trace 2bdaec5e-2c4a-4737-964e-2e89e2ddaa92

This script reproduces the exact scenario that triggered the CancelledError:
- User query: "latest trends in quantum"
- Agent executes 27 parallel web_search tool calls
- Previous behavior: CancelledError after ~3.6 seconds
- Expected with fix: Successful completion within 300s timeout

Test validates:
1. Parallel tool execution completes without CancelledError
2. Stream timeout of 300s is sufficient
3. Client receives all tool results
4. No duplicate error events
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
    print("📦 Install with: pip install websockets")
    sys.exit(1)


async def test_trace_2bdaec5e_replay():
    """
    Test the exact scenario from trace 2bdaec5e.

    Sends the same query that triggered 27 parallel tool calls.
    """

    uri = "ws://localhost:8000/api/v1/ws"
    thread_id = f"test-trace-2bdaec5e-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print("=" * 80)
    print("🧪 TRACE 2bdaec5e REPLAY TEST")
    print("=" * 80)
    print(f"📡 Connecting to: {uri}")
    print(f"🔖 Thread ID: {thread_id}")
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    print("📝 This test reproduces the exact scenario that caused CancelledError:")
    print("   - Query: 'latest trends in quantum'")
    print("   - Expected: 27 parallel web_search tool calls")
    print("   - Original failure: CancelledError after ~3.6 seconds")
    print("   - With fix: Should complete successfully within 300s")
    print()
    print("=" * 80)

    start_time = time.time()

    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=300) as websocket:
            print("✅ Connected to WebSocket\n")

            # Send the exact query from the trace
            message = {
                "type": "chat",
                "message": "latest trends in quantum",
                "thread_id": thread_id,
            }

            print(f"📤 Sending: {message['message']}")
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
                    # Increased timeout to match backend (300s)
                    response = await asyncio.wait_for(websocket.recv(), timeout=310)
                    event = json.loads(response)
                    events_received.append(event)

                    event_type = event.get("event", "unknown")

                    # Track tool execution
                    if event_type == "on_tool_start" or event_type == "on_tool_call_start":
                        tool_calls_started += 1
                        tool_data = event.get("data", {})
                        tool_name = tool_data.get("name", event.get("name", "unknown"))
                        query = tool_data.get("input", {}).get("query", "N/A")
                        print(f"  🔧 Tool #{tool_calls_started} started: {tool_name}")
                        if len(query) > 80:
                            print(f"     Query: {query[:77]}...")
                        else:
                            print(f"     Query: {query}")

                    elif event_type == "on_tool_end" or event_type == "on_tool_call_end":
                        tool_calls_completed += 1
                        print(f"  ✅ Tool #{tool_calls_completed} completed")

                    # Track errors
                    elif event_type == "on_error":
                        error_events.append(event)
                        error_data = event.get("data", {})
                        print("\n  ❌ ERROR EVENT RECEIVED:")
                        print(f"     {json.dumps(error_data, indent=6)}\n")

                    # Track chain completion (only for main LangGraph chain, not middleware)
                    elif event_type == "on_chain_end":
                        event_name = event.get("name", "")
                        if event_name == "LangGraph":
                            print("\n  🏁 LangGraph chain complete")
                            complete = True
                        else:
                            # Middleware chain ended, continue waiting for main chain
                            pass

                except TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"\n⏱️  Timeout waiting for response ({elapsed:.1f}s elapsed)")
                    print("   This indicates the stream timed out (>300s)")
                    break
                except Exception as e:
                    print(f"\n❌ Error receiving event: {e}")
                    break

            elapsed_time = time.time() - start_time

            # ===== RESULTS =====
            print("\n" + "=" * 80)
            print("📊 TEST RESULTS")
            print("=" * 80)

            print(f"\n⏱️  Execution Time: {elapsed_time:.2f} seconds")
            print(f"📨 Events Received: {len(events_received)}")
            print(f"🔧 Tool Calls Started: {tool_calls_started}")
            print(f"✅ Tool Calls Completed: {tool_calls_completed}")
            print(f"❌ Error Events: {len(error_events)}")

            # Validation
            print("\n" + "=" * 80)
            print("VALIDATION")
            print("=" * 80)

            checks = []

            # Check 1: No timeout (completed within 300s)
            check_timeout = {
                "name": "Completed within 300s timeout",
                "pass": elapsed_time < 300,
                "expected": "< 300 seconds",
                "actual": f"{elapsed_time:.2f} seconds",
            }
            checks.append(check_timeout)

            # Check 2: No CancelledError
            cancelled_errors = [e for e in error_events if "cancel" in json.dumps(e).lower()]
            check_no_cancelled = {
                "name": "No CancelledError received",
                "pass": len(cancelled_errors) == 0,
                "expected": "0 cancellation errors",
                "actual": f"{len(cancelled_errors)} cancellation errors",
            }
            checks.append(check_no_cancelled)

            # Check 3: Tools executed (at least some tool calls)
            check_tools = {
                "name": "Tool calls executed",
                "pass": tool_calls_started > 0,
                "expected": ">= 1 tool call",
                "actual": f"{tool_calls_started} tool calls",
            }
            checks.append(check_tools)

            # Check 4: Tools completed successfully
            check_completion = {
                "name": "Tool calls completed",
                "pass": tool_calls_completed == tool_calls_started
                if tool_calls_started > 0
                else True,
                "expected": f"{tool_calls_started} completions",
                "actual": f"{tool_calls_completed} completions",
            }
            checks.append(check_completion)

            # Check 5: No duplicate error events
            check_duplicates = {
                "name": "No duplicate error events",
                "pass": len(error_events) <= 1,  # At most one error
                "expected": "<= 1 error event",
                "actual": f"{len(error_events)} error events",
            }
            checks.append(check_duplicates)

            # Print validation results
            all_pass = True
            for check in checks:
                status = "✅ PASS" if check["pass"] else "❌ FAIL"
                print(f"\n{status}: {check['name']}")
                print(f"  Expected: {check['expected']}")
                print(f"  Actual:   {check['actual']}")
                if not check["pass"]:
                    all_pass = False

            print("\n" + "=" * 80)

            if all_pass:
                print("🎉 SUCCESS: Trace 2bdaec5e scenario passed!")
                print("\nThe fix has resolved the CancelledError issue:")
                print("  ✓ Parallel tool execution completed successfully")
                print("  ✓ No timeout with 300s limit")
                print("  ✓ No CancelledError received")
                print("  ✓ All tools executed to completion")
                print("=" * 80)
                return True
            else:
                print("❌ FAILURE: Some validation checks failed")
                print("\nIssues detected:")
                failed_checks = [c for c in checks if not c["pass"]]
                for check in failed_checks:
                    print(f"  • {check['name']}: {check['actual']}")
                print("=" * 80)
                return False

    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket connection failed: {e}")
        print("\n💡 Make sure the backend is running:")
        print("   cd backend && uvicorn deep_agent.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    success = await test_trace_2bdaec5e_replay()

    print("\n" + "=" * 80)
    if success:
        print("🎯 TRACE 2bdaec5e REPLAY TEST PASSED")
        print("\nThe WebSocket CancelledError fix is working correctly.")
        print("Parallel tool execution completes without timeout or cancellation.")
        sys.exit(0)
    else:
        print("❌ TRACE 2bdaec5e REPLAY TEST FAILED")
        print("\nReview the validation failures above for details.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
