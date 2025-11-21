"""
Test fixtures package for Deep Agent AGI.

This package provides reusable test fixtures, mock data, and shared test utilities
for the Deep Agent AGI test suite. Fixtures are organized by scope and purpose to
promote test isolation and maintainability.

Directory Structure:
    fixtures/
    ├── __init__.py              # This file (package marker)
    └── mock_responses/          # Mock API response data
        └── __init__.py

Available Fixtures:
    Most fixtures are defined in tests/conftest.py (root level) for pytest auto-discovery.
    See tests/conftest.py for complete fixture documentation.

Fixture Categories:
    - Directory fixtures: project_root, test_data_dir, temp_workspace
    - Mock service fixtures: mock_openai_client, mock_langsmith, mock_perplexity_search
    - Test data fixtures: sample_chat_message, sample_chat_response, sample_tool_calls
    - Async fixtures: event_loop
    - UI fixtures: page, authenticated_page, chat_page (tests/ui/conftest.py)
    - Experiment fixtures: langsmith_client, test_scenarios, agent_service_factory (tests/experiments/conftest.py)

Usage:
    Fixtures are automatically discovered by pytest and can be injected into test functions:

    >>> def test_agent_chat(sample_chat_message, mock_openai_client):
    ...     # Fixtures are injected automatically
    ...     assert sample_chat_message["message"] == "Hello, agent! How are you?"

Best Practices:
    - Use function-scoped fixtures for test isolation (default)
    - Use session-scoped fixtures for expensive setup (browsers, databases)
    - Prefer factory fixtures for parameterized data generation
    - Mock external services to avoid API calls and charges
    - Use temp_workspace for file operation tests to avoid side effects

Related Documentation:
    - tests/fixtures/README.md: Comprehensive fixture documentation
    - tests/conftest.py: Root-level fixture definitions
    - tests/ui/conftest.py: Playwright UI fixtures
    - tests/experiments/conftest.py: Experiment-specific fixtures
"""
