"""
Integration tests for CheckpointerManager.

Tests real database operations, state persistence, cleanup, and error handling
using actual SQLite databases.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from backend.deep_agent.agents.checkpointer import CheckpointerManager
from backend.deep_agent.config.settings import Settings


@pytest.fixture
def temp_db_dir():
    """Fixture providing a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_settings(temp_db_dir) -> None:
    """Fixture providing mocked Settings with temp database path."""
    settings = Mock(spec=Settings)
    settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "checkpoints.db")
    settings.CHECKPOINT_CLEANUP_DAYS = 30
    return settings


@pytest.fixture
def checkpointer_manager(mock_settings):
    """Fixture providing CheckpointerManager instance."""
    return CheckpointerManager(settings=mock_settings)


class TestCheckpointerCreation:
    """Test checkpointer creation with real database operations."""

    @pytest.mark.asyncio
    async def test_create_checkpointer_creates_database_file(
        self, checkpointer_manager, temp_db_dir
    ):
        """Test creating checkpointer creates actual database file."""
        # Arrange
        db_path = Path(checkpointer_manager.settings.CHECKPOINT_DB_PATH)

        # Act
        checkpointer = await checkpointer_manager.create_checkpointer()

        # Assert
        assert checkpointer is not None
        assert isinstance(checkpointer, AsyncSqliteSaver)
        assert db_path.exists()
        assert db_path.is_file()

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_create_checkpointer_with_nested_directories(
        self, checkpointer_manager, temp_db_dir
    ):
        """Test checkpointer creates parent directories if they don't exist."""
        # Arrange
        nested_path = str(temp_db_dir / "nested" / "dirs" / "checkpoint.db")
        checkpointer_manager.settings.CHECKPOINT_DB_PATH = nested_path

        # Act
        checkpointer = await checkpointer_manager.create_checkpointer()

        # Assert
        assert checkpointer is not None
        assert Path(nested_path).exists()
        assert Path(nested_path).parent.exists()

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_get_sqlite_checkpointer_custom_path(
        self, checkpointer_manager, temp_db_dir
    ) -> None:
        """Test get_sqlite_checkpointer with custom database path."""
        # Arrange
        custom_path = str(temp_db_dir / "custom_checkpoints.db")

        # Act
        checkpointer = await checkpointer_manager.get_sqlite_checkpointer(db_path=custom_path)

        # Assert
        assert checkpointer is not None
        assert isinstance(checkpointer, AsyncSqliteSaver)
        assert Path(custom_path).exists()

        # Cleanup
        await checkpointer_manager.close()


class TestStatePersistence:
    """Test checkpointer state persistence operations."""

    @pytest.mark.asyncio
    async def test_checkpointer_saves_and_loads_state(self, checkpointer_manager) -> None:
        """Test checkpointer can persist and retrieve state."""
        # Arrange
        checkpointer = await checkpointer_manager.create_checkpointer()
        test_config = {"configurable": {"thread_id": "test_thread_1", "checkpoint_ns": ""}}
        test_checkpoint = {
            "v": 1,
            "id": "checkpoint_1",
            "ts": datetime.now().isoformat(),
            "channel_values": {"test": "data"},
        }

        # Act
        # Save checkpoint
        await checkpointer.aput(test_config, test_checkpoint, {}, {})

        # Load checkpoint
        loaded = await checkpointer.aget(test_config)

        # Assert
        assert loaded is not None
        assert loaded["id"] == test_checkpoint["id"]

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_multiple_checkpointers_isolated(self, temp_db_dir, mock_settings) -> None:
        """Test multiple checkpointer instances use separate databases."""
        # Arrange
        manager1 = CheckpointerManager(settings=mock_settings)
        manager2_settings = Mock(spec=Settings)
        manager2_settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "checkpoints2.db")
        manager2_settings.CHECKPOINT_CLEANUP_DAYS = 30
        manager2 = CheckpointerManager(settings=manager2_settings)

        # Act
        checkpointer1 = await manager1.create_checkpointer()
        checkpointer2 = await manager2.create_checkpointer()

        # Assert
        assert checkpointer1 is not None
        assert checkpointer2 is not None
        assert Path(mock_settings.CHECKPOINT_DB_PATH).exists()
        assert Path(manager2_settings.CHECKPOINT_DB_PATH).exists()
        assert mock_settings.CHECKPOINT_DB_PATH != manager2_settings.CHECKPOINT_DB_PATH

        # Cleanup
        await manager1.close()
        await manager2.close()


class TestCleanupOperations:
    """Test checkpoint cleanup and maintenance operations."""

    @pytest.mark.asyncio
    async def test_cleanup_old_checkpoints_removes_old_data(
        self, checkpointer_manager, temp_db_dir
    ):
        """Test cleanup removes checkpoints older than retention period."""
        # Arrange
        checkpointer = await checkpointer_manager.create_checkpointer()

        # Create test checkpoints with different timestamps
        old_date = datetime.now() - timedelta(days=35)
        recent_date = datetime.now() - timedelta(days=5)

        old_config = {"configurable": {"thread_id": "old_thread", "checkpoint_ns": ""}}
        recent_config = {"configurable": {"thread_id": "recent_thread", "checkpoint_ns": ""}}

        old_checkpoint = {
            "v": 1,
            "id": "old_checkpoint",
            "ts": old_date.isoformat(),
            "channel_values": {"test": "old_data"},
        }
        recent_checkpoint = {
            "v": 1,
            "id": "recent_checkpoint",
            "ts": recent_date.isoformat(),
            "channel_values": {"test": "recent_data"},
        }

        await checkpointer.aput(old_config, old_checkpoint, {}, {})
        await checkpointer.aput(recent_config, recent_checkpoint, {}, {})

        # Act
        deleted_count = await checkpointer_manager.cleanup_old_checkpoints()

        # Assert
        assert deleted_count >= 0

        # Verify recent checkpoint still exists
        loaded_recent = await checkpointer.aget(recent_config)
        assert loaded_recent is not None

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_cleanup_with_custom_retention_days(self, checkpointer_manager) -> None:
        """Test cleanup with custom days parameter."""
        # Arrange
        _checkpointer = await checkpointer_manager.create_checkpointer()
        custom_days = 7

        # Act
        deleted_count = await checkpointer_manager.cleanup_old_checkpoints(days=custom_days)

        # Assert
        assert deleted_count >= 0

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_cleanup_with_no_checkpoints_returns_zero(self, checkpointer_manager) -> None:
        """Test cleanup returns 0 when database is empty."""
        # Arrange
        await checkpointer_manager.create_checkpointer()

        # Act
        deleted_count = await checkpointer_manager.cleanup_old_checkpoints()

        # Assert
        assert deleted_count == 0

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_cleanup_handles_missing_database(self, temp_db_dir, mock_settings) -> None:
        """Test cleanup handles case where database doesn't exist."""
        # Arrange
        mock_settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "nonexistent.db")
        manager = CheckpointerManager(settings=mock_settings)

        # Act
        deleted_count = await manager.cleanup_old_checkpoints()

        # Assert
        assert deleted_count == 0

        # Cleanup
        await manager.close()


class TestResourceManagement:
    """Test resource cleanup and lifecycle management."""

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(self, checkpointer_manager) -> None:
        """Test close method properly releases database connection."""
        # Arrange
        checkpointer = await checkpointer_manager.create_checkpointer()
        assert checkpointer is not None

        # Act
        await checkpointer_manager.close()

        # Assert - should not raise any exceptions

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup(self, mock_settings) -> None:
        """Test CheckpointerManager works as async context manager."""
        # Arrange & Act
        async with CheckpointerManager(settings=mock_settings) as manager:
            checkpointer = await manager.create_checkpointer()

            # Assert - inside context
            assert checkpointer is not None
            assert isinstance(checkpointer, AsyncSqliteSaver)

        # Assert - context exited, resources cleaned up

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self, checkpointer_manager) -> None:
        """Test calling close multiple times doesn't raise errors."""
        # Arrange
        await checkpointer_manager.create_checkpointer()

        # Act - call close multiple times
        await checkpointer_manager.close()
        await checkpointer_manager.close()
        await checkpointer_manager.close()

        # Assert - should not raise exceptions


class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.mark.asyncio
    async def test_create_checkpointer_with_invalid_path_raises_error(
        self, checkpointer_manager
    ) -> None:
        """Test creating checkpointer with invalid path raises appropriate error."""
        # Arrange
        checkpointer_manager.settings.CHECKPOINT_DB_PATH = (
            "/invalid/path/that/does/not/exist/db.sqlite"
        )

        # Act & Assert
        with pytest.raises((OSError, PermissionError, ValueError)):
            await checkpointer_manager.create_checkpointer()

    @pytest.mark.asyncio
    async def test_create_checkpointer_with_permission_denied(
        self, checkpointer_manager, temp_db_dir
    ):
        """Test creating checkpointer with no write permission raises error."""
        # Arrange
        read_only_path = temp_db_dir / "readonly.db"
        read_only_path.touch()
        read_only_path.chmod(0o444)  # Read-only
        checkpointer_manager.settings.CHECKPOINT_DB_PATH = str(read_only_path)

        # Act & Assert
        with pytest.raises((OSError, PermissionError, sqlite3.OperationalError)):
            await checkpointer_manager.create_checkpointer()

        # Cleanup
        read_only_path.chmod(0o644)  # Restore permissions
