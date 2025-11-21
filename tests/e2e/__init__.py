"""
End-to-End (E2E) Test Suite for Deep Agent AGI.

This package contains end-to-end tests that validate complete user workflows
and journeys through the system with minimal mocking. E2E tests focus on
testing the integration of all components working together as a complete system.

Purpose:
    E2E tests simulate real user interactions with the system to verify that
    all components (API, services, agents, tools, database, external APIs)
    work together correctly to deliver complete functionality.

    These tests are organized by workflow type:
    - test_complete_workflows/: Core workflows (chat, HITL, tool usage)
    - test_user_journeys/: Complex multi-step user scenarios
    - test_reasoning_scenarios/: Deep reasoning and planning workflows

Philosophy:
    - Minimal mocking: Only mock external APIs (OpenAI, Perplexity, LangSmith)
    - Test complete flows: From API request to final response
    - Focus on user stories: Each test represents a real user scenario
    - Data realism: Use realistic test data and scenarios
    - State management: Verify state persistence and thread safety

Phase 0.5 Live API Testing:
    These tests are designed for Phase 0.5 Live API Integration Testing and
    require valid API keys. They are skipped in regular CI/CD runs and should
    only be run manually or as part of live API validation:

    ```bash
    # Run E2E tests manually (requires OPENAI_API_KEY)
    pytest tests/e2e/ -v --maxfail=1
    ```

Best Practices:
    1. Write tests as user stories (Given-When-Then)
    2. Use descriptive test names that explain the workflow
    3. Keep tests independent (no shared state between tests)
    4. Clean up resources (use fixtures with teardown)
    5. Test both happy paths and error scenarios
    6. Verify response structure, status codes, and business logic
    7. Focus on critical paths (80% of user interactions)
    8. Keep tests fast (<30s per test) by avoiding unnecessary delays

Example Test Structure:
    ```python
    def test_complete_user_workflow(client, fixtures):
        '''
        Test complete workflow from user perspective.

        User Story:
            As a user, I want to [action] so that [outcome].

        Flow:
            1. User performs action A
            2. System processes and responds
            3. User performs action B based on response
            4. System completes workflow

        Success Criteria:
            - Step A completes successfully
            - Response contains expected data
            - Step B executes correctly
            - Final state matches expectations
        '''
        # Arrange (Given)
        test_data = {...}

        # Act (When)
        response = client.post("/api/endpoint", json=test_data)

        # Assert (Then)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    ```

See Also:
    - tests/e2e/README.md: Detailed E2E testing guide
    - tests/integration/: Integration tests (focused component testing)
    - tests/unit/: Unit tests (isolated function testing)
"""
