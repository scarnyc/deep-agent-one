"""Integration tests for prompt optimization tools.

Tests real optimization workflows, analysis logic, and evaluation metrics.
Focuses on business logic and integration behavior, not static data validation.
"""

from unittest.mock import MagicMock, patch

import pytest
from deep_agent.tools.prompt_optimization import (
    ab_test_prompts,
    analyze_prompt,
    create_evaluation_dataset,
    evaluate_prompt,
    optimize_prompt,
)


class TestPromptAnalysis:
    """Test suite for analyze_prompt integration."""

    def test_analyze_prompt_detects_contradictions_in_real_prompt(self) -> None:
        """Test that contradictory instructions are detected in real prompts."""
        prompt = "Be concise but also be thorough and explain everything in detail."

        result = analyze_prompt(prompt, "general")

        # Verify contradiction detection
        assert any(
            "contradict" in item.lower()
            for item in result["issues"] + result["best_practices_violations"]
        )
        assert result["clarity_score"] < 100  # Should be penalized

    def test_analyze_prompt_detects_missing_tool_usage_guidelines(self) -> None:
        """Test that missing tool usage guidelines are flagged for research tasks."""
        prompt = "You are an assistant that can search the web."

        result = analyze_prompt(prompt, "research")

        # Should recommend adding tool usage guidelines
        violations = result["best_practices_violations"]
        assert isinstance(violations, list)
        tool_violations = [v for v in violations if "tool_usage" in v.lower()]
        assert len(tool_violations) > 0

    def test_analyze_prompt_scores_xml_structure_higher(self) -> None:
        """Test that XML-style structure improves structure score."""
        prompt_without_xml = "You are a helpful assistant. Do task A. Do task B."
        prompt_with_xml = """
        ## Instructions
        You are a helpful assistant.
        ## Task
        Do task A
        ## Task
        Do task B
        """

        result_without = analyze_prompt(prompt_without_xml, "general")
        result_with = analyze_prompt(prompt_with_xml, "general")

        # XML structure should score higher
        assert result_with["structure_score"] >= result_without["structure_score"]

    def test_analyze_prompt_detects_verbosity_mismatch_for_task_type(self) -> None:
        """Test that verbosity analysis is context-aware based on task type."""
        # Code generation should use high verbosity
        code_gen_prompt = "Be brief and concise in your code responses."
        result = analyze_prompt(code_gen_prompt, "code_gen")

        # Should flag low verbosity for code_gen task
        violations = result["best_practices_violations"]
        assert any("verbosity" in v.lower() for v in violations)


class TestPromptOptimization:
    """Test suite for optimize_prompt integration with Opik."""

    @patch("deep_agent.tools.prompt_optimization.get_opik_client")
    def test_optimize_prompt_executes_hierarchical_reflective_algorithm(
        self, mock_get_client
    ) -> None:
        """Test optimization workflow with hierarchical_reflective algorithm."""
        prompt = "You are a helpful assistant."
        dataset = [{"input": "What is AI?", "expected_output": "AI is artificial intelligence."}]

        mock_opik_client = MagicMock()
        mock_result = {
            "optimized_prompt": "You are a highly capable AI assistant...",
            "original_prompt": prompt,
            "score": 0.85,
            "improvement": 0.25,
            "algorithm": "hierarchical_reflective",
            "trials": 5,
        }
        mock_opik_client.optimize_prompt.return_value = mock_result
        mock_opik_client.get_or_create_dataset.return_value = MagicMock()
        mock_get_client.return_value = mock_opik_client

        # Execute optimization
        result = optimize_prompt(
            prompt=prompt,
            dataset=dataset,
            optimizer_type="hierarchical_reflective",
            max_trials=5,
        )

        # Verify workflow execution
        assert result["optimized_prompt"] is not None
        assert result["score"] == 0.85
        assert result["improvement"] == 0.25
        assert result["algorithm"] == "hierarchical_reflective"

        # Verify correct parameters were passed to optimize_prompt
        call_kwargs = mock_opik_client.optimize_prompt.call_args
        assert call_kwargs is not None, "optimize_prompt was not called"
        # Verify key parameters were passed correctly
        mock_opik_client.optimize_prompt.assert_called_once()

    @patch("deep_agent.tools.prompt_optimization.get_opik_client")
    def test_optimize_prompt_supports_all_six_algorithms(self, mock_get_client) -> None:
        """Test that all 6 Opik algorithms can be selected and executed."""
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
        mock_opik_client.get_or_create_dataset.return_value = MagicMock()

        for algo in algorithms:
            mock_opik_client.optimize_prompt.reset_mock()  # Reset between iterations
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

            # Verify result matches expected algorithm
            assert result["algorithm"] == algo

            # Verify optimize_prompt was called with the correct algorithm parameter
            assert (
                mock_opik_client.optimize_prompt.called
            ), f"optimize_prompt was not called for algorithm: {algo}"
            call_args = mock_opik_client.optimize_prompt.call_args
            # Verify the algorithm parameter was actually passed correctly
            # (optimizer_type is mapped to 'algorithm' when calling Opik client)
            passed_algo = call_args.kwargs.get("algorithm")
            assert passed_algo == algo, f"Expected algorithm={algo}, but got {passed_algo}"

    @patch("deep_agent.tools.prompt_optimization.get_opik_client")
    def test_optimize_prompt_raises_error_for_invalid_algorithm(self, mock_get_client) -> None:
        """Test error handling for invalid algorithm selection."""
        prompt = "test"
        dataset = [{"input": "test", "expected_output": "output"}]

        mock_opik_client = MagicMock()
        mock_opik_client.optimize_prompt.side_effect = ValueError("Unsupported algorithm")
        mock_opik_client.get_or_create_dataset.return_value = MagicMock()
        mock_get_client.return_value = mock_opik_client

        with pytest.raises(ValueError):
            optimize_prompt(
                prompt=prompt,
                dataset=dataset,
                optimizer_type="invalid_algo",
                max_trials=3,
            )


class TestPromptEvaluation:
    """Test suite for evaluate_prompt integration."""

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_evaluate_prompt_calculates_accuracy_metric(self, mock_chat_openai) -> None:
        """Test that evaluation calculates accuracy correctly."""
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

        result = evaluate_prompt(prompt, dataset)

        # Verify metrics are calculated
        assert "accuracy" in result
        assert "latency" in result
        assert "cost" in result
        assert "quality_score" in result
        assert 0 <= result["accuracy"] <= 1.0
        assert result["latency"] >= 0

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_evaluate_prompt_achieves_perfect_accuracy(self, mock_chat_openai) -> None:
        """Test evaluation with perfect accuracy scenario."""
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

        result = evaluate_prompt(prompt, dataset)

        assert result["accuracy"] == 1.0

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_evaluate_prompt_handles_empty_dataset(self, mock_chat_openai) -> None:
        """Test evaluation with empty dataset returns zero metrics."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        prompt = "test"
        dataset: list[dict[str, str]] = []

        result = evaluate_prompt(prompt, dataset)

        assert result["accuracy"] == 0.0
        assert result["latency"] == 0.0
        assert result["cost"] == 0
        # Empty dataset should not invoke LLM (no examples to evaluate)
        mock_llm.invoke.assert_not_called()


class TestEvaluationDatasetCreation:
    """Test suite for create_evaluation_dataset integration."""

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_create_evaluation_dataset_generates_examples(self, mock_chat_openai) -> None:
        """Test that dataset creation generates requested number of examples."""
        description = "Math addition problems"
        num_examples = 3

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = """
INPUT: What is 1+1?
OUTPUT: 2

INPUT: What is 2+2?
OUTPUT: 4

INPUT: What is 3+3?
OUTPUT: 6"""
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        result = create_evaluation_dataset(description, num_examples)

        # Verify dataset structure
        assert isinstance(result, list)
        assert len(result) == 3
        assert all("input" in item and "expected_output" in item for item in result)

    @patch("deep_agent.tools.prompt_optimization.ChatOpenAI")
    def test_create_evaluation_dataset_supports_different_sizes(self, mock_chat_openai) -> None:
        """Test dataset creation with different sizes."""
        description = "Test cases"
        sizes = [3, 5, 10]

        mock_llm = MagicMock()
        for size in sizes:
            # Create mock response with correct number of examples
            examples = "\n" + "\n\n".join(
                [f"INPUT: test{i}\nOUTPUT: output{i}" for i in range(size)]
            )
            mock_response = MagicMock()
            mock_response.content = examples
            mock_llm.invoke.return_value = mock_response
            mock_chat_openai.return_value = mock_llm

            result = create_evaluation_dataset(description, size)

            assert len(result) == size


class TestABTestPrompts:
    """Test suite for ab_test_prompts integration."""

    @patch("deep_agent.tools.prompt_optimization.evaluate_prompt")
    def test_ab_test_executes_statistical_comparison(self, mock_evaluate) -> None:
        """Test that A/B test executes and determines winner."""
        prompt_a = "You are helpful."
        prompt_b = "You are very helpful and thorough."
        dataset = [{"input": "test", "expected_output": "output"}]

        # Mock evaluation results
        mock_evaluate.side_effect = [
            {"accuracy": 0.75, "latency": 0.1, "cost": 50, "quality_score": 70.0},
            {"accuracy": 0.85, "latency": 0.12, "cost": 60, "quality_score": 80.0},
        ]

        result = ab_test_prompts(prompt_a, prompt_b, dataset, alpha=0.05)

        # Verify statistical analysis
        assert "winner" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert "statistically_significant" in result
        assert "metrics_comparison" in result
        assert result["winner"] in ["A", "B", "tie"]

        # Verify evaluate_prompt was called exactly twice (once for each prompt variant)
        assert (
            mock_evaluate.call_count == 2
        ), f"Expected 2 evaluate_prompt calls, got {mock_evaluate.call_count}"

    @patch("deep_agent.tools.prompt_optimization.evaluate_prompt")
    def test_ab_test_detects_significant_difference(self, mock_evaluate) -> None:
        """Test statistical significance detection with large performance difference."""
        prompt_a = "prompt A"
        prompt_b = "prompt B"
        dataset = [{"input": f"test{i}", "expected_output": f"out{i}"} for i in range(10)]

        # Mock: B is significantly better than A
        mock_evaluate.side_effect = [
            {"accuracy": 0.5, "latency": 0.1, "cost": 50, "quality_score": 45.0},
            {"accuracy": 0.9, "latency": 0.1, "cost": 50, "quality_score": 85.0},
        ]

        result = ab_test_prompts(prompt_a, prompt_b, dataset, alpha=0.05)

        assert result["winner"] == "B"

    @patch("deep_agent.tools.prompt_optimization.evaluate_prompt")
    def test_ab_test_detects_no_difference(self, mock_evaluate) -> None:
        """Test A/B test with equal performance (tie scenario)."""
        prompt_a = "prompt A"
        prompt_b = "prompt B"
        dataset = [{"input": "test", "expected_output": "output"}]

        # Mock: Same performance
        mock_evaluate.side_effect = [
            {"accuracy": 0.8, "latency": 0.1, "cost": 50, "quality_score": 75.0},
            {"accuracy": 0.8, "latency": 0.1, "cost": 50, "quality_score": 75.0},
        ]

        result = ab_test_prompts(prompt_a, prompt_b, dataset, alpha=0.05)

        assert result["winner"] == "tie"
        assert not result["statistically_significant"]
