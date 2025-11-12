"""
GPT-5 configuration models for LangChain ChatOpenAI integration.

This module provides configuration models for creating ChatOpenAI instances
with GPT-5 models, including reasoning effort and verbosity controls.

Models:
    ReasoningEffort: Enum for reasoning levels (minimal, low, medium, high)
    Verbosity: Enum for response verbosity levels (low, medium, high)
    GPT5Config: Configuration for ChatOpenAI with GPT-5 parameters

Configuration Options:
    - model_name: GPT-5 model variant (gpt-5, gpt-5-mini, gpt-5-nano)
    - reasoning_effort: Control thinking depth (maps to OpenAI {"effort": "level"})
    - verbosity: Control response detail level
    - max_tokens: Token limit for responses (default 4096)
    - temperature: Randomness/creativity (0.0=deterministic, 1.0=creative)

Design Notes:
    - ReasoningEffort maps directly to OpenAI's reasoning parameter
    - Higher reasoning effort = slower but more thorough responses
    - Verbosity is independent of reasoning effort (can have high reasoning + low verbosity)

Example:
    >>> from deep_agent.models.gpt5 import GPT5Config, ReasoningEffort, Verbosity
    >>> # Create config for deep reasoning with concise output
    >>> config = GPT5Config(
    ...     model_name="gpt-5",
    ...     reasoning_effort=ReasoningEffort.HIGH,
    ...     verbosity=Verbosity.LOW,
    ...     temperature=0.7
    ... )
    >>> # Use with LangChain ChatOpenAI
    >>> # llm = create_gpt5_llm(config)  # See backend/deep_agent/llm/gpt5.py

Usage with LLMFactory:
    >>> from deep_agent.llm.factory import LLMFactory
    >>> factory = LLMFactory()
    >>> llm = factory.create_llm(
    ...     model_type="gpt5",
    ...     reasoning_effort="high",
    ...     verbosity="low"
    ... )
"""
from enum import Enum

from pydantic import BaseModel, Field


class ReasoningEffort(str, Enum):
    """
    Reasoning effort levels for GPT-5.

    Maps to ChatOpenAI reasoning parameter: {"effort": "minimal"|"low"|"medium"|"high"}
    """

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verbosity(str, Enum):
    """
    Response verbosity levels for GPT-5.

    Maps to ChatOpenAI verbosity parameter.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GPT5Config(BaseModel):
    """Configuration for creating ChatOpenAI instances with GPT-5."""

    model_name: str = Field(
        default="gpt-5",
        description="GPT-5 model name (gpt-5, gpt-5-mini, gpt-5-nano)",
    )
    reasoning_effort: ReasoningEffort = Field(
        default=ReasoningEffort.MEDIUM,
        description="Reasoning effort level",
    )
    verbosity: Verbosity = Field(
        default=Verbosity.MEDIUM,
        description="Response verbosity level",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens in response",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for response randomness",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "gpt-5",
                "reasoning_effort": "medium",
                "verbosity": "medium",
                "max_tokens": 4096,
                "temperature": 0.7,
            }
        }
    }
