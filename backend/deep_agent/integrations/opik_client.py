"""
Opik Client Integration for Prompt Optimization.

Provides a unified interface to Opik's 6 optimization algorithms:
1. HierarchicalReflectiveOptimizer (Rank #1, 67.83%) - Best for complex prompts
2. FewShotBayesianOptimizer (Rank #2, 59.17%) - Best for few-shot examples
3. EvolutionaryOptimizer (Rank #3, 52.51%) - Multi-objective optimization
4. MetaPromptOptimizer (Rank #4, 38.75%) - LLM critique + MCP tool support
5. GepaOptimizer (Rank #5, 32.27%) - Single-turn tasks
6. ParameterOptimizer - LLM parameter tuning (temperature, top_p)

Integrates with LangSmith for tracing and provides async support.
"""

import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional

import opik
from structlog import get_logger

from deep_agent.config.settings import Settings, get_settings

logger = get_logger(__name__)

# TODO: opik_optimizer module is not yet available in opik 0.2.0
# This is a placeholder implementation for Phase 1 development
# When Opik releases optimizer functionality, replace these with real imports:
# from opik import optimizers as opik_optimizer
# For now, we create placeholder classes that match the expected interface

class _PlaceholderOptimizer:
    """Placeholder optimizer until Opik releases optimizer functionality."""
    def optimize_prompt(self, prompt: Any, dataset: Any, metric: Any, max_trials: int = 10) -> Any:
        # Placeholder result
        result = type('obj', (object,), {
            'prompt': str(prompt),
            'score': 0.0,
            'improvement': 0.0
        })()
        logger.warning(
            "Using placeholder optimizer - opik_optimizer not available",
            optimizer_type=type(self).__name__,
        )
        return result

class _PlaceholderChatPrompt:
    """Placeholder ChatPrompt until Opik releases optimizer functionality."""
    def __init__(self, messages: List[Dict[str, str]], model: str, tools: Optional[List] = None, function_map: Optional[Dict] = None):
        self.messages = messages
        self.model = model
        self.tools = tools
        self.function_map = function_map

    def __str__(self) -> str:
        return self.messages[0]["content"] if self.messages else ""

# Placeholder module structure
class _OpikOptimizerPlaceholder:
    """Placeholder for opik_optimizer module."""
    HierarchicalReflectiveOptimizer = _PlaceholderOptimizer
    FewShotBayesianOptimizer = _PlaceholderOptimizer
    EvolutionaryOptimizer = _PlaceholderOptimizer
    MetaPromptOptimizer = _PlaceholderOptimizer
    GepaOptimizer = _PlaceholderOptimizer
    ParameterOptimizer = _PlaceholderOptimizer
    ChatPrompt = _PlaceholderChatPrompt

opik_optimizer = _OpikOptimizerPlaceholder()


class OptimizerAlgorithm(str, Enum):
    """Available optimization algorithms with their characteristics."""

    HIERARCHICAL_REFLECTIVE = "hierarchical_reflective"  # Rank #1 (67.83%)
    FEW_SHOT_BAYESIAN = "few_shot_bayesian"  # Rank #2 (59.17%)
    EVOLUTIONARY = "evolutionary"  # Rank #3 (52.51%)
    META_PROMPT = "meta_prompt"  # Rank #4 (38.75%) - Supports MCP tools
    GEPA = "gepa"  # Rank #5 (32.27%)
    PARAMETER = "parameter"  # LLM parameter tuning


# Algorithm selection guide for context-engineering-expert
ALGORITHM_SELECTION_GUIDE = """
## Opik Optimization Algorithm Selection Guide

Choose the appropriate algorithm based on your optimization goals:

### 1. HierarchicalReflectiveOptimizer (RECOMMENDED - Rank #1, 67.83% avg)
**Best for:** Complex prompts requiring systematic refinement
- Uses hierarchical root cause analysis
- Analyzes failures in batches
- Synthesizes findings and addresses failure modes
- **When to use:** Multi-step prompts, complex reasoning chains, systematic improvements needed
- **Benchmark:** Arc: 92.70%, GSM8K: 28.00%, RagBench: 82.8%

### 2. FewShotBayesianOptimizer (Rank #2, 59.17% avg)
**Best for:** Optimizing few-shot examples and demonstrations
- Uses Bayesian optimization (Optuna)
- Finds optimal number and combination of few-shot examples
- **When to use:** Chat models, few-shot prompts, example-based learning
- **Benchmark:** Arc: 28.09%, GSM8K: 59.26%, RagBench: 90.15%

### 3. EvolutionaryOptimizer (Rank #3, 52.51% avg)
**Best for:** Discovering novel prompt structures
- Employs genetic algorithms
- Evolves population of prompts
- Supports multi-objective optimization (score vs. length)
- **When to use:** Exploring creative solutions, multi-objective goals, unconstrained search
- **Benchmark:** Arc: 40.00%, GSM8K: 25.53%, RagBench: 92.00%

### 4. MetaPromptOptimizer (Rank #4, 38.75% avg)
**Best for:** General prompt refinement + MCP tool optimization
- Uses LLM to critique and iteratively refine prompts
- **SUPPORTS MCP TOOL CALLING OPTIMIZATION** (unique feature)
- **When to use:** Prompt clarity/wording, structural improvements, agents with tools
- **Benchmark:** Arc: 25.00%, GSM8K: 26.93%, RagBench: 64.31%

### 5. GepaOptimizer (Rank #5, 32.27% avg)
**Best for:** Single-turn tasks with reflection model
- Wraps external GEPA package
- Optimizes single system prompt
- **When to use:** Simple, single-turn completions (requires `pip install gepa`)
- **Benchmark:** Arc: 6.55%, GSM8K: 26.08%, RagBench: 64.17%

### 6. ParameterOptimizer
**Best for:** Tuning LLM call parameters
- Optimizes temperature, top_p, etc. using Bayesian optimization
- Uses Optuna for efficient parameter search
- **When to use:** Model behavior tuning WITHOUT changing prompt text
- **Note:** No prompt changes, only parameter optimization

**Default Recommendation:** Start with `hierarchical_reflective` for general use.
"""


class OpikClient:
    """
    Unified Opik client for prompt optimization.

    Provides async-safe interface to all 6 Opik optimization algorithms
    with LangSmith tracing integration.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize Opik client.

        Args:
            settings: Application settings. If None, uses get_settings().

        Raises:
            ValueError: If OPIK_API_KEY not configured.
        """
        self.settings = settings or get_settings()

        if not self.settings.OPIK_API_KEY:
            raise ValueError(
                "OPIK_API_KEY not configured. "
                "Please set it in .env or export OPIK_API_KEY=your_key"
            )

        # Initialize Opik client
        self.client = opik.Opik(
            api_key=self.settings.OPIK_API_KEY,
            workspace=self.settings.OPIK_WORKSPACE,
        )

        # Project name for organizing optimization experiments
        self.project_name = self.settings.OPIK_PROJECT

        logger.info(
            "Opik client initialized",
            project=self.project_name,
            workspace=self.settings.OPIK_WORKSPACE,
        )

    def get_or_create_dataset(
        self,
        name: str,
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Get existing dataset or create new one.

        Args:
            name: Dataset name
            items: Optional list of dataset items to insert

        Returns:
            Opik Dataset object
        """
        try:
            dataset = self.client.get_or_create_dataset(name=name)

            if items:
                dataset.insert(items)
                logger.info(
                    "Dataset items added",
                    dataset=name,
                    items_count=len(items),
                )

            return dataset

        except Exception as e:
            logger.error(
                "Failed to get/create dataset",
                dataset=name,
                error=str(e),
            )
            raise

    def get_optimizer(
        self,
        algorithm: OptimizerAlgorithm,
    ) -> Any:
        """
        Get optimizer instance for specified algorithm.

        Args:
            algorithm: Optimizer algorithm to use

        Returns:
            Opik optimizer instance

        Raises:
            ValueError: If algorithm not supported or GEPA not installed
        """
        try:
            if algorithm == OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE:
                optimizer = opik_optimizer.HierarchicalReflectiveOptimizer()

            elif algorithm == OptimizerAlgorithm.FEW_SHOT_BAYESIAN:
                optimizer = opik_optimizer.FewShotBayesianOptimizer()

            elif algorithm == OptimizerAlgorithm.EVOLUTIONARY:
                optimizer = opik_optimizer.EvolutionaryOptimizer()

            elif algorithm == OptimizerAlgorithm.META_PROMPT:
                optimizer = opik_optimizer.MetaPromptOptimizer()

            elif algorithm == OptimizerAlgorithm.GEPA:
                try:
                    optimizer = opik_optimizer.GepaOptimizer()
                except ImportError:
                    raise ValueError(
                        "GEPA optimizer requires `pip install gepa`. "
                        "Install it and try again."
                    )

            elif algorithm == OptimizerAlgorithm.PARAMETER:
                optimizer = opik_optimizer.ParameterOptimizer()

            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            logger.info(
                "Optimizer created",
                algorithm=algorithm.value,
            )

            return optimizer

        except Exception as e:
            logger.error(
                "Failed to create optimizer",
                algorithm=algorithm.value,
                error=str(e),
            )
            raise

    async def optimize_prompt_async(
        self,
        prompt: str,
        dataset: Any,
        metric: Any,
        algorithm: OptimizerAlgorithm = OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE,
        max_trials: int = 10,
        model: str = "gpt-4o",
        tools: Optional[List[Dict[str, Any]]] = None,
        function_map: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize prompt asynchronously with specified algorithm.

        Args:
            prompt: Initial prompt to optimize
            dataset: Opik dataset for evaluation
            metric: Evaluation metric function
            algorithm: Optimization algorithm to use
            max_trials: Maximum optimization trials
            model: LLM model to use
            tools: Optional MCP tools (for MetaPrompt algorithm)
            function_map: Optional function mapping (for MetaPrompt with tools)

        Returns:
            Dict with optimized prompt and metrics
        """
        try:
            # Create ChatPrompt object
            chat_prompt = opik_optimizer.ChatPrompt(
                messages=[
                    {"role": "system", "content": prompt},
                ],
                model=model,
                tools=tools,
                function_map=function_map,
            )

            # Get optimizer
            optimizer = self.get_optimizer(algorithm)

            # Run optimization in thread pool (Opik is sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: optimizer.optimize_prompt(
                    prompt=chat_prompt,
                    dataset=dataset,
                    metric=metric,
                    max_trials=max_trials,
                ),
            )

            logger.info(
                "Prompt optimization completed",
                algorithm=algorithm.value,
                trials=max_trials,
                score=result.score if hasattr(result, "score") else None,
            )

            # Extract results
            optimized_prompt = str(result.prompt) if hasattr(result, "prompt") else prompt
            score = float(result.score) if hasattr(result, "score") else 0.0
            improvement = float(result.improvement) if hasattr(result, "improvement") else 0.0

            return {
                "optimized_prompt": optimized_prompt,
                "original_prompt": prompt,
                "score": score,
                "improvement": improvement,
                "algorithm": algorithm.value,
                "trials": max_trials,
                "result": result,  # Full result object for advanced access
            }

        except Exception as e:
            logger.error(
                "Prompt optimization failed",
                algorithm=algorithm.value,
                error=str(e),
            )
            raise

    def optimize_prompt(
        self,
        prompt: str,
        dataset: Any,
        metric: Any,
        algorithm: OptimizerAlgorithm = OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE,
        max_trials: int = 10,
        model: str = "gpt-4o",
        tools: Optional[List[Dict[str, Any]]] = None,
        function_map: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for optimize_prompt_async.

        For async contexts, use optimize_prompt_async directly.
        """
        return asyncio.run(
            self.optimize_prompt_async(
                prompt=prompt,
                dataset=dataset,
                metric=metric,
                algorithm=algorithm,
                max_trials=max_trials,
                model=model,
                tools=tools,
                function_map=function_map,
            )
        )


# Singleton instance
_opik_client: Optional[OpikClient] = None


def get_opik_client(settings: Optional[Settings] = None) -> OpikClient:
    """
    Get or create Opik client singleton.

    Args:
        settings: Optional settings. If None, uses get_settings().

    Returns:
        OpikClient instance
    """
    global _opik_client

    if _opik_client is None:
        _opik_client = OpikClient(settings=settings)

    return _opik_client
