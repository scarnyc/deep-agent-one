"""
Unit tests for DeepAgent creation and configuration.

Tests the create_agent() function that wraps LangChain's create_deep_agent() API
with our configuration, LLM factory, and checkpointer integration.

Note: Since deepagents package is not yet installed, these tests verify the setup
      logic and integration points. Tests will pass once deepagents is installed.
"""

import pytest
import sys
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock, call
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from backend.deep_agent.config.settings import Settings, get_settings
from backend.deep_agent.agents.checkpointer import CheckpointerManager


# Test fixtures


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Fixture providing mocked Settings with temp paths."""
    settings = Mock(spec=Settings)
    settings.ENV = "local"  # Required for prompts module
    settings.OPENAI_API_KEY = "sk-test-key-12345"
    settings.LANGSMITH_API_KEY = "test-langsmith-key"
    settings.LANGSMITH_PROJECT = "test-project"
    settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
    settings.LANGSMITH_TRACING_V2 = True
    settings.GPT5_MODEL_NAME = "gpt-5"
    settings.GPT5_DEFAULT_REASONING_EFFORT = "medium"
    settings.GPT5_DEFAULT_VERBOSITY = "medium"  # Valid values: low, medium, high
    settings.GPT5_MAX_TOKENS = 4096
    settings.GPT5_TEMPERATURE = 0.7
    settings.CHECKPOINT_DB_PATH = str(tmp_path / "test_checkpoints.db")
    settings.CHECKPOINT_CLEANUP_DAYS = 30
    settings.ENABLE_HITL = True
    settings.ENABLE_SUB_AGENTS = True
    return settings


@pytest.fixture
def mock_llm() -> ChatOpenAI:
    """Fixture providing a mocked ChatOpenAI instance."""
    llm = Mock(spec=ChatOpenAI)
    llm.model_name = "gpt-5"
    llm.temperature = 0.7
    llm.max_tokens = 4096
    return llm


@pytest.fixture
def mock_checkpointer() -> AsyncSqliteSaver:
    """Fixture providing a mocked AsyncSqliteSaver checkpointer."""
    checkpointer = AsyncMock(spec=AsyncSqliteSaver)
    checkpointer.setup = AsyncMock()
    return checkpointer


@pytest.fixture
def mock_compiled_graph() -> CompiledStateGraph:
    """Fixture providing a mocked CompiledStateGraph."""
    graph = Mock(spec=CompiledStateGraph)
    graph.nodes = ["__start__", "agent", "__end__"]
    graph.edges = [("__start__", "agent"), ("agent", "__end__")]
    graph.get_graph = Mock(return_value=Mock(nodes=[], edges=[]))

    # Mock async invocation
    async def mock_ainvoke(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"messages": [{"role": "assistant", "content": "Test response"}]}

    graph.ainvoke = AsyncMock(side_effect=mock_ainvoke)
    return graph


@pytest.fixture
def mock_deepagents_module(mock_compiled_graph: CompiledStateGraph) -> Mock:
    """Fixture that mocks the entire deepagents module."""
    mock_module = Mock()

    # Mock create_deep_agent function
    mock_agent = Mock()
    mock_agent.compile = Mock(return_value=mock_compiled_graph)
    mock_module.create_deep_agent = Mock(return_value=mock_agent)

    return mock_module


# Helper function to setup common mocks


def setup_mocks(
    mock_settings: Settings,
    mock_llm: ChatOpenAI,
    mock_checkpointer: AsyncSqliteSaver,
    mock_compiled_graph: CompiledStateGraph,
) -> tuple[Mock, Mock]:
    """Set up common mocks for tests."""
    # Mock CheckpointerManager
    mock_manager = AsyncMock()
    mock_manager.create_checkpointer = AsyncMock(return_value=mock_checkpointer)
    mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
    mock_manager.__aexit__ = AsyncMock()

    # Mock deep agent
    mock_deep_agent = Mock()
    mock_deep_agent.compile = Mock(return_value=mock_compiled_graph)

    return mock_manager, mock_deep_agent


# Test classes


class TestCreateAgentBasics:
    """Test basic agent creation functionality."""

    @pytest.mark.asyncio
    async def test_create_agent_with_default_settings_uses_get_settings(
        self,
        mock_llm: ChatOpenAI,
    ) -> None:
        """Test agent creation falls back to get_settings() when no settings provided."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        # Mock get_settings to return a valid settings object
        test_settings = Mock(spec=Settings)
        test_settings.ENV = "local"  # Required for prompts module
        test_settings.OPENAI_API_KEY = "sk-test-key"
        test_settings.LANGSMITH_API_KEY = "test-langsmith-key"
        test_settings.LANGSMITH_PROJECT = "test-project"
        test_settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
        test_settings.LANGSMITH_TRACING_V2 = True
        test_settings.GPT5_MODEL_NAME = "gpt-5"
        test_settings.GPT5_DEFAULT_REASONING_EFFORT = "medium"
        test_settings.GPT5_DEFAULT_VERBOSITY = "medium"
        test_settings.GPT5_MAX_TOKENS = 4096
        test_settings.GPT5_TEMPERATURE = 0.7
        test_settings.CHECKPOINT_DB_PATH = "/tmp/test.db"
        test_settings.CHECKPOINT_CLEANUP_DAYS = 30
        test_settings.ENABLE_HITL = True
        test_settings.ENABLE_SUB_AGENTS = True

        with patch("backend.deep_agent.agents.deep_agent.get_settings") as mock_get_settings:
            mock_get_settings.return_value = test_settings

            # Act - should use get_settings()
            agent = await create_agent()

            # Verify get_settings was called
            mock_get_settings.assert_called_once()

            # Assert agent was created
            assert agent is not None
            assert isinstance(agent, CompiledStateGraph)


class TestLLMIntegration:
    """Test LLM integration via llm_factory."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    async def test_agent_creates_llm_from_factory(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        """Test agent creation calls LLM factory with correct parameters."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_llm_factory.return_value = mock_llm

        # Act
        try:
            await create_agent(settings=mock_settings)
        except NotImplementedError:
            pass  # Expected since deepagents isn't installed

        # Assert - verify LLM factory was called with API key and config
        mock_llm_factory.assert_called_once()
        call_kwargs = mock_llm_factory.call_args.kwargs

        # Check API key was passed
        assert "api_key" in call_kwargs
        assert call_kwargs["api_key"] == mock_settings.OPENAI_API_KEY

        # Check config was passed
        assert "config" in call_kwargs
        config = call_kwargs["config"]
        assert config.model_name == mock_settings.GPT5_MODEL_NAME
        assert config.reasoning_effort.value == mock_settings.GPT5_DEFAULT_REASONING_EFFORT

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    async def test_agent_uses_custom_reasoning_effort_from_settings(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        """Test agent respects custom reasoning effort from settings."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_settings.GPT5_DEFAULT_REASONING_EFFORT = "high"
        mock_llm_factory.return_value = mock_llm

        # Act
        try:
            await create_agent(settings=mock_settings)
        except NotImplementedError:
            pass  # Expected

        # Assert
        mock_llm_factory.assert_called_once()
        config = mock_llm_factory.call_args.kwargs["config"]
        assert config.reasoning_effort.value == "high"


class TestCheckpointerIntegration:
    """Test checkpointer integration for state persistence."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    @patch("backend.deep_agent.agents.deep_agent.CheckpointerManager")
    async def test_agent_creates_checkpointer_manager(
        self,
        mock_checkpointer_manager_class: Mock,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
        mock_checkpointer: AsyncSqliteSaver,
    ) -> None:
        """Test agent creation instantiates CheckpointerManager."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_llm_factory.return_value = mock_llm

        # Mock CheckpointerManager
        mock_manager = AsyncMock()
        mock_manager.create_checkpointer = AsyncMock(return_value=mock_checkpointer)
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.__aexit__ = AsyncMock()
        mock_checkpointer_manager_class.return_value = mock_manager

        # Act
        try:
            await create_agent(settings=mock_settings)
        except NotImplementedError:
            pass  # Expected

        # Assert - verify CheckpointerManager was created with settings
        mock_checkpointer_manager_class.assert_called_once_with(settings=mock_settings)
        mock_manager.create_checkpointer.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    @patch("backend.deep_agent.agents.deep_agent.CheckpointerManager")
    async def test_checkpointer_manager_context_cleanup(
        self,
        mock_checkpointer_manager_class: Mock,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
        mock_checkpointer: AsyncSqliteSaver,
    ) -> None:
        """Test CheckpointerManager context manager cleans up properly."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_llm_factory.return_value = mock_llm

        # Mock CheckpointerManager
        mock_manager = AsyncMock()
        mock_manager.create_checkpointer = AsyncMock(return_value=mock_checkpointer)
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.__aexit__ = AsyncMock()
        mock_checkpointer_manager_class.return_value = mock_manager

        # Act
        try:
            await create_agent(settings=mock_settings)
        except NotImplementedError:
            pass  # Expected

        # Assert - verify context manager was used (enter and exit called)
        mock_manager.__aenter__.assert_called_once()
        mock_manager.__aexit__.assert_called_once()


class TestSubAgentSupport:
    """Test sub-agent delegation support."""

    @pytest.mark.asyncio
    async def test_create_agent_accepts_subagents_parameter(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test create_agent accepts None subagents parameter."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        # Act - should accept None subagents and create agent
        agent = await create_agent(settings=mock_settings, subagents=None)

        # Assert
        assert agent is not None
        assert isinstance(agent, CompiledStateGraph)

    @pytest.mark.asyncio
    async def test_create_agent_logs_subagent_count(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test agent creation logs when no subagents provided."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        # Act
        with patch("backend.deep_agent.agents.deep_agent.logger") as mock_logger:
            agent = await create_agent(settings=mock_settings, subagents=None)

            # Assert - verify logging occurred with subagent count 0
            mock_logger.info.assert_called()
            # Find the call that logs agent creation
            for call_obj in mock_logger.info.call_args_list:
                if "Creating DeepAgent" in str(call_obj):
                    assert call_obj[1]["subagents_count"] == 0
                    break

            # Assert agent was created
            assert agent is not None


class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    async def test_create_agent_missing_api_key_raises_error(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
    ) -> None:
        """Test creating agent with missing API key raises ValueError."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_settings.OPENAI_API_KEY = ""
        mock_llm_factory.side_effect = ValueError("API key is required")

        # Act & Assert
        with pytest.raises(ValueError, match="API key is required"):
            await create_agent(settings=mock_settings)

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    @patch("backend.deep_agent.agents.deep_agent.CheckpointerManager")
    async def test_create_agent_checkpointer_failure_raises_error(
        self,
        mock_checkpointer_manager_class: Mock,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        """Test checkpointer creation failure is propagated."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_llm_factory.return_value = mock_llm

        # Mock CheckpointerManager to raise error on create_checkpointer
        mock_manager = AsyncMock()
        mock_manager.create_checkpointer = AsyncMock(
            side_effect=OSError("Cannot create database")
        )
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        # Important: __aexit__ should return None (not suppress exception)
        async def mock_aexit(*args):
            return None
        mock_manager.__aexit__ = mock_aexit
        mock_checkpointer_manager_class.return_value = mock_manager

        # Act & Assert
        with pytest.raises(OSError, match="Cannot create database"):
            await create_agent(settings=mock_settings)

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    async def test_create_agent_invalid_reasoning_effort_raises_error(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
    ) -> None:
        """Test creating agent with invalid reasoning effort raises ValueError."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_settings.GPT5_DEFAULT_REASONING_EFFORT = "invalid"

        # Act & Assert - should raise ValueError when creating GPT5Config
        with pytest.raises(ValueError):
            await create_agent(settings=mock_settings)


class TestLoggingAndObservability:
    """Test logging and observability features."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    async def test_agent_creation_logs_configuration(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        """Test agent creation logs configuration details."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_llm_factory.return_value = mock_llm

        # Act
        with patch("backend.deep_agent.agents.deep_agent.logger") as mock_logger:
            try:
                await create_agent(settings=mock_settings)
            except NotImplementedError:
                pass  # Expected

            # Assert - verify configuration was logged
            mock_logger.info.assert_called()
            # Check that model and reasoning effort were logged
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Creating DeepAgent" in call for call in info_calls)

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_gpt5_llm")
    async def test_agent_creation_logs_llm_creation(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        """Test LLM creation is logged."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        mock_llm_factory.return_value = mock_llm

        # Act
        with patch("backend.deep_agent.agents.deep_agent.logger") as mock_logger:
            try:
                await create_agent(settings=mock_settings)
            except NotImplementedError:
                pass  # Expected

            # Assert - verify LLM creation was logged
            debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
            assert any("Created GPT-5 LLM instance" in call for call in debug_calls)


class TestSystemInstructions:
    """Test system instructions configuration."""

    @pytest.mark.asyncio
    async def test_system_instructions_include_file_tools_description(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test system instructions mention file system tools."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        # Act - inspect the function source to verify instructions
        import inspect
        source = inspect.getsource(create_agent)

        # Assert - verify instructions mention key capabilities
        assert "file system tools" in source.lower()
        assert "ls" in source
        assert "read_file" in source
        assert "write_file" in source
        assert "edit_file" in source

    @pytest.mark.asyncio
    async def test_system_instructions_mention_hitl(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test system instructions mention HITL approval."""
        # Arrange
        from backend.deep_agent.agents.deep_agent import create_agent

        import inspect
        source = inspect.getsource(create_agent)

        # Assert
        assert "hitl" in source.lower() or "approval" in source.lower()


# Integration test that will work once deepagents is installed


class TestDeepAgentsIntegration:
    """
    Integration tests for when deepagents package is installed.

    These tests will be skipped if deepagents is not available.
    """

    @pytest.mark.skipif(
        find_spec("deepagents") is None,
        reason="deepagents package not installed"
    )
    @pytest.mark.asyncio
    async def test_create_agent_with_real_deepagents(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test agent creation with real deepagents package (when installed)."""
        # This test will only run once deepagents is installed
        from backend.deep_agent.agents.deep_agent import create_agent

        # Act - this should work once deepagents is installed
        agent = await create_agent(settings=mock_settings)

        # Assert
        assert agent is not None
        assert isinstance(agent, CompiledStateGraph)
        assert hasattr(agent, "ainvoke")
