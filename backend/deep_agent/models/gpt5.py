"""GPT-5 configuration models for LangChain ChatOpenAI integration."""
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
