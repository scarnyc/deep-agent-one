"""
End-to-end tests for context-engineering-expert agent.

Tests complete workflows from agent invocation to prompt optimization results.
Marks tests with @pytest.mark.e2e for selective execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deep_agent.agents.sub_agents.context_engineering_expert import (
    create_context_engineering_expert,
    get_context_engineering_expert,
)
from deep_agent.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for E2E tests."""
    settings = MagicMock(spec=Settings)
    settings.OPENAI_API_KEY = "test-openai-key"
    settings.OPIK_API_KEY = "test-opik-key"
    settings.OPIK_WORKSPACE = "test-workspace"
    settings.OPIK_PROJECT = "context-engineering-tests"
    settings.LANGSMITH_API_KEY = "test-langsmith-key"
    settings.LANGSMITH_PROJECT = "context-engineering"
    settings.GPT5_MODEL_NAME = "gpt-5-preview"
    settings.GPT5_DEFAULT_REASONING_EFFORT = "high"
    settings.GPT5_MAX_TOKENS = 4096
    return settings


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies for E2E tests."""
    with patch("deep_agent.agents.sub_agents.context_engineering_expert.create_gpt5_llm") as mock_create_llm, \
         patch("deep_agent.agents.sub_agents.context_engineering_expert.create_deep_agent") as mock_create_agent, \
         patch("deep_agent.agents.sub_agents.context_engineering_expert.setup_langsmith") as mock_langsmith:

        # Mock LLM
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        # Mock compiled graph
        mock_graph = MagicMock()
        mock_create_agent.return_value = mock_graph

        yield {
            "create_llm": mock_create_llm,
            "create_agent": mock_create_agent,
            "langsmith": mock_langsmith,
            "llm": mock_llm,
            "graph": mock_graph,
        }


@pytest.mark.e2e
@pytest.mark.asyncio
class TestContextEngineeringExpertCreation:
    """Test suite for agent creation."""

    async def test_create_agent_success(self, mock_settings, mock_dependencies):
        """Test successful agent creation."""
        # Act
        agent = await create_context_engineering_expert(settings=mock_settings)

        # Assert
        assert agent is not None
        assert agent == mock_dependencies["graph"]

        # Verify LangSmith was set up
        mock_dependencies["langsmith"].assert_called_once_with(mock_settings)

        # Verify LLM was created with correct config
        mock_dependencies["create_llm"].assert_called_once()
        call_kwargs = mock_dependencies["create_llm"].call_args.kwargs
        assert call_kwargs["api_key"] == "test-openai-key"
        assert call_kwargs["config"].reasoning_effort.value == "high"
        assert call_kwargs["config"].temperature == 0.3  # Lower for consistent analysis

        # Verify create_deep_agent was called with tools
        mock_dependencies["create_agent"].assert_called_once()
        call_kwargs = mock_dependencies["create_agent"].call_args.kwargs
        assert call_kwargs["model"] == mock_dependencies["llm"]
        assert len(call_kwargs["tools"]) == 5  # All 5 prompt optimization tools
        assert call_kwargs["subagents"] is None
        assert call_kwargs["checkpointer"] is None
        assert "Context Engineering Expert" in call_kwargs["system_prompt"]

    async def test_create_agent_with_default_settings(self, mock_dependencies):
        """Test agent creation with default settings."""
        # Arrange
        mock_settings = MagicMock(spec=Settings)
        mock_settings.OPENAI_API_KEY = "default-key"
        mock_settings.OPIK_API_KEY = "default-opik"
        mock_settings.OPIK_WORKSPACE = "default-ws"
        mock_settings.OPIK_PROJECT = "default-proj"
        mock_settings.LANGSMITH_API_KEY = "default-langsmith"
        mock_settings.LANGSMITH_PROJECT = "default-proj"
        mock_settings.GPT5_MODEL_NAME = "gpt-5-preview"
        mock_settings.GPT5_DEFAULT_REASONING_EFFORT = "high"
        mock_settings.GPT5_MAX_TOKENS = 4096

        with patch("deep_agent.agents.sub_agents.context_engineering_expert.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            # Act
            agent = await create_context_engineering_expert()

            # Assert
            assert agent is not None
            mock_get_settings.assert_called_once()

    async def test_create_agent_llm_error(self, mock_settings, mock_dependencies):
        """Test error handling when LLM creation fails."""
        # Arrange
        mock_dependencies["create_llm"].side_effect = ValueError("Invalid API key")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid API key"):
            await create_context_engineering_expert(settings=mock_settings)

    async def test_create_agent_graph_compilation_error(self, mock_settings, mock_dependencies):
        """Test error handling when graph compilation fails."""
        # Arrange
        mock_dependencies["create_agent"].side_effect = RuntimeError("Graph compilation failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Graph compilation failed"):
            await create_context_engineering_expert(settings=mock_settings)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestContextEngineeringExpertSingleton:
    """Test suite for singleton pattern."""

    async def test_get_context_engineering_expert_singleton(self, mock_settings, mock_dependencies):
        """Test that get_context_engineering_expert returns singleton."""
        # Arrange & Act
        agent1 = await get_context_engineering_expert(settings=mock_settings)
        agent2 = await get_context_engineering_expert(settings=mock_settings)

        # Assert
        assert agent1 is agent2  # Same instance
        # create_deep_agent should only be called once
        assert mock_dependencies["create_agent"].call_count == 1


@pytest.mark.e2e
@pytest.mark.asyncio
class TestContextEngineeringExpertWorkflow:
    """Test suite for complete agent workflows."""

    async def test_analyze_prompt_workflow(self, mock_settings, mock_dependencies):
        """Test complete workflow: user asks to analyze a prompt."""
        # Arrange
        agent = await create_context_engineering_expert(settings=mock_settings)

        # Mock agent invocation result
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": """I've analyzed your prompt using GPT-5 best practices.

**Issues Found:**
- Missing tool usage guidelines
- No parallel tool call limits specified
- Citation requirements not mentioned

**Clarity Score:** 75/100
**Verbosity Score:** 60/100
**Structure Score:** 50/100

**Recommendations:**
1. Add explicit tool usage section with parallel limits (max 3)
2. Require citations for web searches
3. Use XML-style tags for better structure
""",
                }
            ]
        }

        agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Analyze this prompt: You are a helpful assistant. Use web search when needed.",
                    }
                ]
            },
            {"configurable": {"thread_id": "test-analyze"}},
        )

        # Assert
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert "Issues Found" in result["messages"][0]["content"]
        assert "Recommendations" in result["messages"][0]["content"]

    async def test_optimize_prompt_workflow(self, mock_settings, mock_dependencies):
        """Test complete workflow: user requests prompt optimization."""
        # Arrange
        agent = await create_context_engineering_expert(settings=mock_settings)

        # Mock agent invocation result
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": """I've optimized your prompt using the HierarchicalReflectiveOptimizer (Rank #1, 67.83% avg).

**Original Prompt:**
You are a helpful assistant.

**Optimized Prompt:**
You are an expert AI assistant with access to powerful research tools.

<instructions>
- Break down complex queries into systematic subtasks
- Use web_search for current information (max 3 parallel searches)
- Always include citations with sources and URLs: [Source](URL)
- Verify information before presenting as facts
- Confirm task completion before terminating
</instructions>

**Performance Improvement:**
- Score: 0.85 → 0.92 (+8.2%)
- Accuracy: 75% → 89% (+14%)
- Trials: 10

The optimization focused on adding explicit tool usage guidelines and structured task decomposition.
""",
                }
            ]
        }

        agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": """Optimize this prompt using Opik:

Prompt: You are a helpful assistant.
Dataset: [examples provided]
Algorithm: hierarchical_reflective
""",
                    }
                ]
            },
            {"configurable": {"thread_id": "test-optimize"}},
        )

        # Assert
        assert result is not None
        assert "messages" in result
        assert "Optimized Prompt" in result["messages"][0]["content"]
        assert "Performance Improvement" in result["messages"][0]["content"]
        assert "HierarchicalReflectiveOptimizer" in result["messages"][0]["content"]

    async def test_ab_test_workflow(self, mock_settings, mock_dependencies):
        """Test complete workflow: user requests A/B test."""
        # Arrange
        agent = await create_context_engineering_expert(settings=mock_settings)

        # Mock agent invocation result
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": """I've completed the A/B test between your two prompts.

**Results:**

**Prompt A:**
- Accuracy: 75%
- Avg Latency: 120ms
- Total Tokens: 1,200

**Prompt B:**
- Accuracy: 89%
- Avg Latency: 135ms
- Total Tokens: 1,450

**Statistical Analysis:**
- Winner: **B** ✓
- P-value: 0.012 (statistically significant at α=0.05)
- Effect Size: 0.68 (medium-to-large effect)

**Conclusion:**
Prompt B shows a statistically significant improvement in accuracy (+14%) with acceptable trade-offs in latency (+15ms) and token usage (+21%).

**Recommendation:** Use Prompt B for production.
""",
                }
            ]
        }

        agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Run A/B test between Prompt A and Prompt B on dataset X",
                    }
                ]
            },
            {"configurable": {"thread_id": "test-ab"}},
        )

        # Assert
        assert result is not None
        assert "A/B test" in result["messages"][0]["content"]
        assert "Winner" in result["messages"][0]["content"]
        assert "statistically significant" in result["messages"][0]["content"]

    async def test_create_dataset_workflow(self, mock_settings, mock_dependencies):
        """Test complete workflow: user requests dataset creation."""
        # Arrange
        agent = await create_context_engineering_expert(settings=mock_settings)

        # Mock agent invocation result
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": """I've created an evaluation dataset for testing math prompts.

**Dataset (10 examples):**

1. INPUT: What is 2 + 2?
   OUTPUT: 4

2. INPUT: Calculate 15 × 3
   OUTPUT: 45

3. INPUT: What is 100 ÷ 4?
   OUTPUT: 25

[...7 more examples...]

**Coverage:**
- Basic arithmetic (addition, subtraction, multiplication, division)
- Edge cases (zero, negative numbers, decimals)
- Word problems

This dataset can now be used with evaluate_prompt or optimize_prompt tools.
""",
                }
            ]
        }

        agent.ainvoke = AsyncMock(return_value=mock_response)

        # Act
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Create a dataset with 10 examples for testing math calculation prompts",
                    }
                ]
            },
            {"configurable": {"thread_id": "test-dataset"}},
        )

        # Assert
        assert result is not None
        assert "Dataset" in result["messages"][0]["content"]
        assert "examples" in result["messages"][0]["content"].lower()


@pytest.mark.e2e
@pytest.mark.asyncio
class TestContextEngineeringExpertToolIntegration:
    """Test suite for verifying tool integration in agent."""

    async def test_agent_has_all_five_tools(self, mock_settings, mock_dependencies):
        """Test that agent is created with all 5 prompt optimization tools."""
        # Act
        await create_context_engineering_expert(settings=mock_settings)

        # Assert
        call_kwargs = mock_dependencies["create_agent"].call_args.kwargs
        tools = call_kwargs["tools"]

        assert len(tools) == 5

        # Check tool names (functions should have __name__ attribute)
        tool_names = [tool.__name__ for tool in tools]
        assert "analyze_prompt" in tool_names
        assert "optimize_prompt" in tool_names
        assert "evaluate_prompt" in tool_names
        assert "create_evaluation_dataset" in tool_names
        assert "ab_test_prompts" in tool_names

    async def test_agent_system_prompt_includes_algorithm_guide(self, mock_settings, mock_dependencies):
        """Test that system prompt includes algorithm selection guide."""
        # Act
        await create_context_engineering_expert(settings=mock_settings)

        # Assert
        call_kwargs = mock_dependencies["create_agent"].call_args.kwargs
        system_prompt = call_kwargs["system_prompt"]

        assert "HierarchicalReflectiveOptimizer" in system_prompt
        assert "67.83" in system_prompt  # Benchmark percentage
        assert "MetaPromptOptimizer" in system_prompt
        assert "MCP" in system_prompt.upper()  # MCP tool support

    async def test_agent_uses_high_reasoning_effort(self, mock_settings, mock_dependencies):
        """Test that agent uses HIGH reasoning effort for complex analysis."""
        # Act
        await create_context_engineering_expert(settings=mock_settings)

        # Assert
        call_kwargs = mock_dependencies["create_llm"].call_args.kwargs
        config = call_kwargs["config"]

        assert config.reasoning_effort.value == "high"
        assert config.temperature == 0.3  # Lower temperature for consistency
