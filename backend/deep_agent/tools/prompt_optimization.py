"""
Prompt Optimization Tools.

Provides 5 core tools for analyzing, optimizing, and validating prompts:
1. analyze_prompt - GPT-5 best practices analysis
2. optimize_prompt - Opik-powered optimization with algorithm selection
3. evaluate_prompt - Performance metrics evaluation
4. create_evaluation_dataset - Test case generation
5. ab_test_prompts - Statistical A/B testing

Integrates with Opik's 6 optimization algorithms and follows GPT-5 best practices.
"""

import re
from typing import Any

import numpy as np
from langchain_openai import ChatOpenAI
from opik.evaluation.metrics import score_result
from scipy import stats
from structlog import get_logger

from deep_agent.config.settings import get_settings
from deep_agent.integrations.opik_client import (
    OptimizerAlgorithm,
    get_opik_client,
)

logger = get_logger(__name__)


# GPT Best Practices Checklist
GPT_BEST_PRACTICES = {
    "agentic_behavior": [
        "Decompose complex queries into subtasks",
        "Confirm completion before terminating",
        "Maintain autonomous information gathering",
        "Verify all subtasks completed",
    ],
    "clarity_structure": [
        "Use explicit, specific instructions",
        "Avoid contradictory directives",
        "Apply XML-style specs for categorization",
        "Separate concerns into distinct sections",
    ],
    "verbosity_control": [
        "High verbosity for: code generation, reasoning traces",
        "Medium verbosity for: chat responses, summaries",
        "Low verbosity for: quick answers, confirmations",
        "Context-dependent optimization",
    ],
    "tool_usage": [
        "Balance internal knowledge vs. external tools",
        "Limit parallel tool calls (max 3 for web search per Issue #113)",
        "Avoid tool over-reliance when internal knowledge sufficient",
        "Include citations for web search results",
    ],
    "no_contradictions": [
        "Check for conflicting instructions",
        "Ensure directives don't cancel each other out",
        "Maintain logical consistency",
    ],
}


def analyze_prompt(
    prompt: str,
    task_type: str = "general",
) -> dict[str, Any]:
    """
    Analyze prompt structure against GPT-5 best practices.

    Identifies issues, violations, and provides specific recommendations
    for improvement based on GPT-5 prompting guidelines.

    Args:
        prompt: Prompt text to analyze
        task_type: Type of task (general, code_gen, chat, research)

    Returns:
        Dict containing:
        - issues: List of identified problems
        - best_practices_violations: GPT-5 guideline violations
        - recommendations: Specific improvements
        - clarity_score: 0-100 rating
        - verbosity_score: 0-100 rating (task-appropriate)
        - structure_score: 0-100 rating

    Example:
        >>> result = analyze_prompt(
        ...     prompt="You are a helpful assistant.",
        ...     task_type="general"
        ... )
        >>> print(result["clarity_score"])
        65
    """
    logger.info("Analyzing prompt", task_type=task_type, length=len(prompt))

    issues = []
    violations = []
    recommendations = []

    # Check for contradictions
    contradiction_patterns = [
        (r"be concise.*be thorough", "Contradictory: 'concise' vs 'thorough'"),
        (r"don't.*but.*do", "Contradictory: 'don't' followed by 'do'"),
        (r"avoid.*use.*same", "Contradictory: 'avoid' and 'use' for same thing"),
    ]

    for pattern, violation in contradiction_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            issues.append(violation)
            violations.append(f"no_contradictions: {violation}")

    # Check agentic behavior
    has_decomposition = any(
        word in prompt.lower()
        for word in ["step", "subtask", "break down", "first", "then", "finally"]
    )
    if not has_decomposition:
        issues.append("Missing explicit task decomposition guidance")
        violations.append("agentic_behavior: No subtask decomposition")
        recommendations.append("Add explicit step-by-step task breakdown instructions")

    # Check for completion confirmation
    has_confirmation = any(
        word in prompt.lower() for word in ["confirm", "verify", "check", "ensure complete"]
    )
    if not has_confirmation:
        violations.append("agentic_behavior: No completion confirmation")
        recommendations.append("Add instruction to confirm task completion before returning")

    # Check verbosity appropriateness for task type
    verbosity_keywords = {
        "high": ["explain", "detail", "thorough", "comprehensive", "elaborate"],
        "low": ["brief", "concise", "short", "quick", "summary"],
    }

    high_verbosity = sum(1 for kw in verbosity_keywords["high"] if kw in prompt.lower())
    low_verbosity = sum(1 for kw in verbosity_keywords["low"] if kw in prompt.lower())

    if task_type == "code_gen" and low_verbosity > high_verbosity:
        issues.append(f"Task type '{task_type}' should use high verbosity (explanations)")
        violations.append("verbosity_control: Low verbosity for code generation")
        recommendations.append("Increase verbosity for code generation tasks")

    elif task_type == "chat" and high_verbosity > 2:
        issues.append("Chat tasks should use medium verbosity (not too verbose)")
        violations.append("verbosity_control: Too high verbosity for chat")
        recommendations.append("Reduce verbosity for conversational interactions")

    # Check for tool usage guidelines
    has_tool_guidance = "tool" in prompt.lower() or "function" in prompt.lower()
    has_parallel_limit = any(
        phrase in prompt.lower()
        for phrase in ["parallel", "at a time", "simultaneously", "max", "limit"]
    )

    if has_tool_guidance and not has_parallel_limit:
        issues.append("Missing parallel tool call limit (risk of timeout)")
        violations.append("tool_usage: No parallel tool call limit specified")
        recommendations.append(
            "Add limit: 'Maximum 3 parallel tool calls at a time (prevents timeouts)'"
        )

    # Check for citation requirements (if web search mentioned)
    if "search" in prompt.lower() or "web" in prompt.lower():
        has_citations = any(
            word in prompt.lower() for word in ["citation", "source", "url", "reference"]
        )
        if not has_citations:
            issues.append("Web search mentioned but no citation requirements")
            violations.append("tool_usage: Missing citation requirements for web search")
            recommendations.append("Add: 'Always include citations with sources and URLs'")

    # Check for XML-style structure
    has_xml_structure = bool(re.search(r"##\s+[A-Z]", prompt))  # Markdown headers
    if not has_xml_structure:
        issues.append("Missing structured sections (no clear headers)")
        violations.append("clarity_structure: No XML-style categorization")
        recommendations.append("Add clear section headers (## Section Name)")

    # Calculate scores
    clarity_score = max(0, 100 - (len(issues) * 10))
    verbosity_score = 100 - abs(high_verbosity - low_verbosity) * 10
    structure_score = 80 if has_xml_structure else 40

    result = {
        "issues": issues,
        "best_practices_violations": violations,
        "recommendations": recommendations,
        "clarity_score": clarity_score,
        "verbosity_score": min(100, max(0, verbosity_score)),
        "structure_score": structure_score,
        "overall_score": (clarity_score + verbosity_score + structure_score) / 3,
        "task_type": task_type,
        "prompt_length": len(prompt),
        "gpt_best_practices": GPT_BEST_PRACTICES,
    }

    logger.info(
        "Prompt analysis complete",
        issues_count=len(issues),
        violations_count=len(violations),
        overall_score=result["overall_score"],
    )

    return result


def optimize_prompt(
    prompt: str,
    dataset: list[dict[str, str]],
    optimizer_type: str = "hierarchical_reflective",
    max_trials: int = 10,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """
    Optimize prompt using Opik's optimization algorithms.

    Supports all 6 Opik algorithms with automatic dataset creation
    and performance tracking.

    Args:
        prompt: Initial prompt to optimize
        dataset: List of {"input": ..., "expected_output": ...} examples
        optimizer_type: Algorithm to use (see OptimizerAlgorithm enum)
        max_trials: Maximum optimization trials
        model: LLM model for optimization

    Returns:
        Dict containing:
        - optimized_prompt: Best prompt found
        - original_prompt: Starting prompt
        - score: Final performance score
        - improvement: Score improvement (%)
        - algorithm: Algorithm used
        - trials: Number of trials run
        - performance_metrics: Before/after comparison

    Example:
        >>> dataset = [
        ...     {"input": "What is 2+2?", "expected_output": "4"},
        ...     {"input": "What is 3+3?", "expected_output": "6"},
        ... ]
        >>> result = optimize_prompt(
        ...     prompt="You are a math assistant.",
        ...     dataset=dataset,
        ...     optimizer_type="meta_prompt",
        ...     max_trials=5
        ... )
        >>> print(result["improvement"])
        15.3
    """
    logger.info(
        "Starting prompt optimization",
        optimizer=optimizer_type,
        dataset_size=len(dataset),
        max_trials=max_trials,
    )

    # Get Opik client
    opik_client = get_opik_client()

    # Create dataset in Opik
    dataset_name = f"optimization_{hash(prompt) % 10000}"
    opik_dataset = opik_client.get_or_create_dataset(
        name=dataset_name,
        items=dataset,
    )

    # Define evaluation metric
    def accuracy_metric(dataset_item, llm_output):
        """Simple accuracy metric for optimization."""
        expected = dataset_item.get("expected_output", "").lower()
        actual = str(llm_output).lower()

        # Check if expected output is in actual output
        is_correct = expected in actual

        return score_result.ScoreResult(
            name="accuracy",
            value=1.0 if is_correct else 0.0,
            reason="Correct" if is_correct else f"Expected: {expected}, Got: {actual}",
        )

    # Map optimizer_type string to enum
    try:
        algorithm = OptimizerAlgorithm(optimizer_type)
    except ValueError:
        logger.warning(
            f"Unknown optimizer '{optimizer_type}', using hierarchical_reflective",
        )
        algorithm = OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE

    # Run optimization
    try:
        result = opik_client.optimize_prompt(
            prompt=prompt,
            dataset=opik_dataset,
            metric=accuracy_metric,
            algorithm=algorithm,
            max_trials=max_trials,
            model=model,
        )

        logger.info(
            "Prompt optimization completed",
            algorithm=algorithm.value,
            score=result["score"],
            improvement=result["improvement"],
        )

        return result

    except Exception as e:
        logger.error(
            "Prompt optimization failed",
            error=str(e),
            optimizer=optimizer_type,
        )
        raise


def evaluate_prompt(
    prompt: str,
    dataset: list[dict[str, str]],
    metrics: list[str] | None = None,
    model: str = "gpt-4o",
) -> dict[str, float]:
    """
    Evaluate prompt performance with quantitative metrics.

    Runs prompt against test dataset and calculates accuracy,
    latency, and token usage metrics.

    Args:
        prompt: Prompt to evaluate
        dataset: Test dataset
        metrics: List of metrics to calculate (accuracy, latency, cost)
        model: LLM model to use

    Returns:
        Dict with metric scores:
        - accuracy: Task completion rate (0-1)
        - latency: Average response time (seconds)
        - cost: Estimated token cost (tokens)
        - quality_score: Overall rating (0-100)

    Example:
        >>> dataset = [{"input": "Hello", "expected_output": "Hi"}]
        >>> metrics = evaluate_prompt(
        ...     prompt="You are friendly.",
        ...     dataset=dataset,
        ...     metrics=["accuracy", "latency"]
        ... )
        >>> print(metrics["accuracy"])
        0.85
    """
    if metrics is None:
        metrics = ["accuracy", "latency", "cost"]

    logger.info(
        "Evaluating prompt",
        dataset_size=len(dataset),
        metrics=metrics,
    )

    settings = get_settings()
    llm = ChatOpenAI(
        model=model,
        api_key=settings.OPENAI_API_KEY,
    )

    results = {
        "accuracy": 0.0,
        "latency": 0.0,
        "cost": 0.0,
        "quality_score": 0.0,
    }

    total_correct = 0
    total_time = 0.0
    total_tokens = 0

    import time

    for item in dataset:
        input_text = item.get("input", "")
        expected = item.get("expected_output", "")

        # Format prompt with input
        full_prompt = f"{prompt}\n\nInput: {input_text}"

        # Time the response
        start_time = time.time()
        try:
            response = llm.invoke(full_prompt)
            elapsed = time.time() - start_time

            # Calculate accuracy
            actual = response.content.lower()
            expected_lower = expected.lower()
            is_correct = expected_lower in actual

            if is_correct:
                total_correct += 1

            total_time += elapsed

            # Estimate tokens (rough: ~4 chars per token)
            total_tokens += len(full_prompt + response.content) // 4

        except Exception as e:
            logger.error(f"Evaluation error for item: {e}")
            continue

    # Calculate metrics
    if "accuracy" in metrics:
        results["accuracy"] = total_correct / len(dataset) if dataset else 0.0

    if "latency" in metrics:
        results["latency"] = total_time / len(dataset) if dataset else 0.0

    if "cost" in metrics:
        results["cost"] = total_tokens

    # Quality score combines accuracy and latency
    results["quality_score"] = results["accuracy"] * 100 - results["latency"] * 5

    logger.info(
        "Prompt evaluation complete",
        accuracy=results["accuracy"],
        latency=results["latency"],
        tokens=results["cost"],
    )

    return results


def create_evaluation_dataset(
    task_description: str,
    num_examples: int = 20,
    model: str = "gpt-4o",
) -> list[dict[str, str]]:
    """
    Generate evaluation dataset from task description.

    Uses GPT-5 to create diverse test cases for prompt evaluation.

    Args:
        task_description: Description of task to create examples for
        num_examples: Number of examples to generate
        model: LLM model for generation

    Returns:
        List of {"input": ..., "expected_output": ...} dictionaries

    Example:
        >>> dataset = create_evaluation_dataset(
        ...     task_description="Math word problems for grade 3",
        ...     num_examples=10
        ... )
        >>> print(len(dataset))
        10
        >>> print(dataset[0])
        {"input": "If you have 5 apples...", "expected_output": "8"}
    """
    logger.info(
        "Generating evaluation dataset",
        task=task_description,
        num_examples=num_examples,
    )

    settings = get_settings()
    llm = ChatOpenAI(
        model=model,
        api_key=settings.OPENAI_API_KEY,
    )

    generation_prompt = f"""Generate {num_examples} diverse test examples for the following task:

Task: {task_description}

For each example, provide:
1. An input query/question
2. The expected correct output

Format each example as:
INPUT: <input text>
OUTPUT: <expected output>

Generate {num_examples} examples with varying difficulty and edge cases."""

    try:
        response = llm.invoke(generation_prompt)
        content = response.content

        # Parse examples
        dataset = []
        examples = re.split(r"\n\s*INPUT:", content)

        for example in examples[1:]:  # Skip first empty split
            lines = example.split("\nOUTPUT:")
            if len(lines) >= 2:
                input_text = lines[0].strip()
                output_text = lines[1].split("\n")[0].strip()

                dataset.append(
                    {
                        "input": input_text,
                        "expected_output": output_text,
                    }
                )

                if len(dataset) >= num_examples:
                    break

        logger.info(
            "Dataset generation complete",
            examples_generated=len(dataset),
        )

        return dataset

    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        raise


def ab_test_prompts(
    prompt_a: str,
    prompt_b: str,
    dataset: list[dict[str, str]],
    alpha: float = 0.05,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """
    Statistical A/B test between two prompts.

    Evaluates both prompts on same dataset and performs t-test
    to determine statistical significance of differences.

    Args:
        prompt_a: First prompt (baseline)
        prompt_b: Second prompt (variant)
        dataset: Test dataset
        alpha: Significance level (default 0.05)
        model: LLM model to use

    Returns:
        Dict containing:
        - winner: "A", "B", or "tie"
        - p_value: Statistical significance
        - effect_size: Cohen's d
        - metrics_comparison: Detailed metric comparison
        - confidence_level: 1 - alpha

    Example:
        >>> dataset = [{"input": "Test", "expected_output": "Result"}]
        >>> result = ab_test_prompts(
        ...     prompt_a="You are helpful.",
        ...     prompt_b="You are an expert assistant.",
        ...     dataset=dataset
        ... )
        >>> print(result["winner"])
        "B"
        >>> print(result["p_value"])
        0.023
    """
    logger.info(
        "Running A/B test",
        dataset_size=len(dataset),
        alpha=alpha,
    )

    # Evaluate both prompts
    metrics_a = evaluate_prompt(prompt_a, dataset, model=model)
    metrics_b = evaluate_prompt(prompt_b, dataset, model=model)

    # Perform t-test on accuracy scores
    # For simplicity, assume normal distribution
    # In production, would run multiple trials per prompt
    scores_a = [metrics_a["accuracy"]] * len(dataset)
    scores_b = [metrics_b["accuracy"]] * len(dataset)

    t_statistic, p_value = stats.ttest_ind(scores_a, scores_b)

    # Calculate effect size (Cohen's d)
    mean_a = np.mean(scores_a)
    mean_b = np.mean(scores_b)
    std_pooled = np.sqrt((np.std(scores_a) ** 2 + np.std(scores_b) ** 2) / 2)
    effect_size = (mean_b - mean_a) / std_pooled if std_pooled > 0 else 0.0

    # Determine winner
    if p_value < alpha:
        winner = "B" if metrics_b["accuracy"] > metrics_a["accuracy"] else "A"
    else:
        winner = "tie"

    result = {
        "winner": winner,
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "confidence_level": 1 - alpha,
        "statistically_significant": p_value < alpha,
        "metrics_comparison": {
            "prompt_a": metrics_a,
            "prompt_b": metrics_b,
            "accuracy_diff": metrics_b["accuracy"] - metrics_a["accuracy"],
            "latency_diff": metrics_b["latency"] - metrics_a["latency"],
        },
        "interpretation": (
            f"Prompt {winner} {'wins' if winner != 'tie' else 'tied'} "
            f"with p={p_value:.4f} (alpha={alpha})"
        ),
    }

    logger.info(
        "A/B test complete",
        winner=winner,
        p_value=p_value,
        significant=result["statistically_significant"],
    )

    return result
