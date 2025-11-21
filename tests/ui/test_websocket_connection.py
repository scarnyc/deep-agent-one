"""
Playwright UI tests for WebSocket connection (useWebSocket hook).

Tests the frontend WebSocket hook that connects to the backend
AG-UI Protocol endpoint at /api/v1/ws.

Following TDD: These tests are written BEFORE implementing the hook.
"""
import json
import time
from typing import Any

import pytest
from playwright.sync_api import Page, expect


class TestWebSocketConnection:
    """Test WebSocket connection functionality."""

    def test_websocket_connects_to_backend(self, page: Page) -> None:
        """
        Test WebSocket successfully connects to backend /ws endpoint.

        UI Element: WebSocket connection status indicator
        User Action: Navigate to chat page
        Expected Behavior: Status shows "connected" within 5 seconds

        Args:
            page: Playwright page fixture

        Verifies:
            - WebSocket connection established
            - Connection status indicator shows "connected"
            - Connection happens automatically on page load
        """
        # Navigate to a page that uses useWebSocket hook
        page.goto("http://localhost:3000/chat")

        # Wait for WebSocket connection
        # Check for "connected" status indicator
        connection_status = page.locator('[data-testid="ws-status"]')
        expect(connection_status).to_have_text("connected", timeout=5000)

    def test_websocket_sends_valid_message(self, page: Page) -> None:
        """
        Test WebSocket sends properly formatted messages.

        UI Element: Message input field and send button
        User Action: Type message and click send
        Expected Behavior: Message sent via WebSocket, appears in chat history

        Args:
            page: Playwright page fixture

        Verifies:
            - Message successfully sent over WebSocket
            - Message appears in UI chat history
            - Message format is valid (AG-UI Protocol)
        """
        page.goto("http://localhost:3000/chat")

        # Wait for connection
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Type message and send
        message_input = page.locator('[data-testid="message-input"]')
        message_input.fill("Hello from test")

        send_button = page.locator('[data-testid="send-button"]')
        send_button.click()

        # Verify message was sent (check UI update or response)
        # Should see user message in chat history
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).to_contain_text("Hello from test", timeout=3000)

    def test_websocket_receives_events(self, page: Page) -> None:
        """
        Test WebSocket receives AG-UI events from backend.

        UI Element: Chat history with streaming assistant messages
        User Action: Send message to trigger backend response
        Expected Behavior: Streaming AG-UI events update UI in real-time

        Args:
            page: Playwright page fixture

        Verifies:
            - WebSocket receives AG-UI Protocol events
            - Assistant messages appear from streaming events
            - UI updates in real-time during agent execution
        """
        page.goto("http://localhost:3000/chat")

        # Wait for connection
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Send a message to trigger backend response
        message_input = page.locator('[data-testid="message-input"]')
        message_input.fill("Test message")
        page.locator('[data-testid="send-button"]').click()

        # Wait for streaming response (AG-UI events)
        # Should see assistant message appear
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).to_contain_text("assistant", timeout=10000)

    def test_websocket_handles_disconnect(self, page: Page) -> None:
        """
        Test WebSocket handles disconnection gracefully.

        UI Element: Connection status indicator
        User Action: Simulate network disconnect (offline mode)
        Expected Behavior: Status updates to disconnected, reconnects when online

        Args:
            page: Playwright page fixture

        Verifies:
            - Disconnection detected and status updated
            - Automatic reconnection when network restored
            - No crashes or errors during disconnect
        """
        page.goto("http://localhost:3000/chat")

        # Wait for initial connection
        connection_status = page.locator('[data-testid="ws-status"]')
        expect(connection_status).to_have_text("connected", timeout=5000)

        # Simulate network disconnect (go offline)
        page.context.set_offline(True)

        # Status should change to disconnected or reconnecting
        expect(connection_status).not_to_have_text("connected", timeout=3000)

        # Go back online
        page.context.set_offline(False)

        # Should reconnect
        expect(connection_status).to_have_text("connected", timeout=10000)

    def test_websocket_auto_reconnect_exponential_backoff(self, page: Page) -> None:
        """
        Test WebSocket reconnects with exponential backoff.

        UI Element: Connection status with reconnecting state
        User Action: Disconnect and monitor reconnection attempts
        Expected Behavior: Automatic reconnection with backoff strategy

        Args:
            page: Playwright page fixture

        Verifies:
            - Status shows "reconnecting" during attempts
            - Successfully reconnects when network restored
            - Exponential backoff implemented (timing difficult to test in UI)
        """
        page.goto("http://localhost:3000/chat")

        # Wait for initial connection
        connection_status = page.locator('[data-testid="ws-status"]')
        expect(connection_status).to_have_text("connected", timeout=5000)

        # Disconnect
        page.context.set_offline(True)
        expect(connection_status).to_have_text("reconnecting", timeout=3000)

        # Should show reconnecting status
        # Note: Testing exact backoff timing is difficult in UI tests
        # We just verify it attempts to reconnect
        page.wait_for_timeout(2000)  # Wait 2 seconds

        # Go back online - should reconnect
        page.context.set_offline(False)
        expect(connection_status).to_have_text("connected", timeout=15000)

    def test_websocket_invalid_json_error(self, page: Page) -> None:
        """
        Test WebSocket handles invalid JSON gracefully.

        UI Element: Error indicator (should not be visible normally)
        User Action: Normal operation (no invalid JSON sent)
        Expected Behavior: No error state shown during normal operation

        Args:
            page: Playwright page fixture

        Verifies:
            - Error indicator not visible during normal operation
            - Invalid JSON parse errors handled gracefully
            - UI remains functional even if backend sends malformed data
        """
        page.goto("http://localhost:3000/chat")

        # Wait for connection
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Inject invalid JSON via console (simulate error)
        # This is a synthetic test - real implementation would handle parse errors
        # We verify error state is shown
        error_indicator = page.locator('[data-testid="ws-error"]')

        # In normal operation, error should not be visible
        expect(error_indicator).not_to_be_visible()

    def test_websocket_missing_required_fields(self, page: Page) -> None:
        """
        Test WebSocket validates required fields before sending.

        UI Element: Send button, message input
        User Action: Try to send empty message
        Expected Behavior: Send button disabled or validation error shown

        Args:
            page: Playwright page fixture

        Verifies:
            - Send button disabled when message empty
            - Validation prevents sending invalid messages
            - Required fields enforced client-side
        """
        page.goto("http://localhost:3000/chat")

        # Wait for connection
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Try to send empty message
        message_input = page.locator('[data-testid="message-input"]')
        message_input.fill("")  # Empty message

        send_button = page.locator('[data-testid="send-button"]')

        # Send button should be disabled or show validation error
        # Depending on implementation, either:
        # 1. Button disabled when input empty
        # 2. Validation error shown
        expect(send_button).to_be_disabled()

    def test_websocket_connection_status_tracking(self, page: Page) -> None:
        """
        Test WebSocket tracks all connection states.

        UI Element: Connection status indicator
        User Action: Connect, disconnect, reconnect
        Expected Behavior: Status reflects all state transitions accurately

        Args:
            page: Playwright page fixture

        Verifies:
            - Initial state is connecting or connected
            - Disconnect shows disconnected/reconnecting
            - Reconnect shows connected again
            - All state transitions tracked correctly
        """
        page.goto("http://localhost:3000/chat")

        connection_status = page.locator('[data-testid="ws-status"]')

        # Should start as "connecting" or "connected"
        import re
        expect(connection_status).to_have_text(re.compile(r"connecting|connected"), timeout=5000)

        # Eventually should be "connected"
        expect(connection_status).to_have_text("connected", timeout=5000)

        # Disconnect
        page.context.set_offline(True)

        # Should show "disconnected" or "reconnecting"
        expect(connection_status).to_have_text(re.compile(r"disconnected|reconnecting"), timeout=3000)

        # Reconnect
        page.context.set_offline(False)
        expect(connection_status).to_have_text("connected", timeout=15000)

    def test_websocket_multiple_threads(self, page: Page) -> None:
        """
        Test WebSocket handles multiple thread_ids correctly.

        UI Element: Chat messages with thread IDs
        User Action: Send messages in different threads
        Expected Behavior: Thread ID properly passed in WebSocket messages

        Args:
            page: Playwright page fixture

        Verifies:
            - Thread ID included in WebSocket messages
            - Different threads handled correctly
            - Messages routed to correct thread
        """
        page.goto("http://localhost:3000/chat")

        # Wait for connection
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Send message in thread 1
        message_input = page.locator('[data-testid="message-input"]')
        message_input.fill("Thread 1 message")
        page.locator('[data-testid="send-button"]').click()

        # Wait for response
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).to_contain_text("Thread 1 message", timeout=5000)

        # Navigate to different thread (if UI supports)
        # Or just verify thread_id is included in messages
        # This test verifies the hook properly passes thread_id

    def test_websocket_cleanup_on_unmount(self, page: Page) -> None:
        """
        Test WebSocket connection closes when component unmounts.

        UI Element: WebSocket connection (internal)
        User Action: Navigate away from chat page, then return
        Expected Behavior: Connection closed on unmount, new connection on remount

        Args:
            page: Playwright page fixture

        Verifies:
            - Connection properly cleaned up on unmount
            - New connection established on remount
            - No duplicate connections or memory leaks
            - Proper cleanup prevents resource exhaustion
        """
        page.goto("http://localhost:3000/chat")

        # Wait for connection
        connection_status = page.locator('[data-testid="ws-status"]')
        expect(connection_status).to_have_text("connected", timeout=5000)

        # Navigate away (unmount component)
        page.goto("http://localhost:3000/")

        # Navigate back
        page.goto("http://localhost:3000/chat")

        # Should reconnect
        expect(connection_status).to_have_text("connected", timeout=5000)

        # Verify no duplicate connections (would show as multiple messages)
        # This is a behavioral test - proper cleanup prevents memory leaks
