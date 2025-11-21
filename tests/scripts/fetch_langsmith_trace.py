#!/usr/bin/env python3
"""Fetch LangSmith trace and analyze events for mocking."""

import os
import json
from langsmith import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_trace(trace_id: str):
    """Fetch a specific trace from LangSmith."""
    client = Client(
        api_key=os.getenv("LANGSMITH_API_KEY"),
        api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    )

    print(f"🔍 Fetching trace: {trace_id}")
    print("=" * 80)

    try:
        # Get the trace runs
        runs = list(client.list_runs(trace_id=trace_id))

        if not runs:
            print(f"❌ No runs found for trace ID: {trace_id}")
            return

        print(f"✅ Found {len(runs)} runs in trace\n")

        # Analyze each run
        for i, run in enumerate(runs, 1):
            print(f"\n{'=' * 80}")
            print(f"RUN #{i}: {run.name}")
            print(f"{'=' * 80}")
            print(f"Run ID: {run.id}")
            print(f"Run Type: {run.run_type}")
            print(f"Status: {run.status}")
            print(f"Start Time: {run.start_time}")
            print(f"End Time: {run.end_time}")

            # Print inputs
            if run.inputs:
                print(f"\n📥 INPUTS:")
                print(json.dumps(run.inputs, indent=2)[:500])

            # Print outputs
            if run.outputs:
                print(f"\n📤 OUTPUTS:")
                print(json.dumps(run.outputs, indent=2)[:500])

            # Print errors if any
            if run.error:
                print(f"\n❌ ERROR:")
                print(run.error)

            # Print events if available
            if hasattr(run, 'events') and run.events:
                print(f"\n📊 EVENTS ({len(run.events)}):")
                for event in run.events[:10]:  # First 10 events
                    print(f"  - {event}")

            # Print extra metadata
            if run.extra:
                print(f"\n🔧 EXTRA METADATA:")
                print(json.dumps(run.extra, indent=2)[:500])

        # Save full trace to JSON for analysis
        trace_data = {
            "trace_id": trace_id,
            "runs": [
                {
                    "id": str(run.id),
                    "name": run.name,
                    "run_type": run.run_type,
                    "status": run.status,
                    "start_time": str(run.start_time),
                    "end_time": str(run.end_time),
                    "inputs": run.inputs,
                    "outputs": run.outputs,
                    "error": run.error,
                    "extra": run.extra,
                }
                for run in runs
            ]
        }

        output_file = f"tests/scripts/trace_{trace_id.replace('-', '_')}.json"
        with open(output_file, "w") as f:
            json.dump(trace_data, f, indent=2)

        print(f"\n\n✅ Full trace saved to: {output_file}")

        # Analyze tool calls specifically
        print(f"\n{'=' * 80}")
        print("🔧 TOOL CALL ANALYSIS")
        print(f"{'=' * 80}")

        tool_calls = [run for run in runs if run.run_type == "tool"]
        print(f"Total tool calls: {len(tool_calls)}")

        for i, tool_run in enumerate(tool_calls, 1):
            print(f"\n  Tool #{i}: {tool_run.name}")
            print(f"    Status: {tool_run.status}")
            print(f"    Duration: {(tool_run.end_time - tool_run.start_time).total_seconds():.2f}s" if tool_run.end_time else "    Duration: N/A")
            if tool_run.inputs:
                print(f"    Input: {str(tool_run.inputs)[:100]}...")
            if tool_run.outputs:
                print(f"    Output: {str(tool_run.outputs)[:100]}...")

    except Exception as e:
        print(f"❌ Error fetching trace: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Trace ID from user request (investigating 44.85s timeout)
    trace_id = "49feb9c7-84b8-4c2f-936d-86ed9b4562eb"
    fetch_trace(trace_id)
