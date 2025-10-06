"""GPT-5 Pydantic models for request/response handling."""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReasoningEffort(str, Enum):
    """Reasoning effort levels for GPT-5."""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verbosity(str, Enum):
    """Response verbosity levels."""

    STANDARD = "standard"
    VERBOSE = "verbose"
    CONCISE = "concise"


class GPT5Config(BaseModel):
    """Configuration for GPT-5 API requests."""

    model_name: str = Field(default="gpt-5", description="GPT-5 model name")
    reasoning_effort: ReasoningEffort = Field(
        default=ReasoningEffort.MEDIUM,
        description="Reasoning effort level",
    )
    verbosity: Verbosity = Field(
        default=Verbosity.STANDARD,
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
    stream: bool = Field(
        default=True,
        description="Enable streaming responses",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "gpt-5",
                "reasoning_effort": "medium",
                "verbosity": "standard",
                "max_tokens": 4096,
                "temperature": 0.7,
                "stream": True,
            }
        }
    }


class GPT5Request(BaseModel):
    """Request model for GPT-5 API calls."""

    messages: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of conversation messages",
    )
    config: GPT5Config = Field(
        default_factory=GPT5Config,
        description="GPT-5 configuration",
    )

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate messages are not empty."""
        if not v:
            raise ValueError("Messages list cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is 2+2?"},
                ],
                "config": {
                    "reasoning_effort": "medium",
                    "stream": True,
                },
            }
        }
    }


class GPT5Response(BaseModel):
    """Response model from GPT-5 API."""

    content: str = Field(..., description="Response content")
    reasoning_effort: ReasoningEffort = Field(
        ...,
        description="Reasoning effort used",
    )
    tokens_used: int = Field(..., ge=0, description="Total tokens used")
    model: str = Field(..., description="Model name used")
    finish_reason: str = Field(
        default="stop",
        description="Reason the generation stopped",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "2 + 2 equals 4.",
                "reasoning_effort": "medium",
                "tokens_used": 25,
                "model": "gpt-5",
                "finish_reason": "stop",
            }
        }
    }
