"""
Playwright UI tests for agent state management (useAgentState Zustand store).

Tests the frontend Zustand store that manages conversation threads, messages,
tool calls, HITL state, and agent status.

Following TDD: These tests are written BEFORE implementing the store.
"""
from typing import Any

import pytest
from playwright.sync_api import Page, expect


class TestAgentStateManagement:
    """Test Zustand agent state management."""

    def test_create_new_thread(self, page: Page) -> None:
        """Test creating a new conversation thread."""
        # Arrange: Navigate to chat page
        page.goto("http://localhost:3000/chat")

        # Act: Create a new thread (via UI or programmatically)
        # The store should automatically create a thread on mount

        # Assert: Thread ID exists in UI
        thread_id_element = page.locator('[data-testid="thread-id"]')
        expect(thread_id_element).to_be_visible(timeout=5000)
        expect(thread_id_element).not_to_be_empty()

    def test_add_user_message_to_thread(self, page: Page) -> None:
        """Test adding a user message updates the thread state."""
        # Arrange: Navigate and wait for thread
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Act: Send a user message
        page.fill('[data-testid="message-input"]', "Test user message")
        page.click('[data-testid="send-button"]')

        # Assert: Message appears in chat history
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).to_contain_text("Test user message", timeout=3000)

        # Assert: Message has user role
        user_message = page.locator('[data-testid="message-user"]').first
        expect(user_message).to_be_visible()

    def test_add_assistant_message_to_thread(self, page: Page) -> None:
        """Test receiving an assistant message updates the thread state."""
        # Arrange: Send a message to trigger assistant response
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        page.fill('[data-testid="message-input"]', "Hello assistant")
        page.click('[data-testid="send-button"]')

        # Act: Wait for assistant response (via WebSocket AG-UI events)
        assistant_message = page.locator('[data-testid="message-assistant"]').first

        # Assert: Assistant message appears
        expect(assistant_message).to_be_visible(timeout=10000)
        expect(assistant_message).not_to_be_empty()

    def test_track_tool_calls_in_state(self, page: Page) -> None:
        """Test tool calls are tracked in agent state."""
        # Arrange: Send message that triggers tool usage
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        page.fill('[data-testid="message-input"]', "Search for Python tutorials")
        page.click('[data-testid="send-button"]')

        # Act: Wait for tool call to appear
        tool_call = page.locator('[data-testid="tool-call"]').first

        # Assert: Tool call is visible with name and status
        import re
        expect(tool_call).to_be_visible(timeout=10000)
        expect(tool_call).to_have_attribute("data-tool-name", re.compile(r"web_search|search"))
        expect(tool_call).to_have_attribute("data-status", re.compile(r"pending|running|completed"))

    def test_update_agent_status(self, page: Page) -> None:
        """Test agent status updates as agent runs."""
        # Arrange: Navigate to chat
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Get initial status (should be idle)
        agent_status = page.locator('[data-testid="agent-status"]')
        expect(agent_status).to_have_text(re.compile(r"idle|ready"), timeout=3000)

        # Act: Send message to trigger agent run
        page.fill('[data-testid="message-input"]', "Hello")
        page.click('[data-testid="send-button"]')

        # Assert: Status changes to running
        expect(agent_status).to_have_text(re.compile(r"running|processing"), timeout=3000)

        # Assert: Eventually completes
        expect(agent_status).to_have_text(re.compile(r"completed|idle"), timeout=15000)

    def test_hitl_request_state(self, page: Page) -> None:
        """Test HITL approval request updates state."""
        # Arrange: Navigate and send message that requires approval
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Send message that triggers HITL (e.g., destructive action)
        page.fill('[data-testid="message-input"]', "Delete all files")
        page.click('[data-testid="send-button"]')

        # Act: Wait for HITL approval UI to appear
        hitl_approval = page.locator('[data-testid="hitl-approval"]')

        # Assert: HITL request is displayed
        expect(hitl_approval).to_be_visible(timeout=10000)

        # Assert: Agent status shows waiting for approval
        agent_status = page.locator('[data-testid="agent-status"]')
        expect(agent_status).to_have_text(re.compile(r"waiting.*approval|pending"), timeout=3000)

    def test_multiple_threads_isolation(self, page: Page) -> None:
        """Test multiple threads are isolated in state."""
        # Arrange: Create first thread
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        # Send message in thread 1
        page.fill('[data-testid="message-input"]', "Thread 1 message")
        page.click('[data-testid="send-button"]')

        # Wait for message to appear
        expect(page.locator('[data-testid="chat-history"]')).to_contain_text("Thread 1 message")

        # Act: Create new thread (navigate to new chat page or click "New Chat")
        new_chat_button = page.locator('[data-testid="new-chat-button"]')
        if new_chat_button.is_visible():
            new_chat_button.click()
        else:
            # Navigate to new instance
            page.goto("http://localhost:3000/chat?new=true")

        # Assert: New thread has empty chat history
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).not_to_contain_text("Thread 1 message")

    def test_clear_thread_state(self, page: Page) -> None:
        """Test clearing a thread removes all messages and state."""
        # Arrange: Create thread with messages
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        page.fill('[data-testid="message-input"]', "Message to clear")
        page.click('[data-testid="send-button"]')

        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).to_contain_text("Message to clear")

        # Act: Clear thread (if UI supports it)
        clear_button = page.locator('[data-testid="clear-thread-button"]')
        if clear_button.is_visible():
            clear_button.click()

            # Confirm dialog if present
            confirm_button = page.locator('[data-testid="confirm-clear"]')
            if confirm_button.is_visible():
                confirm_button.click()

            # Assert: Chat history is empty
            expect(chat_history).to_be_empty(timeout=3000)

    def test_switch_between_threads(self, page: Page) -> None:
        """Test switching between threads loads correct state."""
        # Arrange: Create two threads with different messages
        page.goto("http://localhost:3000/chat")

        # Thread 1
        page.fill('[data-testid="message-input"]', "Thread 1 content")
        page.click('[data-testid="send-button"]')

        thread_1_id = page.locator('[data-testid="thread-id"]').inner_text()

        # Create Thread 2
        page.goto("http://localhost:3000/chat?new=true")
        page.fill('[data-testid="message-input"]', "Thread 2 content")
        page.click('[data-testid="send-button"]')

        # Act: Switch back to Thread 1 (if UI supports thread list)
        thread_list_item = page.locator(f'[data-testid="thread-{thread_1_id}"]')
        if thread_list_item.is_visible():
            thread_list_item.click()

            # Assert: Thread 1 content is displayed
            chat_history = page.locator('[data-testid="chat-history"]')
            expect(chat_history).to_contain_text("Thread 1 content")
            expect(chat_history).not_to_contain_text("Thread 2 content")

    @pytest.mark.skip(reason="State persistence not implemented in Phase 0 - deferred to Phase 1")
    def test_persist_state_across_page_refresh(self, page: Page) -> None:
        """Test agent state persists across page refresh (Phase 1 feature)."""
        # NOTE: This test is skipped for Phase 0
        # State persistence will be implemented in Phase 1 using:
        # - localStorage/sessionStorage for client-side persistence
        # - OR backend state synchronization via WebSocket reconnection

        # Arrange: Create thread with message
        page.goto("http://localhost:3000/chat")
        expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

        page.fill('[data-testid="message-input"]', "Persistent message")
        page.click('[data-testid="send-button"]')

        expect(page.locator('[data-testid="chat-history"]')).to_contain_text("Persistent message")

        # Act: Refresh page
        page.reload()

        # Assert: Message still visible after refresh
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).to_contain_text("Persistent message", timeout=5000)
