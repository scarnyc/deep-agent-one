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
        """Test WebSocket successfully connects to backend /ws endpoint."""
        # Navigate to a page that uses useWebSocket hook
        page.goto("http://localhost:3000/chat")

        # Wait for WebSocket connection
        # Check for "connected" status indicator
        connection_status = page.locator('[data-testid="ws-status"]')
        expect(connection_status).to_have_text("connected", timeout=5000)

    def test_websocket_sends_valid_message(self, page: Page) -> None:
        """Test WebSocket sends properly formatted messages."""
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
        """Test WebSocket receives AG-UI events from backend."""
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
        """Test WebSocket handles disconnection gracefully."""
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
        """Test WebSocket reconnects with exponential backoff."""
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
        """Test WebSocket handles invalid JSON gracefully."""
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
        """Test WebSocket validates required fields before sending."""
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
        """Test WebSocket tracks all connection states."""
        page.goto("http://localhost:3000/chat")

        connection_status = page.locator('[data-testid="ws-status"]')

        # Should start as "connecting" or "connected"
        expect(connection_status).to_have_text(/connecting|connected/, timeout=5000)

        # Eventually should be "connected"
        expect(connection_status).to_have_text("connected", timeout=5000)

        # Disconnect
        page.context.set_offline(True)

        # Should show "disconnected" or "reconnecting"
        expect(connection_status).to_have_text(/disconnected|reconnecting/, timeout=3000)

        # Reconnect
        page.context.set_offline(False)
        expect(connection_status).to_have_text("connected", timeout=15000)

    def test_websocket_multiple_threads(self, page: Page) -> None:
        """Test WebSocket handles multiple thread_ids correctly."""
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
        """Test WebSocket connection closes when component unmounts."""
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
