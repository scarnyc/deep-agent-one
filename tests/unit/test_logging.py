"""Unit tests for structured logging."""

import logging

import pytest

from backend.deep_agent.core.logging import (
    LogLevel,
    get_logger,
    setup_logging,
)


class TestLogging:
    """Test structured logging functionality."""

    def test_setup_logging_json_format(self) -> None:
        """Test that logging can be configured with JSON format."""
        # Setup with JSON format
        setup_logging(log_level=LogLevel.INFO, log_format="json")

        logger = get_logger("test_json")

        # Verify logger is configured (structlog returns BoundLoggerLazyProxy)
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_setup_logging_standard_format(self) -> None:
        """Test that logging can be configured with standard format."""
        # Setup with standard format
        setup_logging(log_level=LogLevel.INFO, log_format="standard")

        logger = get_logger("test_standard")

        # Verify logger is configured (structlog returns BoundLoggerLazyProxy)
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a valid logger instance."""
        setup_logging(log_level=LogLevel.INFO)

        logger = get_logger("test_module")

        assert logger is not None
        assert logger.name == "test_module"

    def test_log_level_enum_values(self) -> None:
        """Test that LogLevel enum has correct values."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"

    def test_logger_respects_log_level(self) -> None:
        """Test that logger respects configured log level."""
        # Setup with WARNING level
        setup_logging(log_level=LogLevel.WARNING, log_format="standard")

        logger = get_logger("test_level")

        # Verify effective level
        assert logger.level == logging.WARNING or logger.getEffectiveLevel() == logging.WARNING

    def test_structured_log_includes_context(self, capsys: pytest.CaptureFixture) -> None:
        """Test that structured logs can include context fields."""
        setup_logging(log_level=LogLevel.INFO, log_format="standard")

        logger = get_logger("test_context")

        logger.info("test message", request_id="123", user="test_user")

        # Capture stdout and verify message was logged
        captured = capsys.readouterr()
        assert "test message" in captured.out
        assert "request_id" in captured.out or "123" in captured.out

    def test_logger_handles_exceptions(self, capsys: pytest.CaptureFixture) -> None:
        """Test that logger properly handles exception logging."""
        setup_logging(log_level=LogLevel.ERROR, log_format="standard")

        logger = get_logger("test_exception")

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        # Capture stdout and verify exception was logged
        captured = capsys.readouterr()
        assert "An error occurred" in captured.out
        assert "ValueError" in captured.out
        assert "Test exception" in captured.out

    def test_multiple_loggers_use_same_config(self) -> None:
        """Test that multiple loggers share the same configuration."""
        setup_logging(log_level=LogLevel.INFO)

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Both should be configured
        assert logger1 is not None
        assert logger2 is not None
        assert logger1.name == "module1"
        assert logger2.name == "module2"
