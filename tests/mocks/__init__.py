"""
Mock implementations and fixtures for Deep Agent AGI test suite.

This module serves as the namespace for all mock implementations used across
the test suite. While the core mock fixtures are defined in `tests/conftest.py`
for easy access across all test files, this directory provides a centralized
location for understanding the mocking strategy.

Mock Organization
-----------------
The test suite uses pytest fixtures (defined in conftest.py) as the primary
mechanism for providing mock implementations. This approach:

- Centralizes mock definitions for consistency across tests
- Provides automatic dependency injection via pytest
- Simplifies test code by removing boilerplate setup
- Enables parametrized testing with different mock configurations

Available Mock Categories
------------------------
1. **Service Mocks** (External APIs)
   - mock_openai_client: GPT-5 API responses
   - mock_openai_client_with_tool_calls: Tool execution simulation
   - mock_langsmith: Tracing and observability
   - mock_perplexity_search: Web search results

2. **Component Mocks** (Internal Services)
   - mock_agent_service: Agent invocation and state management
   - mock_checkpointer: State persistence (AsyncSqliteSaver)
   - mock_llm: LLM instance (ChatOpenAI)
   - mock_compiled_graph: LangGraph state graph

3. **Data Fixtures** (Test Data)
   - sample_chat_message: User message payloads
   - sample_chat_response: Agent response payloads
   - sample_tool_calls: Tool execution results

4. **Environment Fixtures** (Test Infrastructure)
   - temp_workspace: Isolated filesystem for file tool testing
   - test_data_dir: Access to test fixtures/data
   - project_root: Repository root path

Usage Examples
--------------
Mock fixtures are injected into tests via pytest's dependency injection:

    def test_agent_responds_to_query(mock_openai_client, sample_chat_message):
        '''Test agent generates response using mocked OpenAI API.'''
        # mock_openai_client is automatically configured and injected
        response = agent.invoke(sample_chat_message)
        assert response["status"] == "success"

For custom mock behavior, configure the fixture before use:

    def test_agent_handles_tool_call(mock_openai_client):
        '''Test agent executes tool and processes result.'''
        # Customize mock response
        mock_openai_client.chat.completions.create.return_value.choices[0].message.tool_calls = [
            MagicMock(function=MagicMock(name="read_file", arguments='{"path": "test.txt"}'))
        ]

        response = agent.invoke({"message": "Read test.txt"})
        assert "File contents" in response["messages"][-1]["content"]

Mocking Philosophy
------------------
**When to Mock:**
- External API calls (OpenAI, Perplexity, LangSmith)
- Database operations (checkpointer, vector store)
- Network requests (web search, webhooks)
- File I/O that modifies real filesystem (use temp_workspace)

**When NOT to Mock:**
- Pure functions (no side effects)
- Simple data transformations
- Internal business logic (test actual implementation)
- Configuration loading (use test fixtures/env files)

**Mock vs. Patch vs. MagicMock:**
- **Mock/MagicMock**: Direct replacement with spec for type checking
- **@patch**: Decorator for replacing modules/classes at import time
- **Fixtures**: Pytest's preferred approach for reusable mocks

See Also
--------
- tests/conftest.py: Central fixture definitions
- tests/mocks/README.md: Comprehensive mocking guide
- unittest.mock documentation: https://docs.python.org/3/library/unittest.mock.html
- pytest-mock plugin: https://pytest-mock.readthedocs.io/

Notes
-----
- All mock fixtures follow AAA pattern (Arrange-Act-Assert)
- Mock responses match real API schemas for realistic testing
- Fixtures are scoped to function-level by default (fresh per test)
- Use @pytest.fixture(scope="session") for expensive setup (rare)
"""
