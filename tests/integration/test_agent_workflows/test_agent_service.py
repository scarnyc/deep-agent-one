"""
Integration tests for AgentService orchestration layer.

Tests the service that orchestrates agent creation, invocation, and lifecycle management.
"""

import pytest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from langgraph.graph.state import CompiledStateGraph

from backend.deep_agent.config.settings import Settings


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Fixture providing mocked Settings for agent service tests."""
    settings = Mock(spec=Settings)
    settings.ENV = "local"
    settings.OPENAI_API_KEY = "sk-test-key-12345"
    settings.GPT5_MODEL_NAME = "gpt-5"
    settings.GPT5_DEFAULT_REASONING_EFFORT = "medium"
    settings.GPT5_DEFAULT_VERBOSITY = "medium"
    settings.GPT5_MAX_TOKENS = 4096
    settings.GPT5_TEMPERATURE = 0.7
    settings.CHECKPOINT_DB_PATH = str(tmp_path / "test_service_checkpoints.db")
    settings.CHECKPOINT_CLEANUP_DAYS = 30
    settings.ENABLE_HITL = True
    settings.ENABLE_SUB_AGENTS = False
    return settings


@pytest.fixture
def mock_agent() -> CompiledStateGraph:
    """Fixture providing a mocked agent graph."""
    agent = Mock(spec=CompiledStateGraph)

    # Mock successful invocation
    async def mock_ainvoke(input_data: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        return {
            "messages": [
                {"role": "user", "content": input_data["messages"][0]["content"]},
                {"role": "assistant", "content": "Test response from agent"},
            ]
        }

    agent.ainvoke = AsyncMock(side_effect=mock_ainvoke)
    return agent


class TestAgentServiceCreation:
    """Test AgentService initialization and lifecycle."""

    @pytest.mark.asyncio
    async def test_create_agent_service_with_settings(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test creating AgentService with explicit settings."""
        from backend.deep_agent.services.agent_service import AgentService

        # Act
        service = AgentService(settings=mock_settings)

        # Assert
        assert service is not None
        assert service.settings == mock_settings
        assert service.agent is None  # Agent created lazily

    @pytest.mark.asyncio
    async def test_create_agent_service_without_settings_uses_defaults(self) -> None:
        """Test creating AgentService without settings uses get_settings()."""
        from backend.deep_agent.services.agent_service import AgentService

        with patch("backend.deep_agent.services.agent_service.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.ENV = "local"
            mock_settings.ENABLE_HITL = True
            mock_settings.ENABLE_SUB_AGENTS = False
            mock_get_settings.return_value = mock_settings

            # Act
            service = AgentService()

            # Assert
            assert service is not None
            mock_get_settings.assert_called_once()
            assert service.settings == mock_settings

    @pytest.mark.asyncio
    async def test_agent_service_initializes_agent_lazily(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test agent is not created until first use."""
        from backend.deep_agent.services.agent_service import AgentService

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            # Act - create service
            service = AgentService(settings=mock_settings)

            # Assert - agent not created yet
            assert service.agent is None
            mock_create.assert_not_called()


class TestAgentServiceInvocation:
    """Test agent invocation through AgentService."""

    @pytest.mark.asyncio
    async def test_invoke_agent_with_simple_message(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test invoking agent with a simple user message."""
        from backend.deep_agent.services.agent_service import AgentService

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)

            # Act
            result = await service.invoke(
                message="Hello, agent!",
                thread_id="test-thread-123"
            )

            # Assert
            assert result is not None
            assert "messages" in result
            assert len(result["messages"]) == 2
            assert result["messages"][1]["role"] == "assistant"
            assert "Test response" in result["messages"][1]["content"]

            # Verify agent was created
            mock_create.assert_called_once_with(settings=mock_settings, subagents=None)

            # Verify ainvoke was called with correct parameters
            mock_agent.ainvoke.assert_called_once()
            call_args = mock_agent.ainvoke.call_args
            assert call_args[0][0]["messages"][0]["content"] == "Hello, agent!"
            assert call_args[0][1]["configurable"]["thread_id"] == "test-thread-123"

    @pytest.mark.asyncio
    async def test_invoke_agent_with_thread_id_creates_config(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test thread_id is passed to agent config correctly."""
        from backend.deep_agent.services.agent_service import AgentService

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)

            # Act
            await service.invoke(
                message="Test message",
                thread_id="user-456"
            )

            # Assert
            call_args = mock_agent.ainvoke.call_args
            assert call_args[0][1]["configurable"]["thread_id"] == "user-456"

    @pytest.mark.asyncio
    async def test_invoke_agent_reuses_created_agent(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test agent is created once and reused for subsequent invocations."""
        from backend.deep_agent.services.agent_service import AgentService

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)

            # Act - invoke multiple times
            await service.invoke("Message 1", "thread-1")
            await service.invoke("Message 2", "thread-2")
            await service.invoke("Message 3", "thread-3")

            # Assert - create_agent called only once
            assert mock_create.call_count == 1

            # But ainvoke called three times
            assert mock_agent.ainvoke.call_count == 3


class TestAgentServiceStreaming:
    """Test streaming responses through AgentService."""

    @pytest.mark.asyncio
    async def test_stream_agent_response(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test streaming agent responses token by token."""
        from backend.deep_agent.services.agent_service import AgentService

        # Mock astream_events as async generator
        async def mock_astream(*args, **kwargs):
            yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Hello "}}}
            yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "world!"}}}
            yield {"event": "on_chat_model_end", "data": {}}

        mock_agent.astream_events = mock_astream

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)

            # Act
            chunks = []
            async for chunk in service.stream(
                message="Test streaming",
                thread_id="stream-thread-1"
            ):
                chunks.append(chunk)

            # Assert
            assert len(chunks) > 0
            # First chunk should contain "Hello "
            assert any("Hello" in str(chunk) for chunk in chunks)


class TestAgentServiceInputValidation:
    """Test input validation in AgentService."""

    @pytest.mark.asyncio
    async def test_invoke_rejects_empty_message(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test invoke raises ValueError for empty message."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await service.invoke(message="", thread_id="test-thread")

    @pytest.mark.asyncio
    async def test_invoke_rejects_whitespace_only_message(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test invoke raises ValueError for whitespace-only message."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await service.invoke(message="   ", thread_id="test-thread")

    @pytest.mark.asyncio
    async def test_invoke_rejects_empty_thread_id(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test invoke raises ValueError for empty thread_id."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Thread ID cannot be empty"):
            await service.invoke(message="Test message", thread_id="")

    @pytest.mark.asyncio
    async def test_invoke_rejects_whitespace_only_thread_id(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test invoke raises ValueError for whitespace-only thread_id."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Thread ID cannot be empty"):
            await service.invoke(message="Test message", thread_id="   ")

    @pytest.mark.asyncio
    async def test_stream_rejects_empty_message(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test stream raises ValueError for empty message."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Message cannot be empty"):
            async for _ in service.stream(message="", thread_id="test-thread"):
                pass  # Should not reach here

    @pytest.mark.asyncio
    async def test_stream_rejects_whitespace_only_message(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test stream raises ValueError for whitespace-only message."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Message cannot be empty"):
            async for _ in service.stream(message="   ", thread_id="test-thread"):
                pass  # Should not reach here

    @pytest.mark.asyncio
    async def test_stream_rejects_empty_thread_id(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test stream raises ValueError for empty thread_id."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Thread ID cannot be empty"):
            async for _ in service.stream(message="Test message", thread_id=""):
                pass  # Should not reach here

    @pytest.mark.asyncio
    async def test_stream_rejects_whitespace_only_thread_id(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test stream raises ValueError for whitespace-only thread_id."""
        from backend.deep_agent.services.agent_service import AgentService

        service = AgentService(settings=mock_settings)

        # Act & Assert
        with pytest.raises(ValueError, match="Thread ID cannot be empty"):
            async for _ in service.stream(message="Test message", thread_id="   "):
                pass  # Should not reach here

    @pytest.mark.asyncio
    async def test_stream_handles_agent_execution_failure(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test stream handles agent execution errors gracefully."""
        from backend.deep_agent.services.agent_service import AgentService

        # Mock astream_events to raise exception
        async def mock_astream_error(*args, **kwargs):
            raise RuntimeError("Streaming failed")
            yield  # Make it a generator (unreachable)

        mock_agent.astream_events = mock_astream_error

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)

            # Act & Assert
            with pytest.raises(RuntimeError, match="Streaming failed"):
                async for _ in service.stream("Test", "thread-1"):
                    pass  # Should not reach here


class TestAgentServiceErrorHandling:
    """Test error handling in AgentService."""

    @pytest.mark.asyncio
    async def test_invoke_handles_agent_creation_failure(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test service handles agent creation errors gracefully."""
        from backend.deep_agent.services.agent_service import AgentService

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.side_effect = ValueError("Invalid API key")

            service = AgentService(settings=mock_settings)

            # Act & Assert
            with pytest.raises(ValueError, match="Invalid API key"):
                await service.invoke("Test", "thread-1")

    @pytest.mark.asyncio
    async def test_invoke_handles_agent_execution_failure(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test service handles agent execution errors gracefully."""
        from backend.deep_agent.services.agent_service import AgentService

        mock_agent.ainvoke = AsyncMock(side_effect=RuntimeError("Execution failed"))

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)

            # Act & Assert
            with pytest.raises(RuntimeError, match="Execution failed"):
                await service.invoke("Test", "thread-1")


class TestAgentServiceConcurrency:
    """Test AgentService concurrency and thread safety."""

    @pytest.mark.asyncio
    async def test_concurrent_invocations_create_agent_once(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test concurrent invocations only create agent once (thread-safe)."""
        import asyncio
        from backend.deep_agent.services.agent_service import AgentService

        call_count = 0

        async def mock_create_agent(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate creation delay
            return mock_agent

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.side_effect = mock_create_agent

            service = AgentService(settings=mock_settings)

            # Act - invoke concurrently (should only create agent once)
            tasks = [
                service.invoke(f"Message {i}", f"thread-{i}")
                for i in range(5)
            ]
            await asyncio.gather(*tasks)

            # Assert - create_agent called exactly once despite concurrent calls
            assert call_count == 1
            assert mock_create.call_count == 1


class TestAgentServiceWithSubAgents:
    """Test AgentService with sub-agent support."""

    @pytest.mark.asyncio
    async def test_create_service_with_subagents_enabled(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test creating service with sub-agents enabled."""
        from backend.deep_agent.services.agent_service import AgentService

        mock_settings.ENABLE_SUB_AGENTS = True

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)
            await service.invoke("Test", "thread-1")

            # Assert - sub-agents list should be passed (empty list for Phase 0)
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert "subagents" in call_kwargs
            # Phase 0: empty list or None
            assert call_kwargs["subagents"] is None or call_kwargs["subagents"] == []

    @pytest.mark.asyncio
    async def test_create_service_with_subagents_disabled(
        self,
        mock_settings: Settings,
        mock_agent: CompiledStateGraph,
    ) -> None:
        """Test creating service with sub-agents disabled."""
        from backend.deep_agent.services.agent_service import AgentService

        mock_settings.ENABLE_SUB_AGENTS = False

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_create.return_value = mock_agent

            service = AgentService(settings=mock_settings)
            await service.invoke("Test", "thread-1")

            # Assert - subagents should be None
            mock_create.assert_called_once_with(settings=mock_settings, subagents=None)
