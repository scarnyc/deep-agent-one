"""
Integration tests for LangSmith Fetch CLI tool.

Tests the langsmith-fetch CLI that provides terminal-based trace debugging.
Part of DA1-44: Integrate LangSmith Fetch CLI for terminal-based trace debugging.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


class TestLangSmithFetchCLIAvailability:
    """Test langsmith-fetch CLI is installed and accessible."""

    def test_langsmith_fetch_command_exists(self) -> None:
        """Test that langsmith-fetch command is available in PATH."""
        langsmith_fetch = shutil.which("langsmith-fetch")

        assert langsmith_fetch is not None, (
            "langsmith-fetch command not found in PATH. "
            "Ensure langsmith-fetch package is installed: pip install langsmith-fetch"
        )

    def test_langsmith_fetch_in_virtualenv(self) -> None:
        """Test langsmith-fetch is installed in the current virtual environment."""
        import sys

        langsmith_fetch = shutil.which("langsmith-fetch")

        if langsmith_fetch is not None:
            venv_path = sys.prefix
            assert venv_path in langsmith_fetch, (
                f"langsmith-fetch found at {langsmith_fetch}, but expected it in "
                f"virtual environment at {venv_path}"
            )

    def test_langsmith_fetch_version(self) -> None:
        """Test langsmith-fetch responds to --version flag."""
        result = subprocess.run(
            ["langsmith-fetch", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should either succeed or show help (some CLIs don't have --version)
        assert result.returncode == 0 or "usage" in result.stderr.lower(), (
            f"langsmith-fetch --version failed with return code {result.returncode}. "
            f"stdout: {result.stdout}, stderr: {result.stderr}"
        )

    def test_langsmith_fetch_help(self) -> None:
        """Test langsmith-fetch responds to --help flag."""
        result = subprocess.run(
            ["langsmith-fetch", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, (
            f"langsmith-fetch --help failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )
        assert "traces" in result.stdout.lower() or "usage" in result.stdout.lower(), (
            "langsmith-fetch --help output doesn't mention 'traces' or 'usage'. "
            f"Got: {result.stdout}"
        )


class TestFetchTracesHelperScript:
    """Test the fetch-traces.sh helper script."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Return path to fetch-traces.sh script."""
        return Path(__file__).parent.parent.parent / "scripts" / "fetch-traces.sh"

    def test_script_exists(self, script_path: Path) -> None:
        """Test that fetch-traces.sh script exists."""
        assert script_path.exists(), f"Script not found at {script_path}"

    def test_script_is_executable(self, script_path: Path) -> None:
        """Test that fetch-traces.sh script is executable."""
        assert os.access(script_path, os.X_OK), (
            f"Script at {script_path} is not executable. " "Run: chmod +x scripts/fetch-traces.sh"
        )

    def test_script_shows_help(self, script_path: Path) -> None:
        """Test that script shows help message."""
        result = subprocess.run(
            [str(script_path), "help"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode == 0, (
            f"Script help command failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )
        assert (
            "usage" in result.stdout.lower() or "commands" in result.stdout.lower()
        ), f"Script help output doesn't contain usage information. Got: {result.stdout}"

    def test_script_requires_api_key(self, script_path: Path) -> None:
        """Test that script fails gracefully without API key."""
        # Remove LANGSMITH_API_KEY from environment
        env = {k: v for k, v in os.environ.items() if k != "LANGSMITH_API_KEY"}

        result = subprocess.run(
            [str(script_path), "recent"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

        # Should fail with error about missing API key
        assert result.returncode != 0, "Script should fail without LANGSMITH_API_KEY"
        assert (
            "api" in result.stderr.lower() or "key" in result.stderr.lower()
        ), f"Error message should mention API key. Got: {result.stderr}"

    def test_script_handles_unknown_command(self, script_path: Path) -> None:
        """Test that script handles unknown commands gracefully."""
        result = subprocess.run(
            [str(script_path), "unknown-command"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should fail with unknown command"
        assert "unknown" in result.stderr.lower() or "usage" in result.stdout.lower(), (
            f"Error message should indicate unknown command. "
            f"stdout: {result.stdout}, stderr: {result.stderr}"
        )


class TestLangSmithFetchEnvironmentConfiguration:
    """Test LangSmith environment configuration."""

    def test_langsmith_api_key_in_env_example(self) -> None:
        """Test that LANGSMITH_API_KEY is documented in .env.example."""
        env_example = Path(__file__).parent.parent.parent / ".env.example"

        assert env_example.exists(), ".env.example file not found"

        content = env_example.read_text()
        assert "LANGSMITH_API_KEY" in content, (
            "LANGSMITH_API_KEY not found in .env.example. "
            "Users need this to configure LangSmith integration."
        )

    def test_langsmith_project_in_env_example(self) -> None:
        """Test that LANGSMITH_PROJECT is documented in .env.example."""
        env_example = Path(__file__).parent.parent.parent / ".env.example"

        assert env_example.exists(), ".env.example file not found"

        content = env_example.read_text()
        assert "LANGSMITH_PROJECT" in content, (
            "LANGSMITH_PROJECT not found in .env.example. "
            "Users need this to configure LangSmith project name."
        )


class TestFetchTracesEdgeCases:
    """Test edge cases and input validation for fetch-traces.sh."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Return path to fetch-traces.sh script."""
        return Path(__file__).parent.parent.parent / "scripts" / "fetch-traces.sh"

    def test_rejects_non_numeric_minutes(self, script_path: Path) -> None:
        """Test that script rejects non-numeric MINUTES parameter."""
        result = subprocess.run(
            [str(script_path), "last-n-minutes", "abc"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should reject non-numeric MINUTES"
        assert (
            "positive integer" in result.stderr.lower()
        ), f"Error should mention 'positive integer'. Got: {result.stderr}"

    def test_rejects_negative_minutes(self, script_path: Path) -> None:
        """Test that script rejects negative MINUTES parameter."""
        result = subprocess.run(
            [str(script_path), "last-n-minutes", "-5"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should reject negative MINUTES"

    def test_rejects_zero_minutes(self, script_path: Path) -> None:
        """Test that script rejects zero MINUTES parameter."""
        result = subprocess.run(
            [str(script_path), "last-n-minutes", "0"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should reject zero MINUTES"

    def test_rejects_non_numeric_limit(self, script_path: Path) -> None:
        """Test that script rejects non-numeric LIMIT parameter."""
        result = subprocess.run(
            [str(script_path), "export", "./test-dir", "invalid"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should reject non-numeric LIMIT"
        assert (
            "positive integer" in result.stderr.lower()
        ), f"Error should mention 'positive integer'. Got: {result.stderr}"

    def test_rejects_path_traversal(self, script_path: Path) -> None:
        """Test that script rejects paths with directory traversal."""
        result = subprocess.run(
            [str(script_path), "export", "../../../etc/passwd", "10"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should reject path traversal"
        assert ".." in result.stderr, f"Error should mention '..'. Got: {result.stderr}"

    def test_rejects_hidden_path_traversal(self, script_path: Path) -> None:
        """Test that script rejects hidden path traversal patterns."""
        result = subprocess.run(
            [str(script_path), "export", "./safe/../../../etc", "10"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        assert result.returncode != 0, "Script should reject hidden path traversal"

    def test_accepts_valid_minutes(self, script_path: Path) -> None:
        """Test that script accepts valid positive MINUTES."""
        # This will fail at the langsmith-fetch call (no real API),
        # but should pass validation
        result = subprocess.run(
            [str(script_path), "last-n-minutes", "30"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        # Should not fail on validation (may fail on actual API call)
        assert (
            "positive integer" not in result.stderr.lower()
        ), "Valid MINUTES should pass validation"

    def test_accepts_large_limit(self, script_path: Path) -> None:
        """Test that script accepts large but valid LIMIT values."""
        # This will fail at the langsmith-fetch call (no real API),
        # but should pass validation
        result = subprocess.run(
            [str(script_path), "export", "./test-export", "10000"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "LANGSMITH_API_KEY": "test-key"},  # pragma: allowlist secret
        )

        # Should not fail on validation (may fail on actual API call)
        assert "positive integer" not in result.stderr.lower(), "Large LIMIT should pass validation"


class TestLangSmithFetchResponseStructure:
    """Document expected LangSmith API response structures for reference."""

    def test_trace_response_structure(self) -> None:
        """Document expected trace response structure from LangSmith API."""
        # This test documents the expected structure without making real API calls
        expected_trace_structure: dict[str, Any] = {
            "runs": [
                {
                    "id": "test-run-id-123",
                    "name": "test_agent_run",
                    "run_type": "chain",
                    "status": "success",
                    "start_time": "2025-12-15T10:00:00Z",
                    "end_time": "2025-12-15T10:00:05Z",
                    "inputs": {"query": "What is 2+2?"},
                    "outputs": {"answer": "4"},
                    "error": None,
                }
            ],
            "cursors": {"next": None},
        }

        # Verify expected response structure for documentation
        assert "runs" in expected_trace_structure
        assert isinstance(expected_trace_structure["runs"], list)
        assert "id" in expected_trace_structure["runs"][0]
        assert "status" in expected_trace_structure["runs"][0]

    def test_thread_export_structure(self) -> None:
        """Document expected thread export structure for evaluation datasets."""
        expected_thread_structure: dict[str, Any] = {
            "thread_id": "thread-123",
            "runs": [
                {
                    "id": "run-1",
                    "inputs": {"user_message": "Hello"},
                    "outputs": {"assistant_message": "Hi there!"},
                },
            ],
            "metadata": {
                "created_at": "2025-12-15T10:00:00Z",
                "project": "deep-agent-one",
            },
        }

        # Verify expected export structure for documentation
        assert "thread_id" in expected_thread_structure
        assert "runs" in expected_thread_structure
        assert isinstance(expected_thread_structure["runs"], list)
        assert "metadata" in expected_thread_structure
