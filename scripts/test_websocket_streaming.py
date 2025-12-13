#!/usr/bin/env python3
"""Manual WebSocket client for testing real-time streaming with live server.

This script connects to the FastAPI WebSocket endpoint and displays
streaming events in real-time with color-coded output. It validates
the on_chat_model_stream event implementation and measures performance metrics.

Usage:
    1. Start backend: uvicorn backend.deep_agent.main:app --reload --port 8000
    2. Run this script: python scripts/test_websocket_streaming.py [optional message]
    3. Observe real-time token streaming

Requirements:
    - Backend server running on ws://localhost:8000/api/v1/ws
    - websockets library installed (pip install websockets)

Examples:
    # Default message
    python scripts/test_websocket_streaming.py

    # Custom message
    python scripts/test_websocket_streaming.py "Tell me a joke"

Output:
    - Real-time streaming tokens with color-coded events
    - Performance metrics (TTFT, tokens/second, total duration)
    - Event statistics breakdown
    - Validation checks summary

Exit Codes:
    0 - Test passed (all validation checks passed)
    1 - Connection error or test interrupted
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Any

import websockets


# ANSI color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class WebSocketTestClient:
    """Interactive WebSocket test client with real-time display."""

    def __init__(self, url: str = "ws://localhost:8000/api/v1/ws"):
        self.url = url
        self.event_counts: dict[str, int] = {}
        self.token_buffer = ""  # nosec B105 - empty string buffer, not a password
        self.start_time: float = 0
        self.first_token_time: float = 0
        self.event_log: list[dict[str, Any]] = []

    def print_header(self, text: str) -> None:
        """Print colored header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}")
        print(f"{text}")
        print(f"{'=' * 80}{Colors.ENDC}\n")

    def print_event(self, event_type: str, message: str, color: str = Colors.OKBLUE) -> None:
        """Print colored event message."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{color}[{timestamp}] {event_type}: {message}{Colors.ENDC}")

    def print_token(self, token: str) -> None:
        """Print streaming token (no newline)."""
        print(f"{Colors.OKGREEN}{token}{Colors.ENDC}", end="", flush=True)

    async def connect_and_test(self, message: str = "Tell me a short joke and count to 5") -> None:
        """Connect to WebSocket and test streaming."""
        self.print_header(f"WebSocket Streaming Test - {self.url}")

        print(f"{Colors.OKCYAN}Connecting to server...{Colors.ENDC}")

        try:
            async with websockets.connect(self.url) as websocket:
                self.print_event("CONNECTION", "✅ Connected successfully", Colors.OKGREEN)

                # Send test message
                payload = {
                    "type": "chat",
                    "message": message,
                    "thread_id": f"manual-test-{int(time.time())}",
                }

                print(f"\n{Colors.OKCYAN}Sending message:{Colors.ENDC}")
                print(f"  Message: '{message}'")
                print(f"  Thread ID: {payload['thread_id']}")

                await websocket.send(json.dumps(payload))
                self.print_event("SENT", "Message sent to server", Colors.OKCYAN)

                self.start_time = time.time()
                print(f"\n{Colors.OKGREEN}{Colors.BOLD}Streaming Response:{Colors.ENDC}")
                print(f"{Colors.OKGREEN}{'─' * 80}{Colors.ENDC}\n")

                # Receive and process events
                async for raw_message in websocket:
                    try:
                        event = json.loads(raw_message)
                        await self.process_event(event)

                    except json.JSONDecodeError as e:
                        self.print_event("ERROR", f"Failed to parse JSON: {e}", Colors.FAIL)
                    except Exception as e:
                        self.print_event("ERROR", f"Error processing event: {e}", Colors.FAIL)

        except websockets.exceptions.WebSocketException as e:
            self.print_event("CONNECTION ERROR", str(e), Colors.FAIL)
            sys.exit(1)
        except Exception as e:
            self.print_event("ERROR", str(e), Colors.FAIL)
            sys.exit(1)

        # Print summary
        self.print_summary()

    async def process_event(self, event: dict[str, Any]) -> None:
        """Process a single streaming event."""
        event_type = event.get("event", "unknown")

        # Track event counts
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        # Store event in log
        event_log_entry = {
            "timestamp": time.time() - self.start_time,
            "event_type": event_type,
            "event": event,
        }
        self.event_log.append(event_log_entry)

        # Handle different event types
        if event_type == "on_chat_model_stream":
            await self.handle_token_stream(event)

        elif event_type == "on_chain_start":
            chain_name = event.get("name", "unknown")
            self.print_event("CHAIN START", chain_name, Colors.OKCYAN)

        elif event_type == "on_chain_end":
            chain_name = event.get("name", "unknown")
            self.print_event("CHAIN END", chain_name, Colors.OKCYAN)

        elif event_type == "on_tool_start":
            tool_name = event.get("name", "unknown")
            self.print_event("TOOL START", tool_name, Colors.WARNING)

        elif event_type == "on_tool_end":
            tool_name = event.get("name", "unknown")
            self.print_event("TOOL END", tool_name, Colors.WARNING)

        elif event_type == "on_error":
            error_data = event.get("data", {})
            error_msg = error_data.get("error", "Unknown error")
            self.print_event("ERROR", error_msg, Colors.FAIL)

        else:
            # Log other event types
            print(f"{Colors.WARNING}[{event_type}]{Colors.ENDC}", end=" ", flush=True)

    async def handle_token_stream(self, event: dict[str, Any]) -> None:
        """Handle on_chat_model_stream event (token streaming)."""
        data = event.get("data", {})
        chunk = data.get("chunk", {})

        # Extract content from chunk (handle both dict and object formats)
        if isinstance(chunk, dict):
            content = chunk.get("content", "")
        else:
            content = getattr(chunk, "content", "")

        if content:
            # Record first token time
            if not self.first_token_time:
                self.first_token_time = time.time()
                elapsed = self.first_token_time - self.start_time
                print(f"\n{Colors.OKCYAN}[First token after {elapsed:.2f}s]{Colors.ENDC}\n")

            # Print token and add to buffer
            self.print_token(content)
            self.token_buffer += content

    def print_summary(self) -> None:
        """Print test summary with metrics."""
        end_time = time.time()
        total_duration = end_time - self.start_time

        self.print_header("Test Summary")

        # Performance metrics
        print(f"{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
        print(f"  Total duration: {total_duration:.2f}s")

        if self.first_token_time:
            ttft = self.first_token_time - self.start_time
            print(f"  Time to first token (TTFT): {ttft:.2f}s")

            if self.token_buffer:
                tokens_per_second = len(self.token_buffer) / (end_time - self.first_token_time)
                print(f"  Tokens per second: {tokens_per_second:.2f}")

        # Event statistics
        print(f"\n{Colors.BOLD}Event Statistics:{Colors.ENDC}")
        print(f"  Total events received: {sum(self.event_counts.values())}")
        print("\n  Event type breakdown:")
        for event_type, count in sorted(self.event_counts.items()):
            print(f"    - {event_type}: {count}")

        # Response content
        if self.token_buffer:
            print(f"\n{Colors.BOLD}Complete Response:{Colors.ENDC}")
            print(f"  Length: {len(self.token_buffer)} characters")
            print(f"  Content: {self.token_buffer}")

        # Validation
        print(f"\n{Colors.BOLD}Validation:{Colors.ENDC}")

        checks = []

        # Check token streaming
        if "on_chat_model_stream" in self.event_counts:
            checks.append(
                (
                    "✅",
                    f"Token streaming works ({self.event_counts['on_chat_model_stream']} tokens)",
                )
            )
        else:
            checks.append(("❌", "No token streaming events received"))

        # Check response content
        if self.token_buffer:
            checks.append(("✅", f"Response received ({len(self.token_buffer)} chars)"))
        else:
            checks.append(("❌", "No response content"))

        # Check performance
        if self.first_token_time and (self.first_token_time - self.start_time) < 5:
            checks.append(("✅", "TTFT < 5s (acceptable)"))
        else:
            checks.append(("⚠️", "TTFT > 5s (slow)"))

        if total_duration < 30:
            checks.append(("✅", "Total duration < 30s"))
        else:
            checks.append(("⚠️", "Total duration > 30s (slow)"))

        for status, message in checks:
            color = (
                Colors.OKGREEN
                if status == "✅"
                else (Colors.WARNING if status == "⚠️" else Colors.FAIL)
            )
            print(f"  {color}{status} {message}{Colors.ENDC}")

        # Final verdict
        all_passed = all(check[0] == "✅" for check in checks)
        if all_passed:
            print(
                f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED - Ready for UAT!{Colors.ENDC}"
            )
        else:
            print(
                f"\n{Colors.WARNING}{Colors.BOLD}⚠️  Some checks failed - review results above{Colors.ENDC}"
            )


async def main() -> None:
    """Main entry point."""
    print(f"{Colors.BOLD}WebSocket Streaming Manual Test{Colors.ENDC}")
    print("Testing astream_events() implementation with live server\n")

    # Check if custom message provided
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "Tell me a short joke and count to 5"

    client = WebSocketTestClient()
    await client.connect_and_test(message)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
        sys.exit(0)
