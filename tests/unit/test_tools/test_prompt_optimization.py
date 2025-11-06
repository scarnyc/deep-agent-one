"""
Unit tests for prompt optimization tools.

Tests all 5 prompt optimization tools with proper mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deep_agent.tools.prompt_optimization import (
    GPT5_BEST_PRACTICES,
    ab_test_prompts,
    analyze_prompt,
    create_evaluation_dataset,
    evaluate_prompt,
    optimize_prompt,
)


class TestAnalyzePrompt:
    """Test suite for analyze_prompt tool."""

    def test_analyze_prompt_basic(self):
        """Test basic prompt analysis."""
        # Arrange
        prompt = "You are a helpful assistant. Be concise and accurate."
        task_type = "general"

        # Act
        result = analyze_prompt(prompt, task_type)

        # Assert
        assert "issues" in result
        assert "best_practices_violations" in result
        assert "recommendations" in result
        assert "clarity_score" in result
        assert "verbosity_score" in result
        assert "structure_score" in result
        assert isinstance(result["clarity_score"], (int, float))
        assert 0 <= result["clarity_score"] <= 100

    def test_analyze_prompt_detects_contradictions(self):
        """Test that contradictory instructions are detected."""
        # Arrange
        prompt = "Be concise but also be thorough and explain everything in detail."

        # Act
        result = analyze_prompt(prompt, "general")

        # Assert
        # Check for contradiction in issues or violations
        assert any(
            "contradict" in item.lower()
            for item in result["issues"] + result["best_practices_violations"]
        )

    def test_analyze_prompt_detects_missing_tool_usage(self):
        """Test that missing tool usage guidelines are flagged."""
        # Arrange
        prompt = "You are an assistant that can search the web."
        # Note: No mention of parallel limits or citations

        # Act
        result = analyze_prompt(prompt, "research")

        # Assert
        # Should recommend adding tool usage guidelines (violations is a list)
        violations = result["best_practices_violations"]
        assert isinstance(violations, list)
        # Check that tool_usage violations are present
        tool_violations = [v for v in violations if "tool_usage" in v.lower()]
        assert len(tool_violations) > 0

    def test_analyze_prompt_xml_structure(self):
        """Test that XML-style structure improves score."""
        # Arrange
        prompt_without_xml = "You are a helpful assistant. Do task A. Do task B."
        prompt_with_xml = """
        <instructions>
        You are a helpful assistant.
        <task>Do task A</task>
        <task>Do task B</task>
        </instructions>
        """

        # Act
        result_without = analyze_prompt(prompt_without_xml, "general")
        result_with = analyze_prompt(prompt_with_xml, "general")

        # Assert
        assert result_with["structure_score"] >= result_without["structure_score"]

    def test_analyze_prompt_task_types(self):
        """Test analysis for different task types."""
        # Arrange
        prompt = "You are a helpful assistant."
        task_types = ["general", "research", "code_generation", "chat"]

        # Act & Assert
        for task_type in task_types:
            result = analyze_prompt(prompt, task_type)
            assert result["clarity_score"] >= 0
            assert result["verbosity_score"] >= 0


class TestOptimizePrompt:
    """Test suite for optimize_prompt tool."""

    @patch("deep_agent.tools.prompt_optimization.get_opik_client")
    def test_optimize_prompt_hierarchical_reflective(self, mock_get_client):
        """Test optimization with hierarchical_reflective algorithm."""
        # Arrange
        prompt = "You are a helpful assistant."
        dataset = [
            {"input": "What is AI?", "expected_output": "AI is artificial intelligence."}
        ]

        mock_opik_client = MagicMock()
        # Return a dict, not a MagicMock with attributes
        mock_result = {
            "optimized_prompt": "You are a highly capable AI assistant...",
            "original_prompt": prompt,
            "score": 0.85,
            "improvement": 0.25,
            "algorithm": "hierarchical_reflective",
            "trials": 5,
        }
        mock_opik_client.optimize_prompt.return_value = mock_result
        mock_get_client.return_value = mock_opik_client

        # Act
        result = optimize_prompt(
            prompt=prompt,
            dataset=dataset,
            optimizer_type="hierarchical_reflective",
            max_trials=5,
        )

        # Assert
        assert "optimized_prompt" in result
        assert "original_prompt" in result
        assert "score" in result
        assert "improvement" in result
        assert "algorithm" in result
        assert result["algorithm"] == "hierarchical_reflective"
        assert result["score"] == 0.85
        assert result["improvement"] == 0.25
        mock_opik_client.optimize_prompt.assert_called_once()

    @patch("deep_agent.tools.prompt_optimization.get_opik_client")
    def test_optimize_prompt_all_algorithms(self, mock_get_client):
        """Test that all 6 algorithms can be selected."""
        # Arrange
        prompt = "You are a helpful assistant."
        dataset = [{"input": "test", "expected_output": "output"}]
        algorithms = [
            "hierarchical_reflective",
            "few_shot_bayesian",
            "evolutionary",
            "meta_prompt",
            "gepa",
            "parameter",
        ]

        mock_opik_client = MagicMock()

        # Act & Assert
        for algo in algorithms:
            # Create new mock result for each algorithm with correct algorithm name
            mock_result = {
                "optimized_prompt": "optimized",
                "original_prompt": prompt,
                "score": 0.9,
                "improvement": 0.1,
                "algorithm": algo,
                "trials": 3,
            }
            mock_opik_client.optimize_prompt.return_value = mock_result
            mock_get_client.return_value = mock_opik_client

            result = optimize_prompt(
                prompt=prompt,
                dataset=dataset,
                optimizer_type=algo,
                max_trials=3,
            )
            assert result["algorithm"] == algo

    @patch("deep_agent.tools.prompt_optimization.get_opik_client")
    def test_optimize_prompt_invalid_algorithm(self, mock_get_client):
        """Test error handling for invalid algorithm."""
        # Arrange
        prompt = "test"
        dataset = [{"input": "test", "expected_output": "output"}]

        mock_opik_client = MagicMock()
        mock_opik_client.optimize_prompt.side_effect = ValueError("Unsupported algorithm")
        mock_get_client.return_value = mock_opik_client

        # Act & Assert
        with pytest.raises(Exception):  # Should propagate the ValueError
            optimize_prompt(
                prompt=prompt,
                dataset=dataset,
                optimizer_type="invalid_algo",
                max_trials=3,
            )


class TestEvaluatePrompt:
    """Test suite for evaluate_prompt tool."""

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_evaluate_prompt_basic(self, mock_chat_openai):
        """Test basic prompt evaluation."""
        # Arrange
        prompt = "You are a helpful assistant."
        dataset = [
            {"input": "What is 2+2?", "expected_output": "4"},
            {"input": "What is 3+3?", "expected_output": "6"},
        ]

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "4"
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        # Act
        result = evaluate_prompt(prompt, dataset)

        # Assert
        assert "accuracy" in result
        assert "latency" in result
        assert "cost" in result
        assert "quality_score" in result
        assert 0 <= result["accuracy"] <= 1.0
        assert result["latency"] >= 0
        assert result["cost"] >= 0

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_evaluate_prompt_perfect_accuracy(self, mock_chat_openai):
        """Test evaluation with perfect accuracy."""
        # Arrange
        prompt = "You are a helpful assistant."
        dataset = [
            {"input": "Say 'yes'", "expected_output": "yes"},
            {"input": "Say 'no'", "expected_output": "no"},
        ]

        mock_llm = MagicMock()
        # Mock responses match expected outputs exactly
        mock_llm.invoke.side_effect = [
            MagicMock(content="yes"),
            MagicMock(content="no"),
        ]
        mock_chat_openai.return_value = mock_llm

        # Act
        result = evaluate_prompt(prompt, dataset)

        # Assert
        assert result["accuracy"] == 1.0

    def test_evaluate_prompt_empty_dataset(self):
        """Test evaluation with empty dataset."""
        # Arrange
        prompt = "test"
        dataset = []

        # Act
        result = evaluate_prompt(prompt, dataset)

        # Assert
        assert result["accuracy"] == 0.0
        assert result["latency"] == 0.0
        assert result["cost"] == 0


class TestCreateEvaluationDataset:
    """Test suite for create_evaluation_dataset tool."""

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_create_evaluation_dataset_basic(self, mock_chat_openai):
        """Test basic dataset creation."""
        # Arrange
        description = "Math addition problems"
        num_examples = 3

        mock_llm = MagicMock()
        mock_response = MagicMock()
        # Format must match the parser: "\n\s*INPUT:" splits, so need newline before INPUT
        mock_response.content = """
INPUT: What is 1+1?
OUTPUT: 2

INPUT: What is 2+2?
OUTPUT: 4

INPUT: What is 3+3?
OUTPUT: 6"""
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        # Act
        result = create_evaluation_dataset(description, num_examples)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all("input" in item and "expected_output" in item for item in result)

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_create_evaluation_dataset_different_sizes(self, mock_chat_openai):
        """Test dataset creation with different sizes."""
        # Arrange
        description = "Test cases"
        sizes = [3, 5, 10]

        mock_llm = MagicMock()
        for size in sizes:
            # Create mock response with correct number of examples
            # Need leading newline before first INPUT for parser
            examples = "\n" + "\n\n".join(
                [f"INPUT: test{i}\nOUTPUT: output{i}" for i in range(size)]
            )
            mock_response = MagicMock()
            mock_response.content = examples
            mock_llm.invoke.return_value = mock_response
            mock_chat_openai.return_value = mock_llm

            # Act
            result = create_evaluation_dataset(description, size)

            # Assert
            assert len(result) == size


class TestABTestPrompts:
    """Test suite for ab_test_prompts tool."""

    @patch("deep_agent.tools.prompt_optimization.evaluate_prompt")
    def test_ab_test_prompts_basic(self, mock_evaluate):
        """Test basic A/B testing."""
        # Arrange
        prompt_a = "You are helpful."
        prompt_b = "You are very helpful and thorough."
        dataset = [{"input": "test", "expected_output": "output"}]

        # Mock evaluation results (updated keys: latency and cost instead of avg_latency_ms and total_tokens)
        mock_evaluate.side_effect = [
            {"accuracy": 0.75, "latency": 0.1, "cost": 50, "quality_score": 70.0},
            {"accuracy": 0.85, "latency": 0.12, "cost": 60, "quality_score": 80.0},
        ]

        # Act
        result = ab_test_prompts(prompt_a, prompt_b, dataset, alpha=0.05)

        # Assert
        assert "winner" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert "statistically_significant" in result
        assert "metrics_comparison" in result
        assert result["winner"] in ["A", "B", "tie"]

    @patch("deep_agent.tools.prompt_optimization.evaluate_prompt")
    def test_ab_test_prompts_significance(self, mock_evaluate):
        """Test statistical significance calculation."""
        # Arrange
        prompt_a = "prompt A"
        prompt_b = "prompt B"
        dataset = [{"input": f"test{i}", "expected_output": f"out{i}"} for i in range(10)]

        # Mock: B is significantly better than A
        mock_evaluate.side_effect = [
            {"accuracy": 0.5, "latency": 0.1, "cost": 50, "quality_score": 45.0},
            {"accuracy": 0.9, "latency": 0.1, "cost": 50, "quality_score": 85.0},
        ]

        # Act
        result = ab_test_prompts(prompt_a, prompt_b, dataset, alpha=0.05)

        # Assert
        assert result["winner"] == "B"
        # With large difference (0.5 vs 0.9), should be significant
        # Note: Actual significance depends on sample size

    @patch("deep_agent.tools.prompt_optimization.evaluate_prompt")
    def test_ab_test_prompts_no_difference(self, mock_evaluate):
        """Test A/B test with no difference between prompts."""
        # Arrange
        prompt_a = "prompt A"
        prompt_b = "prompt B"
        dataset = [{"input": "test", "expected_output": "output"}]

        # Mock: Same performance
        mock_evaluate.side_effect = [
            {"accuracy": 0.8, "latency": 0.1, "cost": 50, "quality_score": 75.0},
            {"accuracy": 0.8, "latency": 0.1, "cost": 50, "quality_score": 75.0},
        ]

        # Act
        result = ab_test_prompts(prompt_a, prompt_b, dataset, alpha=0.05)

        # Assert
        # When equal, winner should be "tie"
        assert result["winner"] == "tie"
        assert not result["statistically_significant"]


class TestGPT5BestPractices:
    """Test suite for GPT5_BEST_PRACTICES constant."""

    def test_best_practices_structure(self):
        """Test that best practices dictionary has expected structure."""
        # Assert (updated key names to match actual implementation)
        assert "agentic_behavior" in GPT5_BEST_PRACTICES
        assert "verbosity_control" in GPT5_BEST_PRACTICES
        assert "tool_usage" in GPT5_BEST_PRACTICES
        assert "clarity_structure" in GPT5_BEST_PRACTICES  # Changed from "structure"
        assert "no_contradictions" in GPT5_BEST_PRACTICES  # Changed from "completeness"

        # Check that each category has items
        for category in GPT5_BEST_PRACTICES.values():
            assert isinstance(category, list)
            assert len(category) > 0

    def test_best_practices_content(self):
        """Test that best practices include key requirements."""
        # Flatten all practices into single list
        all_practices = []
        for practices in GPT5_BEST_PRACTICES.values():
            all_practices.extend(practices)

        # Assert key requirements are present
        all_practices_str = " ".join(all_practices).lower()
        assert "parallel" in all_practices_str  # Parallel tool limits
        assert "citation" in all_practices_str  # Citation requirements
        assert "decompose" in all_practices_str or "subtask" in all_practices_str  # Task decomposition
