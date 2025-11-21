"""Integration tests for database operations.

This module tests database interactions, including checkpoint storage,
state persistence, and query operations. Tests use real database
connections with test-specific databases.

Database Components:
    - SQLite checkpointer (LangGraph state persistence)
    - PostgreSQL connections (Phase 1+)
    - Migration scripts
    - Query operations

Test Strategy:
    - Use temporary test databases
    - Real database connections (not mocked)
    - Cleanup after each test
    - Test transactions and rollbacks

Planned Test Coverage:
    - Checkpoint creation and retrieval
    - Thread state persistence
    - Checkpoint expiration/cleanup
    - Concurrent access patterns
    - Migration scripts
    - Database error handling

Note: Database integration tests will be added in Phase 0 completion.
Currently, checkpointer is tested indirectly via agent workflow tests.
"""
