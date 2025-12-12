"""
Integration tests for timeout handling across HTTP and WebSocket endpoints.

Tests verify that:
1. WebSocket connections are excluded from HTTP timeout middleware (30s)
2. REST endpoints still have HTTP timeout protection (30s)
3. WebSocket respects STREAM_TIMEOUT_SECONDS (180s)
"""

import asyncio
from unittest.mock import patch

import pytest
from deep_agent.main import create_app
from fastapi import status
from fastapi.testclient import TestClient


class TestTimeoutMiddleware:
    """Tests for TimeoutMiddleware configuration and behavior."""

    @pytest.mark.asyncio
    async def test_websocket_excluded_from_http_timeout(self):
        """
        Test that WebSocket connections are excluded from HTTP timeout middleware.

        Scenario:
        - WebSocket operation takes 45 seconds (exceeds HTTP timeout of 30s)
        - Should complete successfully because WebSocket is excluded from HTTP timeout
        - Uses STREAM_TIMEOUT_SECONDS (180s) instead
        """
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Mock agent service to take 45 seconds (exceeds HTTP timeout)
        async def slow_stream(*args, **kwargs):
            """Simulate slow streaming that takes longer than HTTP timeout."""
            await asyncio.sleep(45)
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": {"content": "Result after 45s"}},
            }

        with patch("deep_agent.services.agent_service.AgentService.stream", new=slow_stream):
            # Act
            with client.websocket_connect("/api/v1/ws") as websocket:
                websocket.send_json({"type": "chat", "message": "test", "thread_id": "test-123"})

                # Should complete without timeout (WebSocket excluded from 30s HTTP timeout)
                data = websocket.receive_json(timeout=50)

        # Assert
        assert data["event"] == "on_chat_model_stream"
        assert "Result after 45s" in str(data)

    def test_rest_endpoint_has_http_timeout(self):
        """
        Test that REST endpoints still have 30s HTTP timeout.

        Scenario:
        - REST endpoint takes 35 seconds (exceeds HTTP timeout of 30s)
        - Should return 504 Gateway Timeout after 30s
        """
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Create a slow endpoint for testing
        @app.get("/test/slow")
        async def slow_endpoint():
            """Slow endpoint for timeout testing."""
            await asyncio.sleep(35)
            return {"status": "ok"}

        # Act
        response = client.get("/test/slow", timeout=35)

        # Assert
        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert "timeout" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_websocket_respects_stream_timeout(self):
        """
        Test that WebSocket still respects STREAM_TIMEOUT_SECONDS (180s).

        Scenario:
        - WebSocket operation takes 200 seconds (exceeds STREAM_TIMEOUT_SECONDS)
        - Should receive timeout error from agent service
        """
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Mock agent service to exceed STREAM_TIMEOUT_SECONDS
        async def very_slow_stream(*args, **kwargs):
            """Simulate streaming that exceeds stream timeout."""
            await asyncio.sleep(200)  # Exceeds 180s STREAM_TIMEOUT_SECONDS
            yield {"event": "on_chat_model_stream", "data": {}}

        with patch(
            "deep_agent.services.agent_service.AgentService.stream",
            new=very_slow_stream,
        ):
            # Act
            with client.websocket_connect("/api/v1/ws") as websocket:
                websocket.send_json({"type": "chat", "message": "test", "thread_id": "test-123"})

                # Should receive timeout error from agent service
                data = websocket.receive_json(timeout=185)

        # Assert - should receive on_error event
        assert data["event"] == "on_error"
        assert "timeout" in data["data"]["error"].lower()


class TestWebSearchTimeout:
    """Tests for web search tool timeout behavior."""

    @pytest.mark.asyncio
    async def test_web_search_completes_within_websocket_timeout(self):
        """
        Test that web search operations complete within WebSocket timeout.

        Scenario:
        - Web search takes 25 seconds (within WEB_SEARCH_TIMEOUT of 30s)
        - Should complete successfully via WebSocket
        - WebSocket timeout (180s) is not reached
        """
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Mock web search tool to take 25 seconds
        async def realistic_web_search(*args, **kwargs):
            """Simulate realistic web search duration."""
            await asyncio.sleep(25)
            yield {
                "event": "on_tool_end",
                "data": {"output": {"results": [{"title": "Result 1", "content": "Test content"}]}},
            }

        with patch(
            "deep_agent.tools.web_search.WebSearchTool._arun",
            new=realistic_web_search,
        ):
            # Act
            with client.websocket_connect("/api/v1/ws") as websocket:
                websocket.send_json(
                    {
                        "type": "chat",
                        "message": "Search the web for quantum computing",
                        "thread_id": "test-search-123",
                    }
                )

                # Should receive search results within timeout
                data = websocket.receive_json(timeout=30)

        # Assert
        assert data["event"] == "on_tool_end"
        assert "results" in str(data["data"])

    @pytest.mark.asyncio
    async def test_web_search_timeout_handled_gracefully(self):
        """
        Test that web search timeout is handled gracefully.

        Scenario:
        - Web search takes 35 seconds (exceeds WEB_SEARCH_TIMEOUT of 30s)
        - Should receive error message via WebSocket
        - WebSocket connection remains open
        """
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Mock web search tool to timeout
        async def timeout_web_search(*args, **kwargs):
            """Simulate web search timeout."""
            await asyncio.sleep(35)
            # In reality, this would be cancelled by WEB_SEARCH_TIMEOUT
            raise TimeoutError("Search timed out")

        with patch("deep_agent.tools.web_search.WebSearchTool._arun", new=timeout_web_search):
            # Act
            with client.websocket_connect("/api/v1/ws") as websocket:
                websocket.send_json(
                    {
                        "type": "chat",
                        "message": "Search the web for test",
                        "thread_id": "test-timeout-123",
                    }
                )

                # Should receive error event
                data = websocket.receive_json(timeout=40)

        # Assert - should receive on_error or on_tool_error event
        assert data["event"] in ["on_error", "on_tool_error"]
        assert "timeout" in str(data["data"]).lower() or "timed out" in str(data["data"]).lower()


class TestTimeoutHierarchy:
    """Tests for timeout hierarchy and configuration validation."""

    def test_timeout_hierarchy_logged_at_startup(self, caplog):
        """
        Test that timeout hierarchy is logged at application startup.

        Verifies that diagnostic logging provides clear timeout configuration.
        """
        # Arrange & Act
        app = create_app()

        # Assert - check logs for timeout hierarchy
        assert "Timeout configuration summary" in caplog.text
        assert "http_timeout_seconds" in caplog.text
        assert "stream_timeout_seconds" in caplog.text
        assert "web_search_timeout_seconds" in caplog.text
        assert "WebSocket excluded from HTTP timeout" in caplog.text

    def test_stream_timeout_greater_than_http_timeout(self):
        """
        Test configuration validation: STREAM_TIMEOUT_SECONDS > HTTP timeout.

        This is a critical requirement to prevent premature WebSocket timeouts.
        """
        # Arrange
        from deep_agent.core.config import settings

        # Assert
        http_timeout = 30  # From TimeoutMiddleware
        stream_timeout = settings.STREAM_TIMEOUT_SECONDS

        assert (
            stream_timeout > http_timeout
        ), f"STREAM_TIMEOUT_SECONDS ({stream_timeout}s) must be > HTTP timeout ({http_timeout}s)"

    def test_web_search_timeout_within_stream_timeout(self):
        """
        Test configuration validation: WEB_SEARCH_TIMEOUT < STREAM_TIMEOUT_SECONDS.

        Web search should complete before WebSocket stream timeout.
        """
        # Arrange
        from deep_agent.core.config import settings

        # Assert
        web_search_timeout = settings.WEB_SEARCH_TIMEOUT
        stream_timeout = settings.STREAM_TIMEOUT_SECONDS

        assert (
            web_search_timeout < stream_timeout
        ), f"WEB_SEARCH_TIMEOUT ({web_search_timeout}s) must be < STREAM_TIMEOUT_SECONDS ({stream_timeout}s)"
