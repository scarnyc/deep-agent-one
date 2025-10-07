"""
Unit tests for agent prompts module.

Tests prompt selection, environment-specific variants, and versioning.
"""

import pytest
from unittest.mock import Mock, patch

from backend.deep_agent.config.settings import Settings


class TestPromptConstants:
    """Test prompt constant definitions."""

    def test_deep_agent_system_prompt_exists(self) -> None:
        """Test that DEEP_AGENT_SYSTEM_PROMPT constant is defined."""
        from backend.deep_agent.agents.prompts import DEEP_AGENT_SYSTEM_PROMPT

        assert DEEP_AGENT_SYSTEM_PROMPT is not None
        assert isinstance(DEEP_AGENT_SYSTEM_PROMPT, str)
        assert len(DEEP_AGENT_SYSTEM_PROMPT) > 0

    def test_dev_instructions_exists(self) -> None:
        """Test that development instructions variant exists."""
        from backend.deep_agent.agents.prompts import DEEP_AGENT_INSTRUCTIONS_DEV

        assert DEEP_AGENT_INSTRUCTIONS_DEV is not None
        assert isinstance(DEEP_AGENT_INSTRUCTIONS_DEV, str)
        assert len(DEEP_AGENT_INSTRUCTIONS_DEV) > 0

    def test_prod_instructions_exists(self) -> None:
        """Test that production instructions variant exists."""
        from backend.deep_agent.agents.prompts import DEEP_AGENT_INSTRUCTIONS_PROD

        assert DEEP_AGENT_INSTRUCTIONS_PROD is not None
        assert isinstance(DEEP_AGENT_INSTRUCTIONS_PROD, str)
        assert len(DEEP_AGENT_INSTRUCTIONS_PROD) > 0

    def test_prompt_version_exists(self) -> None:
        """Test that prompt version is tracked."""
        from backend.deep_agent.agents.prompts import PROMPT_VERSION

        assert PROMPT_VERSION is not None
        assert isinstance(PROMPT_VERSION, str)
        # Version should follow semantic versioning (major.minor.patch)
        assert len(PROMPT_VERSION.split(".")) == 3


class TestPromptContent:
    """Test prompt content and key elements."""

    def test_system_prompt_mentions_deepagents(self) -> None:
        """Test that system prompt mentions DeepAgents framework."""
        from backend.deep_agent.agents.prompts import DEEP_AGENT_SYSTEM_PROMPT

        assert "deepagents" in DEEP_AGENT_SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_file_tools(self) -> None:
        """Test that system prompt describes file system tools."""
        from backend.deep_agent.agents.prompts import DEEP_AGENT_SYSTEM_PROMPT

        # Should mention key file tools
        assert "ls" in DEEP_AGENT_SYSTEM_PROMPT.lower()
        assert "read_file" in DEEP_AGENT_SYSTEM_PROMPT.lower()
        assert "write_file" in DEEP_AGENT_SYSTEM_PROMPT.lower()
        assert "edit_file" in DEEP_AGENT_SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_hitl(self) -> None:
        """Test that system prompt mentions HITL approval."""
        from backend.deep_agent.agents.prompts import DEEP_AGENT_SYSTEM_PROMPT

        # Should mention human approval or HITL
        prompt_lower = DEEP_AGENT_SYSTEM_PROMPT.lower()
        assert "approval" in prompt_lower or "hitl" in prompt_lower

    def test_dev_instructions_more_verbose_than_prod(self) -> None:
        """Test that dev instructions are more verbose/detailed than prod."""
        from backend.deep_agent.agents.prompts import (
            DEEP_AGENT_INSTRUCTIONS_DEV,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        )

        # Dev should have more explanatory content
        assert len(DEEP_AGENT_INSTRUCTIONS_DEV) >= len(DEEP_AGENT_INSTRUCTIONS_PROD)


class TestGetAgentInstructions:
    """Test get_agent_instructions function for environment-based selection."""

    def test_returns_dev_instructions_for_local_env(self) -> None:
        """Test function returns dev instructions for local environment."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_DEV,
        )

        instructions = get_agent_instructions(env="local")
        assert instructions == DEEP_AGENT_INSTRUCTIONS_DEV

    def test_returns_dev_instructions_for_dev_env(self) -> None:
        """Test function returns dev instructions for dev environment."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_DEV,
        )

        instructions = get_agent_instructions(env="dev")
        assert instructions == DEEP_AGENT_INSTRUCTIONS_DEV

    def test_returns_prod_instructions_for_prod_env(self) -> None:
        """Test function returns prod instructions for prod environment."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        )

        instructions = get_agent_instructions(env="prod")
        assert instructions == DEEP_AGENT_INSTRUCTIONS_PROD

    def test_returns_prod_instructions_for_staging_env(self) -> None:
        """Test function returns prod instructions for staging environment."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        )

        instructions = get_agent_instructions(env="staging")
        assert instructions == DEEP_AGENT_INSTRUCTIONS_PROD

    def test_defaults_to_dev_for_unknown_env(self) -> None:
        """Test function defaults to dev instructions for unknown environment."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_DEV,
        )

        instructions = get_agent_instructions(env="unknown")
        assert instructions == DEEP_AGENT_INSTRUCTIONS_DEV

    def test_case_insensitive_env_matching(self) -> None:
        """Test environment matching is case-insensitive."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        )

        # Should work with uppercase
        instructions_upper = get_agent_instructions(env="PROD")
        assert instructions_upper == DEEP_AGENT_INSTRUCTIONS_PROD

        # Should work with mixed case
        instructions_mixed = get_agent_instructions(env="PrOd")
        assert instructions_mixed == DEEP_AGENT_INSTRUCTIONS_PROD


class TestGetAgentInstructionsWithSettings:
    """Test get_agent_instructions with Settings integration."""

    def test_uses_settings_env_when_provided(self) -> None:
        """Test function uses ENV from Settings when no env parameter."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        )

        # Mock settings with prod ENV
        mock_settings = Mock(spec=Settings)
        mock_settings.ENV = "prod"

        instructions = get_agent_instructions(settings=mock_settings)
        assert instructions == DEEP_AGENT_INSTRUCTIONS_PROD

    def test_env_parameter_overrides_settings(self) -> None:
        """Test explicit env parameter overrides Settings.ENV."""
        from backend.deep_agent.agents.prompts import (
            get_agent_instructions,
            DEEP_AGENT_INSTRUCTIONS_DEV,
        )

        # Settings says prod, but we explicitly pass dev
        mock_settings = Mock(spec=Settings)
        mock_settings.ENV = "prod"

        instructions = get_agent_instructions(env="dev", settings=mock_settings)
        assert instructions == DEEP_AGENT_INSTRUCTIONS_DEV

    def test_falls_back_to_get_settings_when_no_args(self) -> None:
        """Test function calls get_settings() when no args provided."""
        from backend.deep_agent.agents.prompts import get_agent_instructions

        with patch("backend.deep_agent.agents.prompts.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.ENV = "prod"
            mock_get_settings.return_value = mock_settings

            instructions = get_agent_instructions()

            # Verify get_settings was called
            mock_get_settings.assert_called_once()
            assert instructions is not None


class TestPromptOpikCompatibility:
    """Test prompts are compatible with Opik auto-optimization."""

    def test_prompts_are_strings_not_templates(self) -> None:
        """Test prompts are plain strings (Opik-compatible)."""
        from backend.deep_agent.agents.prompts import (
            DEEP_AGENT_SYSTEM_PROMPT,
            DEEP_AGENT_INSTRUCTIONS_DEV,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        )

        # All prompts should be plain strings
        assert isinstance(DEEP_AGENT_SYSTEM_PROMPT, str)
        assert isinstance(DEEP_AGENT_INSTRUCTIONS_DEV, str)
        assert isinstance(DEEP_AGENT_INSTRUCTIONS_PROD, str)

        # Should not contain template variables (Opik will manage those)
        for prompt in [
            DEEP_AGENT_SYSTEM_PROMPT,
            DEEP_AGENT_INSTRUCTIONS_DEV,
            DEEP_AGENT_INSTRUCTIONS_PROD,
        ]:
            # No f-string remnants or template markers
            assert "{" not in prompt or "{{" in prompt  # Double braces OK (escaped)
            assert not prompt.startswith("f\"")
            assert not prompt.startswith("f'")

    def test_get_agent_instructions_returns_complete_prompt(self) -> None:
        """Test get_agent_instructions returns complete, ready-to-use prompt."""
        from backend.deep_agent.agents.prompts import get_agent_instructions

        instructions = get_agent_instructions(env="prod")

        # Should be non-empty and complete
        assert len(instructions) > 50  # Reasonable minimum length
        assert not instructions.strip().endswith("...")  # Not truncated
        assert instructions.strip()  # No leading/trailing whitespace issues
