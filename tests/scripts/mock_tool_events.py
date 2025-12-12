#!/usr/bin/env python3
"""Generate mock events matching LangSmith trace e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06.

This module simulates the exact event sequence from the original trace where
10 parallel web_search tool calls were executed, taking 8-14 seconds each.
"""

import uuid
from datetime import datetime
from typing import Any


class TraceEventGenerator:
    """Generate mock events matching the actual LangSmith trace."""

    # Actual tool IDs from trace e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06
    TOOL_IDS = [
        "b36eb3d4-735e-41a9-8743-267cdb278464",
        "18036579-c190-4d52-8d08-d6eb890d283f",
        "572ca62d-1ce6-412c-b4ef-b81e36898b46",
        "e942fb09-500a-444c-8018-af6e4da17d65",
        "03418ed0-6d83-4233-b72b-b068c8804b8b",
        "7d7ec400-e15e-4220-a55e-f5981a032168",
        "56d7f9ad-dcc0-49cc-b629-aff487b83438",
        "23a7a9ef-10ce-4269-a153-f348174a5887",
        "14d1d57b-6d59-4eb1-8cea-5c1986b7f831",
        "2ece164a-c925-4411-946d-9ed073bb1d0a",
    ]

    # Tool completion times (seconds after start)
    TOOL_DURATIONS = [
        11.47,  # Tool 1: 11.47s
        13.63,  # Tool 2: 13.63s (longest)
        7.71,  # Tool 3: 7.71s
        7.49,  # Tool 4: 7.49s
        7.72,  # Tool 5: 7.72s
        9.43,  # Tool 6: 9.43s
        8.20,  # Tool 7: 8.20s
        8.19,  # Tool 8: 8.19s
        9.43,  # Tool 9: 9.43s
        9.63,  # Tool 10: 9.63s
    ]

    # Mock web search queries (realistic based on quantum computing trends)
    TOOL_QUERIES = [
        "latest quantum computing breakthroughs 2025",
        "quantum networking advances",
        "quantum cryptography developments",
        "fault-tolerant quantum computers progress",
        "quantum sensing applications",
        "quantum algorithms research",
        "quantum hardware improvements",
        "quantum error correction techniques",
        "quantum supremacy milestones",
        "commercial quantum computing adoption",
    ]

    def __init__(self, thread_id: str = None, trace_id: str = None):
        """Initialize generator with thread and trace IDs."""
        self.thread_id = thread_id or str(uuid.uuid4())
        self.trace_id = trace_id or "e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06"
        self.start_time = datetime.now()

    def generate_chain_start(self) -> dict[str, Any]:
        """Generate on_chain_start event."""
        return {
            "event": "on_chain_start",
            "data": {
                "input": {
                    "messages": [
                        {"content": "what's the latest trends in quantum?", "type": "human"}
                    ]
                }
            },
            "name": "model",
            "tags": [],
            "run_id": str(uuid.uuid4()),
            "metadata": {
                "thread_id": self.thread_id,
                "trace_id": self.trace_id,
                "langgraph_node": "model",
                "langgraph_step": 1,
            },
        }

    def generate_tool_call_start_events(self) -> list[dict[str, Any]]:
        """Generate 10 on_tool_call_start events (parallel tool execution)."""
        events = []
        for i, (tool_id, query) in enumerate(zip(self.TOOL_IDS, self.TOOL_QUERIES, strict=False)):
            event = {
                "event": "on_tool_call_start",
                "data": {
                    "input": {
                        "query": query,
                        "max_results": 5,
                    },
                    "tool_call_id": tool_id,
                },
                "name": "web_search",
                "tags": ["web_search", f"tool_{i+1}"],
                "run_id": tool_id,
                "metadata": {
                    "thread_id": self.thread_id,
                    "trace_id": self.trace_id,
                    "langgraph_node": "tools",
                    "tool_index": i,
                },
            }
            events.append(event)
        return events

    def generate_tool_call_end_events(self) -> list[tuple[float, dict[str, Any]]]:
        """Generate 10 on_tool_call_end events with timing (duration, event)."""
        events = []
        for i, (tool_id, duration, query) in enumerate(
            zip(self.TOOL_IDS, self.TOOL_DURATIONS, self.TOOL_QUERIES, strict=False)
        ):
            event = {
                "event": "on_tool_call_end",
                "data": {
                    "output": {
                        "results": [
                            {
                                "title": f"Quantum Computing Trends {i+1}",
                                "url": f"https://example.com/quantum-{i+1}",
                                "snippet": f"Mock result for: {query}",
                            }
                        ]
                    },
                    "tool_call_id": tool_id,
                },
                "name": "web_search",
                "tags": ["web_search", f"tool_{i+1}"],
                "run_id": tool_id,
                "metadata": {
                    "thread_id": self.thread_id,
                    "trace_id": self.trace_id,
                    "langgraph_node": "tools",
                    "tool_index": i,
                    "duration_seconds": duration,
                },
            }
            events.append((duration, event))
        return events

    def generate_llm_stream_events(self) -> list[dict[str, Any]]:
        """Generate on_chat_model_stream events (model response after tools)."""
        response_chunks = [
            "Based on the latest research, here are the key quantum computing trends:\n\n",
            "1. **Fault-Tolerant Systems**: Major progress toward error-corrected qubits\n",
            "2. **Quantum Networking**: Advances in quantum repeaters and entanglement distribution\n",
            "3. **Commercial Applications**: Growing enterprise adoption in optimization and ML\n",
            "4. **Hardware Scaling**: Multiple platforms reaching 100+ qubit systems\n\n",
            "These trends indicate quantum computing is transitioning from research to practical applications.",
        ]

        events = []
        for i, chunk in enumerate(response_chunks):
            event = {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": {
                        "content": chunk,
                        "type": "AIMessageChunk",
                    }
                },
                "name": "ChatOpenAI",
                "tags": ["llm", "streaming"],
                "run_id": str(uuid.uuid4()),
                "metadata": {
                    "thread_id": self.thread_id,
                    "trace_id": self.trace_id,
                    "chunk_index": i,
                },
            }
            events.append(event)
        return events

    def generate_chain_end(self) -> dict[str, Any]:
        """Generate on_chain_end event."""
        return {
            "event": "on_chain_end",
            "data": {
                "output": {
                    "messages": [
                        {
                            "content": "Based on the latest research, quantum trends include...",
                            "type": "ai",
                        }
                    ]
                }
            },
            "name": "model",
            "tags": [],
            "run_id": str(uuid.uuid4()),
            "metadata": {
                "thread_id": self.thread_id,
                "trace_id": self.trace_id,
                "langgraph_node": "model",
            },
        }

    def generate_all_events(self) -> list[tuple[float, dict[str, Any]]]:
        """Generate complete event sequence with timing.

        Returns:
            List of (delay_seconds, event) tuples matching the trace timeline.
        """
        events = []

        # 1. Chain start (immediate)
        events.append((0.0, self.generate_chain_start()))

        # 2. All tool start events (parallel, at t=0)
        for tool_start_event in self.generate_tool_call_start_events():
            events.append((0.0, tool_start_event))

        # 3. Tool end events (staggered based on actual durations)
        tool_end_events = self.generate_tool_call_end_events()
        events.extend(tool_end_events)

        # 4. LLM streaming (starts after longest tool completes at ~14s)
        max_tool_duration = max(self.TOOL_DURATIONS)
        for i, stream_event in enumerate(self.generate_llm_stream_events()):
            # Space out streaming chunks over ~5 seconds
            delay = max_tool_duration + (i * 1.0)
            events.append((delay, stream_event))

        # 5. Chain end (after streaming completes, ~20s total)
        events.append((max_tool_duration + 6.0, self.generate_chain_end()))

        # Sort by delay to ensure correct ordering
        events.sort(key=lambda x: x[0])

        return events


def main():
    """Demo the event generator."""
    generator = TraceEventGenerator()
    events = generator.generate_all_events()

    print(f"Generated {len(events)} events from trace e2eaaf57\n")
    print("=" * 80)
    print("EVENT TIMELINE")
    print("=" * 80)

    for delay, event in events:
        event_type = event["event"]
        event_name = event.get("name", "unknown")
        print(f"t={delay:5.2f}s  {event_type:30s}  {event_name}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    event_counts = {}
    for _, event in events:
        event_type = event["event"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    for event_type, count in sorted(event_counts.items()):
        print(f"  {event_type:30s}: {count:2d}")

    # Verify tool events are present
    tool_events = [e for _, e in events if e["event"] in ["on_tool_call_start", "on_tool_call_end"]]

    print(f"\n✓ Tool events present: {len(tool_events)} (expected: 20)")
    print(
        f"  - on_tool_call_start: {len([e for _, e in events if e['event'] == 'on_tool_call_start'])}"
    )
    print(
        f"  - on_tool_call_end: {len([e for _, e in events if e['event'] == 'on_tool_call_end'])}"
    )


if __name__ == "__main__":
    main()
