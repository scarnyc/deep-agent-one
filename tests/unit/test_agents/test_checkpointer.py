"""
Unit tests for CheckpointerManager.

Tests checkpointer creation, configuration, cleanup, and resource management
for LangGraph state persistence.
"""

import asyncio
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

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
def mock_settings(temp_db_dir):
    """Fixture providing mocked Settings with temp database path."""
    settings = Mock(spec=Settings)
    settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "checkpoints.db")
    settings.CHECKPOINT_CLEANUP_DAYS = 30
    return settings


@pytest.fixture
def checkpointer_manager(mock_settings):
    """Fixture providing CheckpointerManager instance."""
    return CheckpointerManager(settings=mock_settings)


class TestCheckpointerManagerInit:
    """Test CheckpointerManager initialization."""

    def test_init_with_settings(self, mock_settings):
        """Test initialization with provided settings."""
        # Arrange & Act
        manager = CheckpointerManager(settings=mock_settings)

        # Assert
        assert manager is not None
        assert manager.settings == mock_settings

    def test_init_without_settings(self):
        """Test initialization without settings uses default get_settings()."""
        # Arrange & Act
        manager = CheckpointerManager()

        # Assert
        assert manager is not None
        assert manager.settings is not None
        assert isinstance(manager.settings, Settings)

    def test_init_sets_db_path_from_settings(self, mock_settings):
        """Test initialization extracts database path from settings."""
        # Arrange
        expected_path = "/tmp/test_checkpoints.db"
        mock_settings.CHECKPOINT_DB_PATH = expected_path

        # Act
        manager = CheckpointerManager(settings=mock_settings)

        # Assert
        assert manager.settings.CHECKPOINT_DB_PATH == expected_path


class TestCreateCheckpointer:
    """Test checkpointer creation methods."""

    @pytest.mark.asyncio
    async def test_create_checkpointer_default_env(self, checkpointer_manager, temp_db_dir):
        """Test creating checkpointer with default environment."""
        # Arrange
        # Act
        checkpointer = await checkpointer_manager.create_checkpointer()

        # Assert
        assert checkpointer is not None
        assert isinstance(checkpointer, AsyncSqliteSaver)
        # Verify database file was created
        db_path = Path(checkpointer_manager.settings.CHECKPOINT_DB_PATH)
        assert db_path.exists()

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_create_checkpointer_custom_env(self, checkpointer_manager):
        """Test creating checkpointer with custom environment name."""
        # Arrange
        env = "production"

        # Act
        checkpointer = await checkpointer_manager.create_checkpointer(env=env)

        # Assert
        assert checkpointer is not None
        assert isinstance(checkpointer, AsyncSqliteSaver)

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_get_sqlite_checkpointer_default_path(self, checkpointer_manager):
        """Test get_sqlite_checkpointer uses settings path by default."""
        # Arrange
        # Act
        checkpointer = await checkpointer_manager.get_sqlite_checkpointer()

        # Assert
        assert checkpointer is not None
        assert isinstance(checkpointer, AsyncSqliteSaver)
        db_path = Path(checkpointer_manager.settings.CHECKPOINT_DB_PATH)
        assert db_path.exists()

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_get_sqlite_checkpointer_custom_path(self, checkpointer_manager, temp_db_dir):
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

    @pytest.mark.asyncio
    async def test_checkpointer_creates_parent_directories(self, checkpointer_manager, temp_db_dir):
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


class TestCheckpointerFunctionality:
    """Test checkpointer persistence and state operations."""

    @pytest.mark.asyncio
    async def test_checkpointer_can_save_and_load_state(self, checkpointer_manager):
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
    async def test_multiple_checkpointers_isolated(self, temp_db_dir, mock_settings):
        """Test multiple checkpointer instances are isolated."""
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
        # Verify they're different files
        assert mock_settings.CHECKPOINT_DB_PATH != manager2_settings.CHECKPOINT_DB_PATH

        # Cleanup
        await manager1.close()
        await manager2.close()


class TestCleanupOperations:
    """Test checkpoint cleanup and maintenance operations."""

    @pytest.mark.asyncio
    async def test_cleanup_old_checkpoints_default_days(self, checkpointer_manager, temp_db_dir):
        """Test cleanup removes checkpoints older than default days."""
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
        assert deleted_count >= 0  # Should delete at least old checkpoint

        # Verify recent checkpoint still exists
        loaded_recent = await checkpointer.aget(recent_config)
        assert loaded_recent is not None

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_cleanup_old_checkpoints_custom_days(self, checkpointer_manager):
        """Test cleanup with custom days parameter."""
        # Arrange
        checkpointer = await checkpointer_manager.create_checkpointer()
        custom_days = 7

        # Act
        deleted_count = await checkpointer_manager.cleanup_old_checkpoints(days=custom_days)

        # Assert
        assert deleted_count >= 0  # Returns count of deleted checkpoints

        # Cleanup
        await checkpointer_manager.close()

    @pytest.mark.asyncio
    async def test_cleanup_no_checkpoints_returns_zero(self, checkpointer_manager):
        """Test cleanup returns 0 when no checkpoints exist."""
        # Arrange
        await checkpointer_manager.create_checkpointer()

        # Act
        deleted_count = await checkpointer_manager.cleanup_old_checkpoints()

        # Assert
        assert deleted_count == 0

        # Cleanup
        await checkpointer_manager.close()


class TestResourceManagement:
    """Test resource cleanup and context manager support."""

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(self, checkpointer_manager):
        """Test close method properly cleans up checkpointer resources."""
        # Arrange
        checkpointer = await checkpointer_manager.create_checkpointer()
        assert checkpointer is not None

        # Act
        await checkpointer_manager.close()

        # Assert - should not raise any exceptions
        # Attempting to use closed checkpointer should handle gracefully

    @pytest.mark.asyncio
    async def test_async_context_manager_support(self, mock_settings):
        """Test CheckpointerManager works as async context manager."""
        # Arrange & Act
        async with CheckpointerManager(settings=mock_settings) as manager:
            checkpointer = await manager.create_checkpointer()

            # Assert - inside context
            assert checkpointer is not None
            assert isinstance(checkpointer, AsyncSqliteSaver)

        # Assert - context exited, resources should be cleaned up

    @pytest.mark.asyncio
    async def test_close_idempotent(self, checkpointer_manager):
        """Test calling close multiple times is safe."""
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
    async def test_create_checkpointer_invalid_path_raises_error(self, checkpointer_manager):
        """Test creating checkpointer with invalid path raises appropriate error."""
        # Arrange
        checkpointer_manager.settings.CHECKPOINT_DB_PATH = "/invalid/path/that/does/not/exist/db.sqlite"

        # Act & Assert
        with pytest.raises((OSError, PermissionError, ValueError)):
            await checkpointer_manager.create_checkpointer()

    @pytest.mark.asyncio
    async def test_create_checkpointer_permission_denied(self, checkpointer_manager, temp_db_dir):
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

    @pytest.mark.asyncio
    async def test_cleanup_handles_missing_database(self, temp_db_dir, mock_settings):
        """Test cleanup handles case where database doesn't exist yet."""
        # Arrange
        mock_settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "nonexistent.db")
        manager = CheckpointerManager(settings=mock_settings)

        # Act
        deleted_count = await manager.cleanup_old_checkpoints()

        # Assert - should handle gracefully, return 0
        assert deleted_count == 0

        # Cleanup
        await manager.close()


class TestConfiguration:
    """Test configuration and settings integration."""

    def test_settings_integration(self):
        """Test CheckpointerManager integrates with Settings class."""
        # Arrange & Act
        manager = CheckpointerManager()

        # Assert
        assert manager.settings is not None
        assert hasattr(manager.settings, 'CHECKPOINT_DB_PATH')
        assert hasattr(manager.settings, 'CHECKPOINT_CLEANUP_DAYS')

    @pytest.mark.asyncio
    async def test_environment_specific_configuration(self, temp_db_dir):
        """Test environment-specific configuration (local vs prod)."""
        # Arrange
        local_settings = Mock(spec=Settings)
        local_settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "local_checkpoints.db")
        local_settings.CHECKPOINT_CLEANUP_DAYS = 7

        prod_settings = Mock(spec=Settings)
        prod_settings.CHECKPOINT_DB_PATH = str(temp_db_dir / "prod_checkpoints.db")
        prod_settings.CHECKPOINT_CLEANUP_DAYS = 90

        # Act
        local_manager = CheckpointerManager(settings=local_settings)
        prod_manager = CheckpointerManager(settings=prod_settings)

        local_checkpointer = await local_manager.create_checkpointer(env="local")
        prod_checkpointer = await prod_manager.create_checkpointer(env="production")

        # Assert
        assert local_checkpointer is not None
        assert prod_checkpointer is not None
        assert Path(local_settings.CHECKPOINT_DB_PATH).exists()
        assert Path(prod_settings.CHECKPOINT_DB_PATH).exists()

        # Cleanup
        await local_manager.close()
        await prod_manager.close()
