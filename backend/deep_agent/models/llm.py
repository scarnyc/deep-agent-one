"""
LLM configuration models for multi-provider LangChain integration.

This module provides configuration models for creating LLM instances with
different providers (OpenAI GPT, Google Gemini) using provider-specific parameters.

Models:
    ReasoningEffort: Enum for GPT reasoning levels (minimal, low, medium, high)
    Verbosity: Enum for GPT response verbosity (low, medium, high)
    ThinkingLevel: Enum for Gemini thinking depth (low, medium, high)
    GPTConfig: Configuration for ChatOpenAI with GPT-5.1 parameters
    GeminiConfig: Configuration for ChatGoogleGenerativeAI with Gemini 3 Pro parameters

Provider Differences:
    - GPT-5.1: Uses `reasoning_effort` (no temperature support)
    - Gemini 3 Pro: Uses `temperature` (keep at 1.0) + `thinking_level`

Example:
    >>> from deep_agent.models.llm import GPTConfig, GeminiConfig, ReasoningEffort
    >>> # GPT-5.1 config (fallback)
    >>> gpt_config = GPTConfig(reasoning_effort=ReasoningEffort.HIGH)
    >>> # Gemini 3 Pro config (primary)
    >>> gemini_config = GeminiConfig(thinking_level=ThinkingLevel.HIGH)

Usage with LLMFactory:
    >>> from deep_agent.services.llm_factory import create_gpt_llm, create_gemini_llm
    >>> primary_llm = create_gemini_llm(api_key="...", config=gemini_config)
    >>> fallback_llm = create_gpt_llm(api_key="sk-...", config=gpt_config)
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


class ThinkingLevel(str, Enum):
    """
    Thinking depth levels for Gemini 3 Pro models (Gemini-specific parameter).

    Controls the maximum depth of the model's internal reasoning process.
    Gemini 3 treats these as relative allowances for thinking rather than strict guarantees.

    WARNING: If not specified, Gemini 3 Pro defaults to HIGH.

    Note: This is Gemini-specific. GPT uses `reasoning_effort` instead.
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


class GeminiConfig(BaseModel):
    """
    Configuration for creating ChatGoogleGenerativeAI instances with Gemini 3 Pro.

    Note: Parameters are Gemini-specific. GPT models use different parameters
    (reasoning_effort instead of temperature/thinking_level).

    WARNING: Keep temperature at 1.0 per Google documentation. Lower values
    can cause looping or degraded performance on complex reasoning tasks.
    """

    model_name: str = Field(
        default="gemini-3-pro-preview",
        description="Gemini model name (e.g., gemini-3-pro-preview)",
    )
    temperature: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Temperature for sampling (keep at 1.0 for Gemini 3 Pro)",
    )
    thinking_level: ThinkingLevel = Field(
        default=ThinkingLevel.HIGH,
        description="Thinking depth level (Gemini-specific, default: high)",
    )
    max_output_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens in response",
    )
    streaming: bool = Field(
        default=True,
        description="Enable streaming responses",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "gemini-3-pro-preview",
                "temperature": 1.0,
                "thinking_level": "high",
                "max_output_tokens": 4096,
                "streaming": True,
            }
        }
    }
