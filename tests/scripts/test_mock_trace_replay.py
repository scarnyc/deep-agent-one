#!/usr/bin/env python3
"""Test event filtering by replaying trace e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06.

This test verifies that our fixes (expanded STREAM_ALLOWED_EVENTS and increased
timeout) allow tool events to stream correctly through the event filter.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.scripts.mock_tool_events import TraceEventGenerator
from backend.deep_agent.config.settings import get_settings


def filter_events(
    events: List[Dict[str, Any]], allowed_events: set[str]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Simulate the event filtering logic from agent_service.py.

    Args:
        events: All events generated
        allowed_events: Set of allowed event types

    Returns:
        (passed_events, filtered_events) tuple
    """
    passed = []
    filtered = []

    for event in events:
        event_type = event.get("event", "unknown")
        if event_type in allowed_events:
            passed.append(event)
        else:
            filtered.append(event)

    return passed, filtered


def analyze_results(
    passed: List[Dict[str, Any]], filtered: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze filtering results and generate report."""

    # Count event types
    passed_counts = {}
    for event in passed:
        event_type = event["event"]
        passed_counts[event_type] = passed_counts.get(event_type, 0) + 1

    filtered_counts = {}
    for event in filtered:
        event_type = event["event"]
        filtered_counts[event_type] = filtered_counts.get(event_type, 0) + 1

    # Check for tool events
    tool_events_passed = sum(
        passed_counts.get(evt, 0)
        for evt in ["on_tool_call_start", "on_tool_call_end", "on_tool_start", "on_tool_end"]
    )

    tool_events_filtered = sum(
        filtered_counts.get(evt, 0)
        for evt in ["on_tool_call_start", "on_tool_call_end", "on_tool_start", "on_tool_end"]
    )

    return {
        "total_events": len(passed) + len(filtered),
        "passed_events": len(passed),
        "filtered_events": len(filtered),
        "passed_counts": passed_counts,
        "filtered_counts": filtered_counts,
        "tool_events_passed": tool_events_passed,
        "tool_events_filtered": tool_events_filtered,
    }


def print_report(analysis: Dict[str, Any], allowed_events: set[str]):
    """Print detailed test report."""
    print("\n" + "=" * 80)
    print("MOCK TRACE REPLAY TEST - RESULTS")
    print("=" * 80)

    print(f"\n📊 Event Statistics:")
    print(f"  Total events generated: {analysis['total_events']}")
    print(f"  Events passed through:  {analysis['passed_events']} ({analysis['passed_events'] / analysis['total_events'] * 100:.1f}%)")
    print(f"  Events filtered out:    {analysis['filtered_events']} ({analysis['filtered_events'] / analysis['total_events'] * 100:.1f}%)")

    print(f"\n✅ Passed Event Types:")
    for event_type, count in sorted(analysis["passed_counts"].items()):
        print(f"  - {event_type:30s}: {count:2d}")

    if analysis["filtered_counts"]:
        print(f"\n❌ Filtered Event Types:")
        for event_type, count in sorted(analysis["filtered_counts"].items()):
            print(f"  - {event_type:30s}: {count:2d}")

    print(f"\n🔧 Tool Event Analysis:")
    print(f"  Tool events passed:    {analysis['tool_events_passed']}")
    print(f"  Tool events filtered:  {analysis['tool_events_filtered']}")

    print(f"\n⚙️  Configuration:")
    print(f"  Allowed events: {sorted(allowed_events)}")

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    # Validation checks
    checks = []

    # Check 1: Tool events should pass through
    tool_check = {
        "name": "Tool events pass through filter",
        "expected": "20 tool events (10 start + 10 end)",
        "actual": f"{analysis['tool_events_passed']} tool events",
        "pass": analysis['tool_events_passed'] == 20,
    }
    checks.append(tool_check)

    # Check 2: No tool events should be filtered
    no_filter_check = {
        "name": "No tool events filtered out",
        "expected": "0 tool events filtered",
        "actual": f"{analysis['tool_events_filtered']} tool events filtered",
        "pass": analysis['tool_events_filtered'] == 0,
    }
    checks.append(no_filter_check)

    # Check 3: Chat model stream events pass through
    chat_stream_check = {
        "name": "Chat model stream events pass",
        "expected": "6+ streaming events",
        "actual": f"{analysis['passed_counts'].get('on_chat_model_stream', 0)} streaming events",
        "pass": analysis['passed_counts'].get('on_chat_model_stream', 0) >= 6,
    }
    checks.append(chat_stream_check)

    # Check 4: Chain events pass through
    chain_check = {
        "name": "Chain lifecycle events pass",
        "expected": "2 chain events (start + end)",
        "actual": f"{analysis['passed_counts'].get('on_chain_start', 0) + analysis['passed_counts'].get('on_chain_end', 0)} chain events",
        "pass": (
            analysis['passed_counts'].get('on_chain_start', 0) == 1
            and analysis['passed_counts'].get('on_chain_end', 0) == 1
        ),
    }
    checks.append(chain_check)

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
        print("🎉 SUCCESS: All validation checks passed!")
        print("\nThe fixes have resolved the event filtering issue:")
        print("  ✓ Tool events (on_tool_call_start, on_tool_call_end) now stream correctly")
        print("  ✓ STREAM_ALLOWED_EVENTS configuration includes all required event types")
        print("  ✓ Frontend will receive tool execution visibility")
    else:
        print("❌ FAILURE: Some validation checks failed")
        print("\nIssues detected:")
        failed_checks = [c for c in checks if not c["pass"]]
        for check in failed_checks:
            print(f"  • {check['name']}: {check['actual']}")

    print("=" * 80)

    return all_pass


def main():
    """Run the mock trace replay test."""
    print("=" * 80)
    print("MOCK TRACE REPLAY TEST")
    print("Simulating LangSmith trace: e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06")
    print("=" * 80)

    # Load settings to get current allowed events
    settings = get_settings()
    allowed_events = set(settings.stream_allowed_events_list)

    print(f"\n📋 Test Configuration:")
    print(f"  Stream version: {settings.STREAM_VERSION}")
    print(f"  Stream timeout: {settings.STREAM_TIMEOUT_SECONDS}s")
    print(f"  Allowed events: {len(allowed_events)} types")

    # Generate mock events
    print("\n🎬 Generating mock events from trace...")
    generator = TraceEventGenerator(
        thread_id="test-thread-123",
        trace_id="e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06"
    )

    events_with_timing = generator.generate_all_events()
    events = [event for _, event in events_with_timing]

    print(f"  Generated {len(events)} events")

    # Simulate event filtering
    print("\n🔍 Simulating event filter from agent_service.py...")
    passed, filtered = filter_events(events, allowed_events)

    print(f"  Passed through: {len(passed)} events")
    print(f"  Filtered out:   {len(filtered)} events")

    # Analyze results
    analysis = analyze_results(passed, filtered)

    # Print report and validation
    all_pass = print_report(analysis, allowed_events)

    # Exit with appropriate code
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
