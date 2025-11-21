"""
Tools for DeepAgents.

This module provides LangChain tools that extend agent capabilities with:
- Web search (Perplexity MCP integration)
- Prompt optimization (Opik integration for context engineering)

Tools are automatically registered with DeepAgents and available for
LLM-driven tool selection during agent execution.

Exports:
    web_search: Search the web using Perplexity MCP
    analyze_prompt: Analyze prompt against GPT-5 best practices
    optimize_prompt: Optimize prompt using Opik algorithms
    evaluate_prompt: Evaluate prompt performance metrics
    create_evaluation_dataset: Generate test cases for prompt evaluation
    ab_test_prompts: Statistical A/B testing for prompt variants
"""

from deep_agent.tools.prompt_optimization import (
    ab_test_prompts,
    analyze_prompt,
    create_evaluation_dataset,
    evaluate_prompt,
    optimize_prompt,
)
from deep_agent.tools.web_search import web_search

__all__ = [
    "web_search",
    "analyze_prompt",
    "optimize_prompt",
    "evaluate_prompt",
    "create_evaluation_dataset",
    "ab_test_prompts",
]
