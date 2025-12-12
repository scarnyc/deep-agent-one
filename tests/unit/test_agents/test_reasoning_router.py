"""Tests for reasoning router."""

import pytest

from backend.deep_agent.agents.reasoning_router import ReasoningRouter
from backend.deep_agent.models.llm import ReasoningEffort


class TestReasoningRouterPhase0:
    """Test Phase 0 reasoning router (always returns MEDIUM)."""

    @pytest.fixture
    def router(self) -> ReasoningRouter:
        """Create ReasoningRouter instance."""
        return ReasoningRouter()

    def test_simple_query(self, router: ReasoningRouter) -> None:
        """Test simple query returns MEDIUM."""
        effort = router.determine_effort("What is 2+2?")
        assert effort == ReasoningEffort.MEDIUM

    def test_complex_query(self, router: ReasoningRouter) -> None:
        """Test complex query returns MEDIUM (Phase 0 ignores complexity)."""
        query = "Analyze the philosophical implications of quantum mechanics on free will"
        effort = router.determine_effort(query)
        assert effort == ReasoningEffort.MEDIUM

    def test_trigger_phrases_ignored_phase_0(self, router: ReasoningRouter) -> None:
        """Test trigger phrases are ignored in Phase 0."""
        # These would trigger higher effort in Phase 1, but not in Phase 0
        queries = [
            "think harder about this problem",
            "deep dive into the architecture",
            "analyze carefully the implementation",
            "be thorough in your review",
        ]
        for query in queries:
            effort = router.determine_effort(query)
            assert effort == ReasoningEffort.MEDIUM

    def test_empty_query(self, router: ReasoningRouter) -> None:
        """Test empty query still returns MEDIUM."""
        effort = router.determine_effort("")
        assert effort == ReasoningEffort.MEDIUM

    def test_very_long_query(self, router: ReasoningRouter) -> None:
        """Test very long query returns MEDIUM (Phase 0 ignores length)."""
        long_query = "word " * 1000  # 1000 words
        effort = router.determine_effort(long_query)
        assert effort == ReasoningEffort.MEDIUM

    def test_multiple_calls_consistent(self, router: ReasoningRouter) -> None:
        """Test multiple calls with same query return consistent results."""
        query = "Explain how deepagents work"
        efforts = [router.determine_effort(query) for _ in range(5)]
        assert all(e == ReasoningEffort.MEDIUM for e in efforts)

    def test_different_queries_all_medium(self, router: ReasoningRouter) -> None:
        """Test various queries all return MEDIUM."""
        queries = [
            "Hello",
            "Write a function to check if a number is prime",
            "What's the weather?",
            "Explain quantum computing in simple terms",
            "Fix the bug in my code",
        ]
        for query in queries:
            effort = router.determine_effort(query)
            assert effort == ReasoningEffort.MEDIUM


class TestReasoningRouterPlaceholder:
    """Test that Phase 1 functionality is documented but not implemented."""

    @pytest.fixture
    def router(self) -> ReasoningRouter:
        """Create ReasoningRouter instance."""
        return ReasoningRouter()

    def test_has_trigger_phrases_attribute(self, router: ReasoningRouter) -> None:
        """Test router has trigger_phrases attribute for Phase 1."""
        # Should exist for future Phase 1 implementation
        assert hasattr(router, "trigger_phrases")
        assert isinstance(router.trigger_phrases, list)

    def test_has_complexity_threshold_attributes(self, router: ReasoningRouter) -> None:
        """Test router has complexity threshold attributes for Phase 1."""
        # Should exist for future Phase 1 implementation
        assert hasattr(router, "complexity_threshold_high")
        assert hasattr(router, "complexity_threshold_medium")


class TestReasoningRouterDocumentation:
    """Test that router is properly documented."""

    def test_class_has_docstring(self) -> None:
        """Test ReasoningRouter has docstring."""
        assert ReasoningRouter.__doc__ is not None
        assert "Phase 0" in ReasoningRouter.__doc__

    def test_determine_effort_has_docstring(self) -> None:
        """Test determine_effort method has docstring."""
        assert ReasoningRouter.determine_effort.__doc__ is not None
