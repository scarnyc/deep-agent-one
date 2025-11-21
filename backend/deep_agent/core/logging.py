"""Structured logging configuration using structlog."""
import logging
import sys
from enum import Enum
from typing import Any, Literal

import structlog
from structlog.typing import EventDict, Processor


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log events."""
    event_dict["app"] = "deep-agent-agi"
    return event_dict


def setup_logging(
    log_level: LogLevel = LogLevel.INFO,
    log_format: Literal["json", "standard"] = "json",
) -> None:
    """
    Configure structured logging with structlog.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ('json' or 'standard')
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.value)

    # Clear existing handlers to prevent accumulation on reconfiguration
    logging.root.handlers.clear()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
    ]

    # Add format-specific processors
    if log_format == "json":
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])
    else:  # standard format
        processors.extend([
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ])

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure formatter for standard format
    if log_format == "standard":
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(numeric_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def generate_langsmith_url(
    trace_id: str,
    project: str = "deep-agent-agi",
    organization: str | None = None,
) -> str:
    """
    Generate LangSmith trace URL for debugging.

    Args:
        trace_id: LangSmith trace ID
        project: LangSmith project name (default: "deep-agent-agi")
        organization: Optional organization name for cloud-hosted LangSmith

    Returns:
        Full URL to LangSmith trace viewer

    Example:
        >>> url = generate_langsmith_url("abc-123-def")
        >>> print(url)
        https://smith.langchain.com/public/abc-123-def/r
    """
    if not trace_id:
        return ""

    # LangSmith public trace URL format (works without auth)
    # Format: https://smith.langchain.com/public/{trace_id}/r
    return f"https://smith.langchain.com/public/{trace_id}/r"
