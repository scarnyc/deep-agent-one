"""Checkpointer manager for LangGraph state persistence."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiosqlite

from deep_agent.config.settings import Settings, get_settings

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def _lazy_import_checkpointer():
    """Lazy import of AsyncSqliteSaver to avoid blocking at module load time."""
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    return AsyncSqliteSaver
from deep_agent.core.logging import get_logger

logger = get_logger(__name__)


class CheckpointerManager:
    """
    Manages LangGraph checkpointers for agent state persistence.

    This class handles creation and management of AsyncSqliteSaver checkpointers
    for Phase 0 (local/dev), with support for PostgreSQL checkpointers in Phase 1+.

    Key Features:
        - Environment-specific checkpointer configuration
        - Automatic database file and directory creation
        - Cleanup utilities for old checkpoints
        - Async context manager support for resource cleanup
        - Thread-safe state persistence

    Example:
        >>> async with CheckpointerManager() as manager:
        ...     checkpointer = await manager.create_checkpointer()
        ...     # Use checkpointer with agent
        ...     agent = create_deep_agent(...)
        ...     graph = agent.compile(checkpointer=checkpointer)
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize CheckpointerManager with configuration.

        Args:
            settings: Settings instance with checkpointer configuration.
                     If None, uses get_settings() default singleton.
        """
        self.settings = settings if settings is not None else get_settings()
        self._checkpointer: Any = None  # AsyncSqliteSaver but using Any to avoid import
        self._connection: aiosqlite.Connection | None = None

        logger.info(
            "CheckpointerManager initialized",
            db_path=self.settings.CHECKPOINT_DB_PATH,
            cleanup_days=self.settings.CHECKPOINT_CLEANUP_DAYS,
        )

    async def create_checkpointer(self, env: str = "local") -> Any:  # Returns AsyncSqliteSaver
        """
        Create a checkpointer for the specified environment.

        Phase 0: Returns AsyncSqliteSaver for all environments
        Phase 1+: Will return PostgresSaver for production environments

        Args:
            env: Environment name (local, dev, staging, prod)

        Returns:
            Configured AsyncSqliteSaver instance

        Raises:
            OSError: If database path is invalid or inaccessible
            PermissionError: If insufficient permissions to create database

        Example:
            >>> manager = CheckpointerManager()
            >>> checkpointer = await manager.create_checkpointer(env="local")
        """
        logger.debug(f"Creating checkpointer for environment: {env}")

        # Phase 0: Always use SQLite
        # Phase 1: Add logic to return PostgresSaver for production
        return await self.get_sqlite_checkpointer()

    async def get_sqlite_checkpointer(
        self, db_path: str | None = None
    ) -> Any:  # Returns AsyncSqliteSaver
        """
        Create an AsyncSqliteSaver checkpointer with specified database path.

        Args:
            db_path: Path to SQLite database file. If None, uses settings path.

        Returns:
            Configured AsyncSqliteSaver instance

        Raises:
            OSError: If database path is invalid or inaccessible
            PermissionError: If insufficient permissions to create database

        Example:
            >>> manager = CheckpointerManager()
            >>> checkpointer = await manager.get_sqlite_checkpointer()
            >>> # Or with custom path:
            >>> checkpointer = await manager.get_sqlite_checkpointer("/tmp/custom.db")
        """
        # Use provided path or default from settings
        resolved_path = db_path if db_path is not None else self.settings.CHECKPOINT_DB_PATH

        # Ensure parent directories exist
        db_file = Path(resolved_path)
        try:
            db_file.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured parent directory exists: {db_file.parent}")
        except (OSError, PermissionError) as e:
            logger.error(
                "Failed to create parent directory",
                path=str(db_file.parent),
                error=str(e),
            )
            raise

        # Create checkpointer using AsyncSqliteSaver
        try:
            # Create aiosqlite connection
            conn = await aiosqlite.connect(str(resolved_path))
            self._connection = conn

            # Lazy import to avoid blocking at module load time
            AsyncSqliteSaver = _lazy_import_checkpointer()

            # Create AsyncSqliteSaver with the connection
            checkpointer = AsyncSqliteSaver(conn)
            self._checkpointer = checkpointer

            # Setup database schema
            await checkpointer.setup()

            logger.info(
                "Created AsyncSqliteSaver checkpointer",
                db_path=resolved_path,
                exists=db_file.exists(),
            )

            return checkpointer

        except Exception as e:
            logger.error(
                "Failed to create checkpointer",
                db_path=resolved_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Clean up connection if creation failed
            if self._connection is not None:
                await self._connection.close()
                self._connection = None
            raise

    async def cleanup_false_errors(self) -> int:
        """
        Remove CancelledError entries from successful runs.

        This cleanup removes false error checkpoint writes that occur when
        post-completion cancellations happen during checkpoint finalization.
        These are safe to remove as they represent expected shutdown behavior,
        not actual errors.

        Returns:
            Number of false error entries removed

        Example:
            >>> manager = CheckpointerManager()
            >>> await manager.create_checkpointer()
            >>> removed = await manager.cleanup_false_errors()
            >>> print(f"Removed {removed} false error entries")
        """
        db_path = Path(self.settings.CHECKPOINT_DB_PATH)

        # If database doesn't exist yet, nothing to clean up
        if not db_path.exists():
            logger.debug("Database does not exist, nothing to cleanup")
            return 0

        try:
            async with aiosqlite.connect(str(db_path)) as conn:
                # Count false error entries
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) FROM writes
                    WHERE channel = '__error__'
                    AND task_id IN (
                        SELECT DISTINCT task_id FROM checkpoints
                        WHERE metadata LIKE '%completed_naturally%'
                    )
                    """
                )
                row = await cursor.fetchone()
                count = row[0] if row else 0

                if count > 0:
                    # Delete false error entries
                    await conn.execute(
                        """
                        DELETE FROM writes
                        WHERE channel = '__error__'
                        AND task_id IN (
                            SELECT DISTINCT task_id FROM checkpoints
                            WHERE metadata LIKE '%completed_naturally%'
                        )
                        """
                    )
                    await conn.commit()

                    logger.info(
                        "Cleaned up false error entries from successful runs",
                        removed_count=count,
                    )

                return count

        except aiosqlite.OperationalError as e:
            # Table might not exist yet
            if "no such table" in str(e).lower():
                logger.debug("Writes table does not exist yet")
                return 0
            else:
                logger.error("Failed to cleanup false errors", error=str(e))
                return 0
        except Exception as e:
            logger.error(
                "Unexpected error during false error cleanup",
                error=str(e),
                error_type=type(e).__name__,
            )
            return 0

    async def cleanup_old_checkpoints(self, days: int = 30) -> int:
        """
        Clean up checkpoints older than specified number of days.

        Args:
            days: Number of days to retain. Checkpoints older than this are deleted.
                 Defaults to settings.CHECKPOINT_CLEANUP_DAYS (30 days).

        Returns:
            Number of checkpoints deleted

        Example:
            >>> manager = CheckpointerManager()
            >>> await manager.create_checkpointer()
            >>> deleted = await manager.cleanup_old_checkpoints(days=7)
            >>> print(f"Deleted {deleted} old checkpoints")
        """
        # Use provided days or fall back to settings
        cleanup_days = days if days != 30 else self.settings.CHECKPOINT_CLEANUP_DAYS
        cutoff_date = datetime.now() - timedelta(days=cleanup_days)
        deleted_count = 0

        db_path = Path(self.settings.CHECKPOINT_DB_PATH)

        # If database doesn't exist yet, nothing to clean up
        if not db_path.exists():
            logger.debug("Database does not exist, nothing to cleanup")
            return 0

        try:
            # Connect to database directly for cleanup operations
            async with aiosqlite.connect(str(db_path)) as conn:
                # Query for old checkpoints
                # LangGraph stores checkpoints with timestamp in 'ts' column
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) FROM checkpoints
                    WHERE ts < ?
                    """,
                    (cutoff_date.isoformat(),),
                )
                row = await cursor.fetchone()
                if row:
                    deleted_count = row[0]

                # Delete old checkpoints
                if deleted_count > 0:
                    await conn.execute(
                        """
                        DELETE FROM checkpoints
                        WHERE ts < ?
                        """,
                        (cutoff_date.isoformat(),),
                    )
                    await conn.commit()

                    logger.info(
                        "Cleaned up old checkpoints",
                        deleted_count=deleted_count,
                        cutoff_date=cutoff_date.isoformat(),
                        days=cleanup_days,
                    )

        except aiosqlite.OperationalError as e:
            # Table might not exist yet (no checkpoints created)
            if "no such table" in str(e).lower():
                logger.debug("Checkpoints table does not exist yet")
                return 0
            else:
                logger.error("Failed to cleanup checkpoints", error=str(e))
                # Don't raise - cleanup is best-effort
                return 0
        except Exception as e:
            logger.error(
                "Unexpected error during cleanup",
                error=str(e),
                error_type=type(e).__name__,
            )
            return 0

        return deleted_count

    async def close(self) -> None:
        """
        Close checkpointer connections and clean up resources.

        This method is idempotent - calling it multiple times is safe.

        Example:
            >>> manager = CheckpointerManager()
            >>> checkpointer = await manager.create_checkpointer()
            >>> # ... use checkpointer ...
            >>> await manager.close()
        """
        if self._checkpointer is not None:
            self._checkpointer = None
            logger.debug("Cleared checkpointer reference")

        if self._connection is not None:
            try:
                await self._connection.close()
                self._connection = None
                logger.debug("Closed database connection")
            except Exception as e:
                logger.warning(
                    "Error closing database connection", error=str(e)
                )

    async def __aenter__(self) -> "CheckpointerManager":
        """
        Enter async context manager.

        Returns:
            Self for use in async with statements

        Example:
            >>> async with CheckpointerManager() as manager:
            ...     checkpointer = await manager.create_checkpointer()
            ...     # Use checkpointer
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit async context manager and cleanup resources.

        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception value if exception occurred
            exc_tb: Exception traceback if exception occurred
        """
        await self.close()
