# Test Fixtures Documentation

## Purpose

The `tests/fixtures/` directory provides reusable test fixtures, mock data, and shared test utilities for the Deep Agent AGI test suite. Fixtures promote test isolation, maintainability, and consistent test setup across the entire codebase.

**Key Benefits:**
- **Reusability:** Share common test setup across multiple tests
- **Isolation:** Each test gets fresh fixtures to prevent state pollution
- **Maintainability:** Update test data in one place
- **Readability:** Clear, declarative test dependencies via fixture injection
- **Performance:** Session-scoped fixtures reduce expensive setup operations

---

## Directory Structure

```
tests/fixtures/
├── __init__.py              # Package marker with fixture overview
├── README.md                # This file (comprehensive documentation)
└── mock_responses/          # Mock API response data
    └── __init__.py          # Mock response definitions and documentation
```

**Note:** Most fixtures are defined in `tests/conftest.py` (root level) for automatic pytest discovery. This allows all tests to access fixtures without explicit imports.

---

## Available Fixtures

### Directory Fixtures

#### `project_root`
- **Purpose:** Provides absolute path to repository root
- **Scope:** Function-scoped
- **Returns:** `Path` object to project root
- **Dependencies:** None
- **Example:**
  ```python
  def test_config_file(project_root):
      config_file = project_root / "pyproject.toml"
      assert config_file.exists()
  ```

#### `test_data_dir`
- **Purpose:** Provides path to test fixtures directory
- **Scope:** Function-scoped
- **Returns:** `Path` object to `tests/fixtures/`
- **Dependencies:** `project_root`
- **Example:**
  ```python
  def test_load_mock_data(test_data_dir):
      mock_file = test_data_dir / "mock_responses" / "chat.json"
      data = json.loads(mock_file.read_text())
  ```

#### `temp_workspace`
- **Purpose:** Creates isolated temporary directory for file operation tests
- **Scope:** Function-scoped (fresh workspace per test)
- **Returns:** `Path` object to temporary directory with pre-created test files
- **Dependencies:** `tmp_path` (pytest built-in)
- **Pre-created Files:**
  - `test.txt` - Plain text file
  - `data.json` - JSON file with sample data
  - `config.yaml` - YAML configuration file
- **Lifecycle:** Automatically cleaned up after test
- **Example:**
  ```python
  def test_read_file_tool(temp_workspace):
      file_path = temp_workspace / "test.txt"
      content = file_path.read_text()
      assert "Hello" in content
  ```

---

### Mock Service Fixtures (E2E Tests)

These fixtures mock external services to avoid API calls and charges during testing.

#### `mock_openai_client`
- **Purpose:** Mock OpenAI client for testing without real API calls
- **Scope:** Function-scoped
- **Returns:** `MagicMock` of OpenAI client
- **Dependencies:** None (patches at module level)
- **Mock Behavior:**
  - Returns assistant message: "I'm a helpful AI assistant. How can I assist you today?"
  - Includes token usage: 10 prompt, 20 completion, 30 total
  - `finish_reason`: "stop"
  - No tool calls
- **Example:**
  ```python
  def test_chat_endpoint(mock_openai_client):
      # OpenAI client is already mocked
      response = await agent_service.invoke("Hello")
      assert "helpful AI assistant" in response["messages"][-1]["content"]
  ```

#### `mock_openai_client_with_tool_calls`
- **Purpose:** Mock OpenAI client that simulates tool calling workflow
- **Scope:** Function-scoped
- **Returns:** `MagicMock` configured for multi-turn tool call flow
- **Dependencies:** None (patches at module level)
- **Mock Behavior:**
  - **First call:** Returns `tool_calls` (read_file with path="test.txt")
  - **Second call:** Returns final text response after tool execution
  - Simulates realistic LangGraph tool calling pattern
- **Example:**
  ```python
  def test_agent_with_tools(mock_openai_client_with_tool_calls, temp_workspace):
      response = await agent_service.invoke("Read test.txt")
      # Agent should have called read_file tool
      assert "completed the task" in response["messages"][-1]["content"]
  ```

#### `mock_langsmith`
- **Purpose:** Mock LangSmith tracing to prevent actual API calls
- **Scope:** Function-scoped
- **Returns:** `MagicMock` of LangSmith config getter (returns None)
- **Dependencies:** None (patches at module level)
- **Mock Behavior:**
  - `get_langsmith_config()` returns `None` (tracing disabled)
  - No traces sent to LangSmith API
  - Tracing code paths still executed for integration testing
- **Example:**
  ```python
  def test_agent_without_tracing(mock_langsmith):
      # LangSmith is disabled but code still works
      response = await agent_service.invoke("Hello")
      assert response is not None
  ```

#### `mock_perplexity_search`
- **Purpose:** Mock Perplexity web search for testing
- **Scope:** Function-scoped
- **Returns:** `AsyncMock` of web_search function
- **Dependencies:** None (patches at module level)
- **Mock Behavior:**
  - Returns: `"Search results for '{query}': Mock result 1, Mock result 2, Mock result 3."`
  - No actual network requests
  - Consistent results for reproducible tests
- **Example:**
  ```python
  @pytest.mark.asyncio
  async def test_web_search(mock_perplexity_search):
      result = await web_search("Python docs")
      assert "Mock result" in result
  ```

#### `mock_agent_service`
- **Purpose:** Mock AgentService for API endpoint testing without agent execution
- **Scope:** Function-scoped
- **Returns:** `AsyncMock` of AgentService instance
- **Dependencies:** None (patches at module level)
- **Mock Behavior:**
  - `invoke()`: Returns mock conversation with user/assistant messages
  - `get_state()`: Returns mock state with empty `next[]` (completed)
  - `update_state()`: Returns `None` (no-op)
- **Example:**
  ```python
  @pytest.mark.asyncio
  async def test_chat_api(client, mock_agent_service):
      response = await client.post("/api/v1/chat", json={"message": "Hello"})
      assert response.status_code == 200
  ```

---

### Test Data Fixtures

Pre-configured test data matching API schemas.

#### `sample_chat_message`
- **Purpose:** Sample chat message for testing
- **Scope:** Function-scoped
- **Returns:** `dict` with message and thread_id
- **Schema:**
  - `message` (str): User's message text
  - `thread_id` (str): Conversation thread identifier
- **Example:**
  ```python
  def test_chat_validation(sample_chat_message):
      assert "message" in sample_chat_message
      assert sample_chat_message["thread_id"] == "test-thread-123"
  ```

#### `sample_chat_response`
- **Purpose:** Sample chat response for testing
- **Scope:** Function-scoped
- **Returns:** `dict` matching ChatResponse schema
- **Schema:**
  - `messages` (list): Conversation history [user, assistant messages]
  - `thread_id` (str): Conversation thread identifier
  - `status` (str): Response status ("success", "error", etc.)
- **Example:**
  ```python
  def test_response_validation(sample_chat_response):
      assert sample_chat_response["status"] == "success"
      assert len(sample_chat_response["messages"]) == 2
  ```

#### `sample_tool_calls`
- **Purpose:** Sample tool call data for testing
- **Scope:** Function-scoped
- **Returns:** `list` of tool call dicts matching OpenAI's format
- **Schema (per tool call):**
  - `id` (str): Unique tool call identifier
  - `type` (str): Call type (usually "function")
  - `function` (dict):
    - `name` (str): Tool/function name
    - `arguments` (str): JSON-encoded arguments
  - `result` (str): Tool execution result (added for testing, not in OpenAI schema)
- **Example:**
  ```python
  def test_tool_parsing(sample_tool_calls):
      assert len(sample_tool_calls) == 2
      assert sample_tool_calls[0]["function"]["name"] == "read_file"
  ```

---

### Async Test Support

#### `event_loop`
- **Purpose:** Provides event loop for async tests
- **Scope:** Function-scoped
- **Returns:** `asyncio.AbstractEventLoop`
- **Dependencies:** None
- **Lifecycle:** Automatically closed after test
- **Example:**
  ```python
  @pytest.mark.asyncio
  async def test_async_function(event_loop):
      result = await some_async_function()
      assert result is not None
  ```

**Note:** `pytest-asyncio` provides this automatically, but explicit fixture ensures consistent behavior across pytest versions.

---

### UI Fixtures (Playwright)

Defined in `tests/ui/conftest.py` for browser automation testing.

#### `browser_context_args`
- **Purpose:** Configure browser context for all UI tests
- **Scope:** Session-scoped
- **Configuration:**
  - Base URL: `http://localhost:3000`
  - Viewport: 1280x720
  - Locale: en-US
  - Timezone: America/New_York
- **Environment Variables:**
  - `PLAYWRIGHT_BASE_URL`: Override base URL
  - `PLAYWRIGHT_TIMEOUT`: Override timeout (default: 30000ms)
  - `PLAYWRIGHT_HEADED`: Run in headed mode (default: false)

#### `page`
- **Purpose:** Provides fresh Playwright page for each test
- **Scope:** Function-scoped
- **Features:**
  - Automatic timeout configuration
  - Navigation to base URL
  - Screenshot on test failure
- **Example:**
  ```python
  @pytest.mark.ui
  def test_homepage(page):
      page.goto("/")
      assert page.title() == "Deep Agent AGI"
  ```

#### `authenticated_page`
- **Purpose:** Provides page with user authentication complete
- **Scope:** Function-scoped
- **Dependencies:** `page`
- **Note:** Currently a no-op (Phase 0 has no auth)

#### `chat_page`
- **Purpose:** Provides page navigated to chat interface
- **Scope:** Function-scoped
- **Dependencies:** `page`
- **Features:**
  - Navigates to `/chat`
  - Waits for WebSocket connection
- **Example:**
  ```python
  @pytest.mark.ui
  def test_chat_interface(chat_page):
      chat_page.fill('[data-testid="chat-input"]', "Hello")
      chat_page.click('[data-testid="send-button"]')
  ```

---

### Experiment Fixtures (Prompt Optimization)

Defined in `tests/experiments/conftest.py` for A/B testing experiments.

#### `langsmith_client`
- **Purpose:** Provides LangSmith client for experiments
- **Scope:** Function-scoped
- **Requires:** `LANGSMITH_API_KEY` environment variable
- **Skips test if:** API key not set

#### `test_scenarios`
- **Purpose:** Provides test scenarios for prompt experiments
- **Returns:** `TEST_SCENARIOS` dict from test_scenarios module

#### `prompt_variants`
- **Purpose:** Provides list of available prompt variant names
- **Returns:** `["control", "max_compression", "balanced", "conservative"]`

#### `settings`
- **Purpose:** Provides test settings with checkpointer disabled
- **Returns:** Settings instance with `ENV = "test"`

#### `agent_service_factory`
- **Purpose:** Factory for creating AgentService with different prompt variants
- **Scope:** Function-scoped
- **Returns:** Async factory function
- **Example:**
  ```python
  @pytest.mark.asyncio
  async def test_prompt_variant(agent_service_factory):
      service = await agent_service_factory("balanced")
      response = await service.invoke("Test query")
  ```

---

## Using Fixtures in Tests

### Basic Usage

Fixtures are injected into test functions via parameter names:

```python
def test_example(project_root, sample_chat_message):
    # Fixtures are automatically injected by pytest
    assert project_root.exists()
    assert "message" in sample_chat_message
```

### Fixture Scope

Pytest fixtures support different scopes:

- **function** (default): New instance per test function
- **class**: Shared across test class methods
- **module**: Shared across test module
- **package**: Shared across test package
- **session**: Shared across entire test session

**Recommendation:** Use function scope unless expensive setup justifies sharing.

### Fixture Dependencies

Fixtures can depend on other fixtures:

```python
@pytest.fixture
def dependent_fixture(project_root, test_data_dir):
    # project_root and test_data_dir are automatically resolved
    return project_root / "custom_path"
```

### Autouse Fixtures

Use `autouse=True` for fixtures that should run for every test:

```python
@pytest.fixture(autouse=True)
def setup_logging():
    # This runs before every test automatically
    logging.basicConfig(level=logging.DEBUG)
```

### Parameterized Fixtures

Create multiple fixture variations:

```python
@pytest.fixture(params=["control", "balanced", "conservative"])
def prompt_variant(request):
    return request.param

def test_with_variants(prompt_variant):
    # This test runs 3 times with different prompt_variant values
    assert prompt_variant in ["control", "balanced", "conservative"]
```

---

## Creating New Fixtures

### Best Practices

1. **Minimize Side Effects:** Fixtures should not modify global state
2. **Clear Naming:** Use descriptive names indicating purpose
3. **Appropriate Scope:** Choose minimal scope needed (prefer function-scoped)
4. **Document Dependencies:** Clearly document fixture dependencies
5. **Factory Pattern:** Use factory fixtures for parameterized data generation
6. **Isolation:** Each test should get fresh fixtures to prevent pollution

### Example: Creating a New Fixture

```python
@pytest.fixture
def sample_user_data() -> dict:
    """
    Provide sample user data for testing.

    Scope:
        Function-scoped (new instance per test)

    Dependencies:
        None

    Returns:
        dict: User data with username, email, and role

    Example:
        >>> def test_user_creation(sample_user_data):
        ...     user = create_user(**sample_user_data)
        ...     assert user.username == "testuser"
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
    }
```

### Factory Fixtures

For dynamic data generation:

```python
@pytest.fixture
def user_factory():
    """Factory for creating user data with custom attributes."""
    def _create_user(username="testuser", email=None, role="user"):
        return {
            "username": username,
            "email": email or f"{username}@example.com",
            "role": role,
        }
    return _create_user

def test_with_factory(user_factory):
    admin = user_factory(username="admin", role="admin")
    regular = user_factory(username="user123")
    assert admin["role"] == "admin"
    assert regular["role"] == "user"
```

---

## Fixture Dependencies and Composition

### Dependency Graph

```
project_root (no dependencies)
└── test_data_dir
    └── (used by tests loading mock data)

tmp_path (pytest built-in)
└── temp_workspace
    └── (used by file operation tests)

mock_openai_client (no dependencies)
├── (used by E2E tests)
└── mock_openai_client_with_tool_calls (similar, tool variant)

page (depends on browser_context_args)
├── authenticated_page
└── chat_page

agent_service_factory (depends on settings)
```

### Composition Example

```python
@pytest.fixture
def configured_agent(agent_service_factory, settings):
    """Create pre-configured agent for testing."""
    async def _create():
        service = await agent_service_factory("balanced")
        # Additional configuration
        return service
    return _create

@pytest.mark.asyncio
async def test_agent_behavior(configured_agent):
    agent = await configured_agent()
    response = await agent.invoke("Test query")
    assert response is not None
```

---

## Factory Fixtures vs. Data Fixtures

### Data Fixtures

Return static data (same for all tests):

```python
@pytest.fixture
def sample_config():
    return {"timeout": 30, "retries": 3}
```

**When to use:** Consistent, static test data

### Factory Fixtures

Return function that generates data:

```python
@pytest.fixture
def config_factory():
    def _create(timeout=30, retries=3):
        return {"timeout": timeout, "retries": retries}
    return _create
```

**When to use:** Parameterized data, multiple variations per test

---

## Dependencies

### Core Testing
- **pytest:** Testing framework and fixture system
- **pytest-asyncio:** Async test support
- **pytest-playwright:** Browser automation fixtures

### Mocking
- **unittest.mock:** MagicMock, AsyncMock, patch utilities

### Optional (for advanced scenarios)
- **factory_boy:** Advanced factory patterns for complex data generation
- **faker:** Generate realistic fake data for tests

---

## Related Documentation

### Internal
- `tests/conftest.py` - Root-level fixture definitions
- `tests/ui/conftest.py` - Playwright UI fixtures
- `tests/experiments/conftest.py` - Experiment-specific fixtures
- `CLAUDE.md` - Development guide with testing strategy

### External
- [pytest fixtures documentation](https://docs.pytest.org/en/stable/fixture.html)
- [pytest-playwright documentation](https://playwright.dev/python/docs/test-runners)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)

---

## Best Practices Summary

### DO:
✅ Use function-scoped fixtures by default
✅ Document fixture purpose, scope, and dependencies
✅ Keep fixtures focused and single-purpose
✅ Use factory patterns for parameterized data
✅ Mock external services to avoid API calls
✅ Clean up resources in teardown (use `yield`)
✅ Test fixture behavior in isolation

### DON'T:
❌ Don't modify global state in fixtures
❌ Don't use session scope unnecessarily
❌ Don't create fixtures with side effects
❌ Don't hardcode environment-specific values
❌ Don't mix setup and test logic
❌ Don't share mutable data across tests
❌ Don't forget to document dependencies

---

## Troubleshooting

### Common Issues

**Issue:** Fixture not found
```
ERROR: fixture 'my_fixture' not found
```
**Solution:** Ensure fixture is defined in `conftest.py` or imported correctly

**Issue:** Fixture runs too many times
**Solution:** Check fixture scope - use session/module scope for expensive setup

**Issue:** Tests fail due to state pollution
**Solution:** Verify fixtures are function-scoped and return fresh data

**Issue:** Mock not being applied
**Solution:** Check patch target path matches actual import path

---

## Questions?

For questions or issues with fixtures:
1. Review this README
2. Check fixture docstrings in `tests/conftest.py`
3. Review pytest fixture documentation
4. Consult CLAUDE.md for testing strategy

---

**Last Updated:** 2025-11-12
**Version:** Phase 0 (MVP)
