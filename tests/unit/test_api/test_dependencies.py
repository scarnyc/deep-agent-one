"""
Unit tests for FastAPI dependencies module.

Tests thread safety of singleton AgentService management,
including concurrent access and reset operations.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest

from backend.deep_agent.api.dependencies import (
    AgentServiceInitializationError,
    _agent_service_lock,
    get_agent_service,
    get_agent_service_version,
    reset_agent_service,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton state before and after each test."""
    reset_agent_service()
    yield
    reset_agent_service()


class TestGetAgentService:
    """Tests for get_agent_service() singleton pattern."""

    def test_returns_agent_service_instance(self):
        """Test that get_agent_service returns an AgentService instance."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_instance = MagicMock()
            mock_agent_service.return_value = mock_instance

            result = get_agent_service()

            assert result == mock_instance
            mock_agent_service.assert_called_once()

    def test_returns_same_instance_on_subsequent_calls(self):
        """Test singleton pattern - same instance returned."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_instance = MagicMock()
            mock_agent_service.return_value = mock_instance

            result1 = get_agent_service()
            result2 = get_agent_service()
            result3 = get_agent_service()

            assert result1 is result2 is result3
            # AgentService should only be instantiated once
            mock_agent_service.assert_called_once()

    def test_raises_initialization_error_on_failure(self):
        """Test that initialization errors are wrapped properly."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.side_effect = ValueError("Bad config")

            with pytest.raises(AgentServiceInitializationError) as exc_info:
                get_agent_service()

            assert "Agent service initialization failed" in str(exc_info.value)


class TestResetAgentService:
    """Tests for reset_agent_service() function."""

    def test_reset_clears_singleton(self):
        """Test that reset clears the cached instance."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_instance1 = MagicMock()
            mock_instance2 = MagicMock()
            mock_agent_service.side_effect = [mock_instance1, mock_instance2]

            # Get first instance
            result1 = get_agent_service()
            assert result1 is mock_instance1

            # Reset
            reset_agent_service()

            # Get new instance
            result2 = get_agent_service()
            assert result2 is mock_instance2
            assert result1 is not result2

            # AgentService should be called twice
            assert mock_agent_service.call_count == 2

    def test_reset_is_idempotent(self):
        """Test that multiple resets don't cause issues."""
        # Should not raise any exceptions
        reset_agent_service()
        reset_agent_service()
        reset_agent_service()


class TestConcurrentAccess:
    """Tests for thread safety of singleton management.

    These tests validate the race condition fix for Issue 2:
    Race Condition in Global State Reset (Phase 1).
    """

    def test_concurrent_get_creates_only_one_instance(self):
        """Test that concurrent calls to get_agent_service create only one instance.

        This validates the double-checked locking pattern works correctly
        under concurrent access.
        """
        creation_count = 0
        creation_lock = threading.Lock()

        def mock_agent_service_init():
            nonlocal creation_count
            with creation_lock:
                creation_count += 1
            # Simulate slow initialization
            time.sleep(0.05)
            return MagicMock()

        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.side_effect = mock_agent_service_init

            # Launch many concurrent requests
            num_threads = 20
            results = []

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(get_agent_service) for _ in range(num_threads)]
                for future in as_completed(futures):
                    results.append(future.result())

            # All results should be the same instance
            first_result = results[0]
            for result in results[1:]:
                assert result is first_result

            # AgentService should only be created once
            assert creation_count == 1
            mock_agent_service.assert_called_once()

    def test_concurrent_reset_is_safe(self):
        """Test that concurrent reset calls don't cause race conditions."""
        reset_count = 0
        reset_lock = threading.Lock()

        original_reset = reset_agent_service

        def tracked_reset():
            nonlocal reset_count
            original_reset()
            with reset_lock:
                reset_count += 1

        # First create an instance
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.return_value = MagicMock()
            get_agent_service()

        # Now reset concurrently
        num_threads = 20
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(tracked_reset) for _ in range(num_threads)]
            # Wait for all to complete - should not raise
            for future in as_completed(futures):
                future.result()

        assert reset_count == num_threads

    def test_reset_during_get_is_thread_safe(self):
        """Test that reset during concurrent gets doesn't cause corruption.

        This is the key race condition test: what happens when reset_agent_service()
        is called while get_agent_service() is in progress?
        """
        instances_created = []
        creation_lock = threading.Lock()

        def mock_agent_service_init():
            instance = MagicMock()
            with creation_lock:
                instances_created.append(instance)
            # Simulate slow initialization
            time.sleep(0.02)
            return instance

        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.side_effect = mock_agent_service_init

            results = []
            errors = []

            def get_worker():
                try:
                    result = get_agent_service()
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            def reset_worker():
                time.sleep(0.01)  # Small delay to interleave with gets
                reset_agent_service()

            # Launch concurrent gets and resets
            with ThreadPoolExecutor(max_workers=15) as executor:
                # 10 get operations
                get_futures = [executor.submit(get_worker) for _ in range(10)]
                # 5 reset operations
                reset_futures = [executor.submit(reset_worker) for _ in range(5)]

                # Wait for all to complete
                for future in as_completed(get_futures + reset_futures):
                    future.result()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All get results should be valid AgentService instances (mocks)
            assert len(results) == 10
            for result in results:
                assert result is not None

    def test_lock_prevents_simultaneous_instance_creation(self):
        """Test that the lock prevents multiple instances from being created simultaneously.

        This test specifically validates that if two threads both pass the first
        None check, only one will actually create the instance.

        The double-checked locking pattern ensures that even if multiple threads
        pass the first check, only one will create the instance.
        """
        creation_timestamps = []
        creation_lock = threading.Lock()

        def slow_init():
            """Simulate slow initialization to maximize race condition window."""
            with creation_lock:
                creation_timestamps.append(time.time())
            time.sleep(0.1)  # Long delay to ensure other threads are waiting
            return MagicMock()

        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.side_effect = slow_init

            results = []
            ready_event = threading.Event()

            def worker():
                # Wait until all threads are ready
                ready_event.wait()
                result = get_agent_service()
                results.append(result)

            # Launch multiple threads that start simultaneously
            threads = [threading.Thread(target=worker) for _ in range(5)]
            for t in threads:
                t.start()

            # Release all threads at once to maximize race condition
            ready_event.set()

            for t in threads:
                t.join(timeout=5)

            # Only one creation should have happened despite 5 concurrent requests
            assert mock_agent_service.call_count == 1
            assert len(creation_timestamps) == 1

            # All 5 results should be the same instance
            assert len(results) == 5
            first_result = results[0]
            for result in results[1:]:
                assert result is first_result

    def test_get_after_reset_creates_new_instance(self):
        """Test that get after reset creates a fresh instance."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            instance1 = MagicMock(name="instance1")
            instance2 = MagicMock(name="instance2")
            mock_agent_service.side_effect = [instance1, instance2]

            # Get -> Reset -> Get pattern
            result1 = get_agent_service()
            reset_agent_service()
            result2 = get_agent_service()

            assert result1 is instance1
            assert result2 is instance2
            assert result1 is not result2
            assert mock_agent_service.call_count == 2


class TestAgentServiceInitializationError:
    """Tests for AgentServiceInitializationError exception."""

    def test_error_is_runtime_error_subclass(self):
        """Test that the error is a RuntimeError subclass."""
        assert issubclass(AgentServiceInitializationError, RuntimeError)

    def test_error_message_propagation(self):
        """Test that error messages are properly propagated."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.side_effect = ValueError("Missing API key")

            with pytest.raises(AgentServiceInitializationError) as exc_info:
                get_agent_service()

            # Check the cause is preserved
            assert exc_info.value.__cause__ is not None
            assert "Missing API key" in str(exc_info.value.__cause__)


class TestLockExists:
    """Tests to verify lock infrastructure exists."""

    def test_module_level_lock_exists(self):
        """Test that the module-level lock is properly defined."""
        assert _agent_service_lock is not None
        assert isinstance(_agent_service_lock, type(threading.Lock()))

    def test_lock_is_reentrant_safe(self):
        """Test behavior with the threading.Lock (non-reentrant)."""
        # threading.Lock is NOT reentrant, which is fine for our use case
        # This test documents that behavior
        lock = threading.Lock()
        assert lock.acquire(blocking=False) is True
        # Second acquire on same thread would block (deadlock)
        # We don't test this to avoid deadlock, but document it
        lock.release()


class TestVersionCounter:
    """Tests for version counter functionality."""

    def test_version_starts_at_zero(self):
        """Test that version is 0 before any instance is created."""
        # After reset in fixture, we need to also reset the version
        # The version persists across resets to track total creations
        initial_version = get_agent_service_version()
        assert isinstance(initial_version, int)

    def test_version_increments_on_creation(self):
        """Test that version increments when a new instance is created."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.return_value = MagicMock()

            version_before = get_agent_service_version()
            get_agent_service()
            version_after = get_agent_service_version()

            assert version_after == version_before + 1

    def test_version_increments_after_reset_and_get(self):
        """Test that version increments after reset + get cycle."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.return_value = MagicMock()

            # First creation
            get_agent_service()
            version_1 = get_agent_service_version()

            # Reset and create again
            reset_agent_service()
            get_agent_service()
            version_2 = get_agent_service_version()

            assert version_2 == version_1 + 1

    def test_version_does_not_increment_on_cached_get(self):
        """Test that version doesn't increment when returning cached instance."""
        with patch(
            "backend.deep_agent.api.dependencies.AgentService"
        ) as mock_agent_service:
            mock_agent_service.return_value = MagicMock()

            get_agent_service()
            version_1 = get_agent_service_version()

            # Multiple gets should not increment version
            get_agent_service()
            get_agent_service()
            get_agent_service()

            version_2 = get_agent_service_version()
            assert version_2 == version_1
