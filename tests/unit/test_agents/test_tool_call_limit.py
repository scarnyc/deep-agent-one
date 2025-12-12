"""
Unit tests for recursion_limit configuration in create_agent().

Tests that agents are created with correct recursion_limit based on
MAX_TOOL_CALLS_PER_INVOCATION setting.
"""

from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from backend.deep_agent.agents.deep_agent import create_agent
from backend.deep_agent.config.settings import Settings


class TestRecursionLimitConfiguration:
    """Test recursion_limit is calculated and applied correctly."""

    @pytest.mark.asyncio
    async def test_create_agent_applies_recursion_limit(self):
        """Test that create_agent() applies recursion_limit via with_config()."""
        # Arrange
        test_settings = Settings(
            ENV="test",
            OPENAI_API_KEY="test-key",
            MAX_TOOL_CALLS_PER_INVOCATION=12,
        )

        # Mock create_deep_agent to return a mock graph
        mock_graph = MagicMock(spec=CompiledStateGraph)
        mock_graph_with_config = MagicMock(spec=CompiledStateGraph)
        mock_graph.with_config = MagicMock(return_value=mock_graph_with_config)

        with patch(
            "backend.deep_agent.agents.deep_agent.create_deep_agent", return_value=mock_graph
        ):
            with patch("backend.deep_agent.agents.deep_agent.create_llm"):
                with patch("backend.deep_agent.agents.deep_agent.setup_langsmith"):
                    # Act
                    agent = await create_agent(settings=test_settings)

                    # Assert
                    # Recursion limit should be (12 * 2) + 1 = 25
                    mock_graph.with_config.assert_called_once_with({"recursion_limit": 25})
                    assert agent == mock_graph_with_config

    @pytest.mark.asyncio
    async def test_recursion_limit_calculation_formula(self):
        """Test that recursion_limit is calculated as (max_tool_calls * 2) + 1."""
        # Test with different MAX_TOOL_CALLS_PER_INVOCATION values
        test_cases = [
            (8, 17),  # (8 * 2) + 1 = 17
            (10, 21),  # (10 * 2) + 1 = 21
            (12, 25),  # (12 * 2) + 1 = 25
            (20, 41),  # (20 * 2) + 1 = 41
        ]

        for max_calls, expected_limit in test_cases:
            # Arrange
            test_settings = Settings(
                ENV="test",
                OPENAI_API_KEY="test-key",
                MAX_TOOL_CALLS_PER_INVOCATION=max_calls,
            )

            mock_graph = MagicMock(spec=CompiledStateGraph)
            mock_graph_with_config = MagicMock(spec=CompiledStateGraph)
            mock_graph.with_config = MagicMock(return_value=mock_graph_with_config)

            with patch(
                "backend.deep_agent.agents.deep_agent.create_deep_agent", return_value=mock_graph
            ):
                with patch("backend.deep_agent.agents.deep_agent.create_llm"):
                    with patch("backend.deep_agent.agents.deep_agent.setup_langsmith"):
                        # Act
                        await create_agent(settings=test_settings)

                        # Assert
                        mock_graph.with_config.assert_called_with(
                            {"recursion_limit": expected_limit}
                        )

    @pytest.mark.asyncio
    async def test_returns_compiled_state_graph(self):
        """Test that create_agent() returns CompiledStateGraph, not wrapper."""
        # Arrange
        test_settings = Settings(
            ENV="test",
            OPENAI_API_KEY="test-key",
        )

        mock_graph = MagicMock(spec=CompiledStateGraph)
        mock_graph_with_config = MagicMock(spec=CompiledStateGraph)
        mock_graph.with_config = MagicMock(return_value=mock_graph_with_config)

        with patch(
            "backend.deep_agent.agents.deep_agent.create_deep_agent", return_value=mock_graph
        ):
            with patch("backend.deep_agent.agents.deep_agent.create_llm"):
                with patch("backend.deep_agent.agents.deep_agent.setup_langsmith"):
                    # Act
                    agent = await create_agent(settings=test_settings)

                    # Assert
                    assert isinstance(agent, MagicMock)  # Would be CompiledStateGraph in real usage
                    assert agent == mock_graph_with_config
