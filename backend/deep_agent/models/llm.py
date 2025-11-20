"""
LLM configuration models for LangChain ChatOpenAI integration.

This module provides configuration models for creating ChatOpenAI instances
with GPT models (gpt-4, gpt-5, gpt-6+), including reasoning effort and verbosity controls.

Note: Parameters are GPT-specific. Future multi-provider support will add provider-specific
config classes (e.g., ClaudeConfig, GeminiConfig) in model fallback middleware.

Models:
    ReasoningEffort: Enum for reasoning levels (minimal, low, medium, high) - GPT-specific
    Verbosity: Enum for response verbosity levels (low, medium, high) - GPT-specific
    GPTConfig: Configuration for ChatOpenAI with GPT parameters

Configuration Options:
    - model_name: GPT model name (gpt-4, gpt-5, gpt-6+, gpt-5-mini, gpt-5-nano)
    - reasoning_effort: Control thinking depth (maps to OpenAI {"effort": "level"})
    - verbosity: Control response detail level (GPT-specific parameter)
    - max_tokens: Token limit for responses (default 4096)

Design Notes:
    - ReasoningEffort maps directly to OpenAI's reasoning parameter
    - Higher reasoning effort = slower but more thorough responses
    - Verbosity is independent of reasoning effort (can have high reasoning + low verbosity)
    - Temperature parameter DEPRECATED for GPT-5+ reasoning models

Example:
    >>> from deep_agent.models.llm import GPTConfig, ReasoningEffort, Verbosity
    >>> # Create config for deep reasoning with concise output
    >>> config = GPTConfig(
    ...     model_name="gpt-5",
    ...     reasoning_effort=ReasoningEffort.HIGH,
    ...     verbosity=Verbosity.LOW
    ... )
    >>> # Use with LangChain ChatOpenAI
    >>> # llm = create_llm(config)  # See backend/deep_agent/services/llm_factory.py

Usage with LLMFactory:
    >>> from deep_agent.services.llm_factory import create_llm
    >>> llm = create_llm(
    ...     api_key="sk-...",
    ...     config=GPTConfig(reasoning_effort=ReasoningEffort.HIGH, verbosity=Verbosity.LOW)
    ... )
"""
from enum import Enum

from pydantic import BaseModel, Field


class ReasoningEffort(str, Enum):
    """
    Reasoning effort levels for GPT models (GPT-specific parameter).

    Maps to ChatOpenAI reasoning parameter: {"effort": "minimal"|"low"|"medium"|"high"}

    Note: This is OpenAI-specific. Claude uses "thinking" mode, Gemini has different parameters.
    """

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verbosity(str, Enum):
    """
    Response verbosity levels for GPT models (GPT-specific parameter).

    Controls the length and depth of model responses.

    Note: This is OpenAI-specific. Other providers have different verbosity controls.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GPTConfig(BaseModel):
    """
    Configuration for creating ChatOpenAI instances with GPT models.

    Note: Parameters are GPT-specific. Future multi-provider support will use
    provider-specific config classes (ClaudeConfig, GeminiConfig, etc.).
    """

    model_name: str = Field(
        default="gpt-5.1-2025-11-13",
        description="GPT model name (use dated release format, e.g., gpt-5.1-2025-11-13)",
    )
    reasoning_effort: ReasoningEffort = Field(
        default=ReasoningEffort.MEDIUM,
        description="Reasoning effort level (GPT-specific)",
    )
    verbosity: Verbosity = Field(
        default=Verbosity.MEDIUM,
        description="Response verbosity level (GPT-specific)",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens in response",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "gpt-5",
                "reasoning_effort": "medium",
                "verbosity": "medium",
                "max_tokens": 4096,
            }
        }
    }
