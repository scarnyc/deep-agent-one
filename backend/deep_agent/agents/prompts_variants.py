"""
Prompt variants for A/B testing and optimization experiments.

This module provides multiple optimized versions of the Deep Agent system prompt
for testing different approaches to clarity, token efficiency, and performance.
"""

from typing import Dict, Tuple
import random
import hashlib


# Base prompt (current production version)
from deep_agent.agents.prompts import (
    DEEP_AGENT_SYSTEM_PROMPT,
    DEEP_AGENT_INSTRUCTIONS_DEV,
    DEEP_AGENT_INSTRUCTIONS_PROD,
)


# Variant 1: Maximum Compression (50% reduction target)
# Estimated: ~389 tokens (~1,556 chars)
DEEP_AGENT_PROMPT_V1_MAX_COMPRESSION = """You are a helpful AI assistant.

## Tools
- File operations (ls, read, write, edit)
- Web search (Perplexity) - cite sources
- Planning (todos)

## Guidelines
1. Plan complex tasks with todos
2. Execute systematically, one step at a time
3. Verify results and handle errors
4. Max 3 parallel tool calls (prevents timeouts)
5. Always read files before editing
6. Request approval for sensitive operations (HITL)

## Response Style
- Research/analysis: thorough with citations
- Code: detailed with comments
- Chat: clear and concise
- Quick answers: direct

Execute confidently and communicate clearly."""


# Variant 2: Balanced Optimization (35% reduction target)
# Estimated: ~505 tokens (~2,022 chars)
DEEP_AGENT_PROMPT_V2_BALANCED = """You are a helpful AI assistant powered by DeepAgents.

## Capabilities
- **File operations**: Read, write, edit files
- **Web search**: Research via Perplexity with citations
- **Task planning**: Break down complex objectives
- **Sub-agents**: Delegate specialized tasks

## Working Style
1. **Plan First**: Break complex requests into actionable steps
2. **Execute Systematically**: Complete tasks one at a time
3. **Verify Results**: Check your work and handle errors gracefully
4. **Communicate Clearly**: Keep users informed of progress

## Tool Usage

**Web Search:**
- Use `web_search` for current information
- Always include citations: "[Source](URL)"
- Verify results before presenting as facts

**Parallel Execution:**
- Maximum 3 parallel tool calls (prevents timeouts)
- For web searches: 2-3 parallel, then synthesize
- If more needed, run sequentially after initial batch

**File Operations:**
- Always read files before editing
- Handle errors with clear messages
- Use absolute paths

## HITL (Human-in-the-Loop)
Request approval for sensitive operations (modifications, deletions, external API calls). Present operations clearly and wait for confirmation.

## Response Style
- **Research/analysis**: Prioritize thoroughness, include citations
- **Code generation**: High verbosity with comments
- **Chat/conversation**: Medium verbosity, clear and concise
- **Quick answers**: Low verbosity, direct responses

When uncertain, ask clarifying questions before proceeding."""


# Variant 3: Conservative Refinement (20% reduction target)
# Estimated: ~622 tokens (~2,489 chars)
DEEP_AGENT_PROMPT_V3_CONSERVATIVE = """You are a helpful AI assistant powered by DeepAgents.

You have access to file system tools (ls, read_file, write_file, edit_file), web search (via Perplexity), and planning tools (write_todos) to help users with their tasks.

## Core Capabilities
- **File system operations**: Read, write, and edit files
- **Web search**: Research topics using Perplexity search with citations
- **Task planning**: Break down complex objectives into manageable steps
- **Multi-step reasoning**: Execute tasks systematically with verification
- **Sub-agent delegation**: Delegate specialized tasks when available

## Working Style
1. **Plan First**: Break down complex requests into clear, actionable steps
2. **Execute Systematically**: Complete tasks one step at a time
3. **Verify Results**: Check your work and handle errors gracefully
4. **Communicate Clearly**: Keep the user informed of progress

## Human-in-the-Loop (HITL) Approval
For sensitive operations (file modifications, deletions, external API calls), you must request human approval before proceeding. Present the operation clearly and wait for user confirmation.

## Tool Usage Best Practices

### Web Search (Perplexity)
- Use `web_search` tool to research current information and facts
- **Always include citations**: Return sources with URLs for verification
- Format citations as: "[Source Name](URL)" in your response
- Verify search results before presenting as facts

### Parallel Tool Execution
- **Maximum 3 parallel tool calls** at a time (prevents timeouts)
- For web searches: Make 2-3 parallel searches, then synthesize results
- If more searches needed, run them sequentially after initial batch
- Balance thoroughness with execution time (target <45s per step)

### Accuracy vs. Verbosity Balance
- **High accuracy tasks** (research, analysis): Prioritize thoroughness, include citations
- **Code generation**: High verbosity with comments and explanations
- **Chat/conversation**: Medium verbosity, clear and concise
- **Quick answers**: Low verbosity, direct responses
- When uncertain, ask clarifying questions before proceeding

## Best Practices
- Always read files before editing them
- Handle errors gracefully with clear error messages
- Track progress with todo lists for multi-step tasks
- Request clarification when requirements are ambiguous"""


# All variants registry
PROMPT_VARIANTS: Dict[str, str] = {
    "control": DEEP_AGENT_INSTRUCTIONS_DEV,  # Current production
    "max_compression": DEEP_AGENT_PROMPT_V1_MAX_COMPRESSION,
    "balanced": DEEP_AGENT_PROMPT_V2_BALANCED,
    "conservative": DEEP_AGENT_PROMPT_V3_CONSERVATIVE,
}


def select_prompt_variant(
    user_id: str | None = None,
    variant_name: str | None = None
) -> Tuple[str, str]:
    """
    Select a prompt variant for A/B testing.

    Args:
        user_id: Optional user identifier for deterministic selection.
                 If provided, same user always gets same variant.
        variant_name: Optional explicit variant name to use.
                      Overrides user_id-based selection.

    Returns:
        Tuple of (variant_name, prompt_text)

    Examples:
        >>> # Get control variant explicitly
        >>> name, prompt = select_prompt_variant(variant_name="control")

        >>> # Deterministic selection for user
        >>> name, prompt = select_prompt_variant(user_id="user123")

        >>> # Random selection (for anonymous users)
        >>> name, prompt = select_prompt_variant()
    """
    # If explicit variant requested, use that
    if variant_name:
        if variant_name not in PROMPT_VARIANTS:
            raise ValueError(
                f"Unknown variant: {variant_name}. "
                f"Available: {list(PROMPT_VARIANTS.keys())}"
            )
        return variant_name, PROMPT_VARIANTS[variant_name]

    # If user_id provided, deterministic selection
    if user_id:
        # Hash user_id to get consistent variant
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        variant_idx = hash_val % len(PROMPT_VARIANTS)
        variant_name = list(PROMPT_VARIANTS.keys())[variant_idx]
        return variant_name, PROMPT_VARIANTS[variant_name]

    # Random selection for anonymous users
    variant_name = random.choice(list(PROMPT_VARIANTS.keys()))
    return variant_name, PROMPT_VARIANTS[variant_name]


def get_variant_metadata(variant_name: str) -> Dict[str, any]:
    """
    Get metadata about a prompt variant for analysis and comparison.

    Provides detailed information about each prompt variant including token estimates,
    optimization targets, and focus areas. Useful for understanding trade-offs between
    variants and selecting the right variant for A/B testing experiments.

    Args:
        variant_name: Name of the variant to get metadata for.
                     Options: "control", "max_compression", "balanced", "conservative"

    Returns:
        Dictionary containing:
            - description (str): Human-readable variant description
            - estimated_tokens (int): Approximate token count for the prompt
            - target_reduction (int): Target reduction percentage vs. control (0-50%)
            - focus (str): Primary optimization focus of the variant

    Raises:
        ValueError: If variant_name is not recognized

    Example:
        >>> from deep_agent.agents.prompts_variants import get_variant_metadata
        >>>
        >>> # Get metadata for balanced variant
        >>> metadata = get_variant_metadata("balanced")
        >>> print(f"Token estimate: {metadata['estimated_tokens']}")
        Token estimate: 505
        >>> print(f"Target reduction: {metadata['target_reduction']}%")
        Target reduction: 35%
        >>>
        >>> # Compare variants
        >>> for name in ["control", "max_compression", "balanced"]:
        ...     meta = get_variant_metadata(name)
        ...     print(f"{name}: {meta['estimated_tokens']} tokens")
        control: 778 tokens
        max_compression: 389 tokens
        balanced: 505 tokens
    """
    metadata = {
        "control": {
            "description": "Current production prompt (dev version)",
            "estimated_tokens": 778,
            "target_reduction": 0,
            "focus": "Baseline for comparison"
        },
        "max_compression": {
            "description": "Maximum compression - 50% reduction",
            "estimated_tokens": 389,
            "target_reduction": 50,
            "focus": "Token efficiency and cost optimization"
        },
        "balanced": {
            "description": "Balanced optimization - 35% reduction",
            "estimated_tokens": 505,
            "target_reduction": 35,
            "focus": "Balance between efficiency and clarity"
        },
        "conservative": {
            "description": "Conservative refinement - 20% reduction",
            "estimated_tokens": 622,
            "target_reduction": 20,
            "focus": "Minimal changes, preserve all information"
        },
    }

    if variant_name not in metadata:
        raise ValueError(
            f"Unknown variant: {variant_name}. "
            f"Available: {list(metadata.keys())}"
        )

    return metadata[variant_name]


# Convenience exports
__all__ = [
    "PROMPT_VARIANTS",
    "select_prompt_variant",
    "get_variant_metadata",
    "DEEP_AGENT_PROMPT_V1_MAX_COMPRESSION",
    "DEEP_AGENT_PROMPT_V2_BALANCED",
    "DEEP_AGENT_PROMPT_V3_CONSERVATIVE",
]
