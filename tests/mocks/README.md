# Mock Implementations and Testing Strategy

## Overview

This directory contains documentation and organization for mock implementations used throughout the Deep Agent One test suite. Mocks provide test doubles for external services, APIs, and complex internal components, enabling fast, deterministic, and cost-free testing.

## Purpose

Mocks serve several critical testing needs:

1. **Eliminate External Dependencies**: Test without requiring live API keys, network access, or third-party services
2. **Deterministic Behavior**: Guarantee consistent test results regardless of external factors
3. **Cost Control**: Avoid charges from GPT-5, Perplexity, and other paid APIs during testing
4. **Speed**: Execute tests in milliseconds instead of waiting for API responses
5. **Edge Case Testing**: Simulate error conditions, timeouts, and rare scenarios that are difficult to reproduce with real APIs
6. **Isolation**: Test individual components without side effects from dependencies

## Directory Structure

```
tests/
├── mocks/
│   ├── __init__.py         # Module documentation (this namespace)
│   └── README.md           # Comprehensive mocking guide (this file)
├── conftest.py             # Central fixture definitions (primary mock location)
└── [test directories]/
    └── conftest.py         # Test-specific fixtures (if needed)
```

**Note**: While dedicated mock implementation files can be created in `tests/mocks/` for complex scenarios, the current architecture uses pytest fixtures in `tests/conftest.py` as the primary mechanism for providing mocks. This approach:

- Centralizes mock definitions for consistency
- Provides automatic dependency injection via pytest
- Simplifies test code by removing boilerplate setup
- Enables easy fixture composition and reuse

## Available Mocks

### Service Mocks (External APIs)

#### 1. `mock_openai_client`
**What it mocks**: OpenAI Python SDK client for GPT-5 API calls
**Location**: `tests/conftest.py`

**Behavior**:
- Returns pre-configured chat completion response
- Simulates assistant message: "I'm a helpful AI assistant..."
- Includes realistic token usage (10 prompt, 20 completion, 30 total)
- No tool calls (simple text response)

**Use cases**:
- E2E tests for basic chat workflows
- Testing chat endpoint responses
- Verifying LLM integration without API costs

**Example**:
```python
def test_agent_responds_to_greeting(mock_openai_client):
    """Test agent generates response to user greeting."""
    response = await agent_service.invoke({"message": "Hello"})

    assert "helpful AI assistant" in response["messages"][-1]["content"]
    assert mock_openai_client.chat.completions.create.called
```

#### 2. `mock_openai_client_with_tool_calls`
**What it mocks**: OpenAI client with tool calling workflow
**Location**: `tests/conftest.py`

**Behavior**:
- Returns **sequence** of two responses:
  1. Tool call request (read_file with path="test.txt")
  2. Final response after tool execution
- Simulates realistic LangGraph tool usage pattern
- Tests multi-turn agent conversations

**Use cases**:
- Testing file system tool execution
- Verifying tool call argument parsing
- E2E workflows with tool usage
- Testing agent behavior with tool results

**Example**:
```python
def test_agent_reads_file_with_tool(mock_openai_client_with_tool_calls, temp_workspace):
    """Test agent uses read_file tool correctly."""
    response = await agent_service.invoke({"message": "Read test.txt"})

    # Verify tool was invoked and final response generated
    assert "completed the task" in response["messages"][-1]["content"]
    assert mock_openai_client_with_tool_calls.chat.completions.create.call_count == 2
```

#### 3. `mock_langsmith`
**What it mocks**: LangSmith tracing configuration
**Location**: `tests/conftest.py`

**Behavior**:
- Returns `None` for `get_langsmith_config()` (disables tracing)
- Prevents actual traces from being sent to LangSmith API
- Maintains tracing code paths for integration testing

**Use cases**:
- E2E tests without external tracing dependencies
- Testing code that checks for LangSmith configuration
- Cost-free testing (no LangSmith API usage)

**Example**:
```python
def test_agent_works_without_tracing(mock_langsmith):
    """Test agent functions when LangSmith is disabled."""
    response = await agent_service.invoke({"message": "Hello"})

    assert response is not None
    # Verify tracing was disabled
    mock_langsmith.assert_called_once()
    assert mock_langsmith.return_value is None
```

#### 4. `mock_perplexity_search`
**What it mocks**: Perplexity MCP web search function
**Location**: `tests/conftest.py`

**Behavior**:
- Returns mock search results string
- Format: "Search results for '{query}': Mock result 1, Mock result 2, Mock result 3."
- Async function matching real web_search signature
- Deterministic results for reproducible tests

**Use cases**:
- Testing web search tool integration
- E2E workflows using web_search
- Unit testing search result processing
- Cost-free testing (no Perplexity API charges)

**Example**:
```python
@pytest.mark.asyncio
async def test_agent_performs_web_search(mock_perplexity_search):
    """Test agent uses web_search tool correctly."""
    result = await web_search("Python documentation")

    assert "Python documentation" in result
    assert "Mock result" in result
```

### Component Mocks (Internal Services)

#### 5. `mock_agent_service`
**What it mocks**: AgentService class for agent invocation and state management
**Location**: `tests/conftest.py`

**Behavior**:
- `invoke()`: Returns pre-configured chat response
- `get_state()`: Returns mock state with empty "next" (completed)
- `update_state()`: No-op (returns None)
- Simulates complete AgentService interface

**Use cases**:
- Testing API endpoints without running actual agents
- Unit testing chat route handlers
- Testing HITL approval workflows
- Fast integration tests

**Example**:
```python
def test_chat_endpoint_success(mock_agent_service, client):
    """Test /chat endpoint with mocked agent."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "thread_id": "test-123"}
    )

    assert response.status_code == 200
    assert "Hi there" in response.json()["messages"][-1]["content"]
```

#### 6. `mock_checkpointer`
**What it mocks**: AsyncSqliteSaver (LangGraph checkpointer)
**Location**: Test-specific fixtures in individual test files

**Behavior**:
- AsyncMock with `setup()` method
- Simulates state persistence without database
- Used in agent creation tests

**Use cases**:
- Unit testing agent initialization
- Testing checkpointer integration
- Avoiding filesystem dependencies

**Example**:
```python
@pytest.fixture
def mock_checkpointer() -> AsyncSqliteSaver:
    """Mock checkpointer for agent tests."""
    checkpointer = AsyncMock(spec=AsyncSqliteSaver)
    checkpointer.setup = AsyncMock()
    return checkpointer

@pytest.mark.asyncio
async def test_agent_uses_checkpointer(mock_checkpointer):
    """Test agent initializes with checkpointer."""
    agent = await create_agent(checkpointer=mock_checkpointer)

    assert agent is not None
    mock_checkpointer.setup.assert_called_once()
```

#### 7. `mock_llm`
**What it mocks**: ChatOpenAI LLM instance
**Location**: Test-specific fixtures

**Behavior**:
- Mock with ChatOpenAI spec
- Pre-configured model name, temperature, max_tokens
- Used for testing LLM factory integration

**Use cases**:
- Unit testing LLM configuration
- Testing reasoning effort configuration
- Verifying LLM factory calls

**Example**:
```python
@pytest.fixture
def mock_llm() -> ChatOpenAI:
    """Mock LLM for factory tests."""
    llm = Mock(spec=ChatOpenAI)
    llm.model_name = "gpt-5"
    llm.temperature = 0.7
    return llm

def test_llm_factory_creates_gpt5(mock_llm):
    """Test LLM factory creates GPT-5 instance."""
    with patch("backend.deep_agent.services.llm_factory.ChatOpenAI") as mock_cls:
        mock_cls.return_value = mock_llm

        llm = create_gpt5_llm(api_key="test-key")

        assert llm.model_name == "gpt-5"
```

### Data Fixtures (Test Data)

#### 8. `sample_chat_message`
**What it provides**: Example user message payload
**Location**: `tests/conftest.py`

**Schema**:
```python
{
    "message": "Hello, agent! How are you?",
    "thread_id": "test-thread-123"
}
```

**Use cases**:
- Standardized input for chat endpoint tests
- Consistent test data across test suite

#### 9. `sample_chat_response`
**What it provides**: Example agent response payload
**Location**: `tests/conftest.py`

**Schema**:
```python
{
    "messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! I'm doing well, thank you!"}
    ],
    "thread_id": "test-thread-123",
    "status": "success"
}
```

**Use cases**:
- Expected output validation
- Response schema testing
- API contract verification

#### 10. `sample_tool_calls`
**What it provides**: Example tool call data
**Location**: `tests/conftest.py`

**Schema**:
```python
[
    {
        "id": "call_001",
        "type": "function",
        "function": {
            "name": "read_file",
            "arguments": '{"path": "test.txt"}'
        },
        "result": "File contents: Hello, world!"
    },
    {
        "id": "call_002",
        "type": "function",
        "function": {
            "name": "web_search",
            "arguments": '{"query": "Python documentation"}'
        },
        "result": "Search results: [Python.org, Real Python, ...]"
    }
]
```

**Use cases**:
- Testing tool execution logging
- Verifying tool result processing
- UI tool display testing

### Environment Fixtures (Test Infrastructure)

#### 11. `temp_workspace`
**What it provides**: Isolated temporary directory with test files
**Location**: `tests/conftest.py`

**Behavior**:
- Creates temporary directory under pytest's tmp_path
- Pre-populates with test files: test.txt, data.json, config.yaml
- Automatically cleaned up after test completes

**Use cases**:
- Testing file system tools (read_file, write_file, edit_file, ls)
- Isolated file operations without affecting real filesystem
- Testing file tool error handling

**Example**:
```python
def test_read_file_tool(temp_workspace):
    """Test read_file tool reads file correctly."""
    content = read_file_tool(temp_workspace / "test.txt")

    assert "Hello, this is a test file" in content
```

#### 12. `project_root`
**What it provides**: Absolute path to repository root
**Location**: `tests/conftest.py`

**Use cases**:
- Accessing project configuration files
- Loading test fixtures/data
- Verifying file structure

#### 13. `test_data_dir`
**What it provides**: Path to tests/fixtures directory
**Location**: `tests/conftest.py`

**Use cases**:
- Loading mock API responses from JSON files
- Accessing shared test resources
- Reading test fixture data

## Using Mocks in Tests

### Basic Fixture Injection

Pytest automatically injects fixtures into test functions:

```python
def test_with_mock(mock_openai_client, sample_chat_message):
    """Fixtures are injected by parameter name."""
    # mock_openai_client is already configured and patching OpenAI
    response = agent.invoke(sample_chat_message)
    assert response is not None
```

### Configuring Mock Responses

Override default mock behavior for specific test needs:

```python
def test_agent_handles_error(mock_openai_client):
    """Customize mock to simulate API error."""
    # Override default behavior
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

    # Test error handling
    with pytest.raises(Exception, match="API Error"):
        agent.invoke({"message": "Hello"})
```

### Verifying Mock Calls

Use unittest.mock assertion methods:

```python
def test_agent_calls_openai_once(mock_openai_client):
    """Verify agent makes exactly one API call."""
    agent.invoke({"message": "Hello"})

    # Verify call count
    assert mock_openai_client.chat.completions.create.call_count == 1

    # Verify call arguments
    call_args = mock_openai_client.chat.completions.create.call_args
    assert "Hello" in str(call_args)
```

### Combining Multiple Mocks

Inject multiple fixtures for complex scenarios:

```python
def test_agent_with_tools_and_search(
    mock_openai_client_with_tool_calls,
    mock_perplexity_search,
    temp_workspace
):
    """Test agent using both file tools and web search."""
    response = agent.invoke({
        "message": "Search for Python docs and save to file"
    })

    # Verify both mocks were used
    assert mock_openai_client_with_tool_calls.chat.completions.create.called
    assert mock_perplexity_search.called
```

## Creating New Mocks

### When to Create a New Mock

Create a new mock fixture when:

1. **External Service**: Mocking a new third-party API or service
2. **Expensive Operation**: Database queries, network requests, file I/O
3. **Non-Deterministic Behavior**: Random values, timestamps, external state
4. **Test Isolation**: Preventing side effects between tests
5. **Reusability**: Same mock needed across multiple test files

### Mock Implementation Guidelines

#### 1. Match the Real Interface

Use `spec` parameter to ensure mock matches actual class/function:

```python
from unittest.mock import Mock, AsyncMock
from backend.deep_agent.services.agent_service import AgentService

@pytest.fixture
def mock_agent_service():
    """Mock matching real AgentService interface."""
    # spec ensures mock has same methods/attributes as real class
    mock = AsyncMock(spec=AgentService)

    # Configure common return values
    mock.invoke.return_value = {"messages": [...]}
    mock.get_state.return_value = {"values": {...}}

    return mock
```

#### 2. Provide Realistic Responses

Mock responses should match real API schemas:

```python
@pytest.fixture
def mock_openai_completion():
    """Mock OpenAI completion with realistic structure."""
    completion = MagicMock()

    # Match real OpenAI response schema
    completion.choices = [
        MagicMock(
            message=MagicMock(
                content="Response text",
                role="assistant",
                tool_calls=None
            ),
            finish_reason="stop",
            index=0
        )
    ]

    completion.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )

    completion.model = "gpt-5"
    completion.created = 1234567890

    return completion
```

#### 3. Make Mocks Configurable

Allow tests to customize mock behavior:

```python
@pytest.fixture
def mock_web_search():
    """Configurable web search mock."""
    with patch("backend.deep_agent.tools.web_search.web_search") as mock:
        # Default behavior
        async def default_search(query: str) -> str:
            return f"Results for: {query}"

        mock.side_effect = default_search

        # Expose mock for test-specific configuration
        yield mock

def test_search_with_custom_result(mock_web_search):
    """Test can override default mock behavior."""
    # Customize for this specific test
    async def custom_search(query: str) -> str:
        return "Custom search result"

    mock_web_search.side_effect = custom_search

    result = await web_search("test query")
    assert result == "Custom search result"
```

#### 4. Use Appropriate Mock Types

**Mock vs AsyncMock**:
- `Mock`: Synchronous functions/methods
- `AsyncMock`: Async functions/methods (use for async def)

```python
from unittest.mock import Mock, AsyncMock

# Synchronous function
@pytest.fixture
def mock_sync_function():
    return Mock(return_value="result")

# Asynchronous function
@pytest.fixture
def mock_async_function():
    async_mock = AsyncMock()
    async_mock.return_value = "result"
    return async_mock
```

**MagicMock vs Mock**:
- `MagicMock`: Supports magic methods (`__str__`, `__len__`, etc.)
- `Mock`: Basic mock without magic methods

```python
# Use MagicMock when object is used in operators or special contexts
completion = MagicMock()  # Supports len(), str(), etc.
```

#### 5. Minimize Mock Logic

Keep mocks simple - avoid complex logic:

```python
# ✅ GOOD: Simple, predictable mock
@pytest.fixture
def mock_simple():
    mock = Mock()
    mock.get_data.return_value = {"key": "value"}
    return mock

# ❌ BAD: Complex logic in mock (defeats purpose of mocking)
@pytest.fixture
def mock_complex():
    mock = Mock()

    def complex_logic(arg):
        if arg == "special":
            # 20 lines of logic...
            return computed_value
        else:
            # More complex branching...
            return other_value

    mock.get_data.side_effect = complex_logic
    return mock
```

If you need complex logic, consider testing the real implementation with fixtures instead of mocking.

### Example: Creating a New Mock Fixture

Let's create a mock for a hypothetical vector store:

```python
# tests/conftest.py

from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.fixture
def mock_vector_store() -> AsyncMock:
    """
    Mock vector store for semantic search testing.

    Provides mock implementation of vector database operations
    without requiring actual pgvector/PostgreSQL.

    Scope:
        Function-scoped (fresh mock per test)

    Returns:
        AsyncMock: Vector store with pre-configured methods

    Mock Behavior:
        - add_documents(): Returns mock document IDs
        - similarity_search(): Returns mock search results
        - delete_documents(): Returns success status

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_vector_search(mock_vector_store):
        ...     results = await mock_vector_store.similarity_search("query")
        ...     assert len(results) > 0
    """
    mock = AsyncMock()

    # Mock add_documents
    async def mock_add(documents):
        return [f"doc_{i}" for i in range(len(documents))]

    mock.add_documents.side_effect = mock_add

    # Mock similarity_search
    async def mock_search(query, k=5):
        return [
            {"content": f"Result {i}", "score": 0.9 - (i * 0.1)}
            for i in range(min(k, 3))
        ]

    mock.similarity_search.side_effect = mock_search

    # Mock delete
    mock.delete_documents.return_value = True

    return mock
```

## Mock vs Patch vs MagicMock: When to Use Each

### Mock / MagicMock

**Use when**: Creating direct object replacements

```python
from unittest.mock import Mock, MagicMock

# Direct replacement
mock_client = Mock()
mock_client.get_data.return_value = "data"

# Use in test
result = mock_client.get_data()
assert result == "data"
```

**Advantages**:
- Simple and explicit
- Type-safe with `spec` parameter
- Easy to configure and verify

**Disadvantages**:
- Requires manual dependency injection
- No automatic patching of imports

### @patch Decorator

**Use when**: Replacing modules/classes at import time

```python
from unittest.mock import patch

@patch("backend.deep_agent.services.llm_factory.OpenAI")
def test_with_patch(mock_openai_class):
    """Patch replaces OpenAI class globally."""
    # OpenAI is mocked everywhere during this test
    agent = create_agent()
    assert mock_openai_class.called
```

**Advantages**:
- Automatic patching during test execution
- Works with imports/global state
- Cleans up automatically

**Disadvantages**:
- Can be confusing with multiple patches
- Order matters with multiple decorators
- Harder to debug import issues

### Pytest Fixtures (Recommended)

**Use when**: Reusing mocks across multiple tests

```python
# tests/conftest.py
@pytest.fixture
def mock_openai_client():
    """Reusable OpenAI client mock."""
    with patch("backend.deep_agent.services.llm_factory.OpenAI") as mock:
        mock.return_value = MagicMock()
        yield mock.return_value

# tests/test_agent.py
def test_agent_1(mock_openai_client):
    """Fixture automatically injected."""
    pass

def test_agent_2(mock_openai_client):
    """Fresh mock instance for each test."""
    pass
```

**Advantages**:
- **Best practice for pytest**
- Centralized, reusable mocks
- Automatic dependency injection
- Composable (fixtures can use other fixtures)
- Clear test dependencies

**Disadvantages**:
- Requires fixture definition upfront
- Slightly more boilerplate

### Decision Matrix

| Scenario | Use | Example |
|----------|-----|---------|
| One-off mock in single test | `Mock()` | `mock_obj = Mock(return_value=42)` |
| Replace import/global | `@patch` | `@patch("module.Class")` |
| Reusable across tests | `@pytest.fixture` | `def mock_service(): ...` |
| Complex setup/teardown | `@pytest.fixture` | `yield mock; cleanup()` |
| Test-specific config | Fixture + customize | `mock.method.return_value = custom` |

## Configuring Mock Responses

### Static Return Values

Simplest approach for fixed responses:

```python
mock.get_data.return_value = {"key": "value"}
```

### Dynamic Return Values with `side_effect`

Use `side_effect` for:
- Sequence of different return values
- Raising exceptions
- Dynamic behavior based on arguments

**Sequence of values**:
```python
mock.get_data.side_effect = ["first", "second", "third"]

assert mock.get_data() == "first"
assert mock.get_data() == "second"
assert mock.get_data() == "third"
```

**Raising exceptions**:
```python
mock.api_call.side_effect = ConnectionError("Network error")

with pytest.raises(ConnectionError):
    mock.api_call()
```

**Function for dynamic behavior**:
```python
def custom_behavior(arg):
    if arg == "special":
        return "special_result"
    return "default_result"

mock.process.side_effect = custom_behavior

assert mock.process("special") == "special_result"
assert mock.process("other") == "default_result"
```

### Async Mock Configuration

For async functions, use `AsyncMock`:

```python
from unittest.mock import AsyncMock

# AsyncMock for async functions
mock_async = AsyncMock()
mock_async.return_value = "result"

# Or with side_effect
async def async_behavior():
    return "async_result"

mock_async.side_effect = async_behavior

# Test usage
result = await mock_async()
assert result == "result"
```

### Verifying Mock Calls

**Basic assertions**:
```python
# Called at least once
mock.method.assert_called()

# Called exactly once
mock.method.assert_called_once()

# Called with specific arguments
mock.method.assert_called_with(arg1="value1", arg2="value2")

# Called once with specific arguments
mock.method.assert_called_once_with(arg1="value1")

# Never called
mock.method.assert_not_called()
```

**Inspecting calls**:
```python
# Number of calls
assert mock.method.call_count == 3

# All calls
assert len(mock.method.call_args_list) == 3

# Last call arguments
last_call = mock.method.call_args
assert last_call.args[0] == "expected"
assert last_call.kwargs["key"] == "value"

# Specific call
first_call = mock.method.call_args_list[0]
assert first_call.args == ("arg1",)
```

## Dependencies

The mocking strategy relies on:

- **unittest.mock**: Python standard library (no installation needed)
- **pytest**: Testing framework with fixture support
- **pytest-asyncio**: Async test support
- **pytest-mock**: Additional pytest mock utilities (optional but recommended)

Install optional dependencies:
```bash
poetry add --group dev pytest-mock
```

## Related Documentation

- **tests/conftest.py**: Central fixture definitions (primary mock location)
- **unittest.mock docs**: https://docs.python.org/3/library/unittest.mock.html
- **pytest fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **pytest-mock**: https://pytest-mock.readthedocs.io/
- **Testing Deep Agent One**: See test suite documentation in test directories

## Best Practices

### 1. Mock at the Boundary

Mock external dependencies, not internal business logic:

```python
# ✅ GOOD: Mock external API
@patch("backend.deep_agent.services.llm_factory.OpenAI")
def test_agent_logic(mock_openai):
    # Test actual agent logic with mocked OpenAI
    agent = create_agent()
    result = agent.process("input")
    assert result is not None

# ❌ BAD: Mock internal logic you should be testing
@patch("backend.deep_agent.agents.deep_agent.some_internal_function")
def test_agent(mock_internal):
    # This defeats the purpose - you're not testing anything!
    pass
```

### 2. Use `spec` for Type Safety

Prevent typos and ensure mock matches real interface:

```python
from backend.deep_agent.services.agent_service import AgentService

# ✅ GOOD: spec catches typos
mock = Mock(spec=AgentService)
mock.invoke()  # OK - method exists
mock.typo()    # AttributeError - method doesn't exist

# ❌ BAD: No spec allows any attribute
mock = Mock()
mock.typo()    # No error - allows bugs
```

### 3. Keep Mocks Simple

Avoid complex logic in mocks:

```python
# ✅ GOOD: Simple, predictable
mock.get_user.return_value = {"id": 1, "name": "Test"}

# ❌ BAD: Complex logic (just test the real thing!)
def complex_mock_logic(user_id):
    if user_id < 100:
        return compute_something(user_id)
    else:
        return query_database(user_id)

mock.get_user.side_effect = complex_mock_logic
```

### 4. One Mock Per Test Concern

Create focused mocks for specific scenarios:

```python
# ✅ GOOD: Separate fixtures for different scenarios
@pytest.fixture
def mock_openai_success():
    """Mock for successful completion."""
    # ... success response

@pytest.fixture
def mock_openai_error():
    """Mock for API error."""
    # ... error simulation

# ❌ BAD: One fixture trying to handle everything
@pytest.fixture
def mock_openai_all_cases(scenario):
    """Overly complex fixture."""
    if scenario == "success":
        # ...
    elif scenario == "error":
        # ...
    elif scenario == "timeout":
        # ...
    # Too complex!
```

### 5. Document Mock Behavior

Always document what the mock does:

```python
@pytest.fixture
def mock_service():
    """
    Mock service that simulates XYZ behavior.

    Returns:
        - Success response for valid input
        - Raises ValueError for empty input
        - Times out after 5 calls
    """
    mock = Mock()
    # ... configuration
    return mock
```

### 6. Verify Important Calls

Assert that mocks were called correctly:

```python
def test_agent_calls_openai(mock_openai_client):
    """Verify agent makes expected API call."""
    agent.invoke("Hello")

    # Verify call happened
    mock_openai_client.chat.completions.create.assert_called_once()

    # Verify call arguments
    call_args = mock_openai_client.chat.completions.create.call_args
    assert "Hello" in str(call_args.kwargs["messages"])
```

### 7. Reset Mocks Between Tests

Pytest fixtures are function-scoped by default (fresh instance per test), but if using session/module scope:

```python
@pytest.fixture(scope="module")
def mock_service():
    mock = Mock()
    yield mock
    # Reset for next test
    mock.reset_mock()
```

### 8. Avoid Mocking Python Builtins

Don't mock `len()`, `str()`, etc. - use real implementations:

```python
# ❌ BAD: Mocking builtins is fragile
@patch("builtins.len")
def test_with_mock_len(mock_len):
    mock_len.return_value = 5
    # Breaks everything!

# ✅ GOOD: Use real builtins, mock your own functions
def test_with_mock_data():
    mock_data = ["item1", "item2"]  # Real list
    assert len(mock_data) == 2      # Real len()
```

## Troubleshooting

### Mock Not Being Used

**Problem**: Test calls real API despite mock
**Solution**: Check patch target is correct

```python
# ❌ WRONG: Patching where it's defined
@patch("openai.OpenAI")  # Wrong if OpenAI is imported elsewhere

# ✅ CORRECT: Patch where it's imported
@patch("backend.deep_agent.services.llm_factory.OpenAI")  # Where it's used
```

### AttributeError on Mock

**Problem**: Mock raises AttributeError for method call
**Solution**: Use `spec` or configure attribute

```python
# Problem
mock = Mock()
mock.get_data()  # Works, but...
mock.get_data.return_value  # AttributeError

# Solution 1: Configure properly
mock.get_data.return_value = "data"

# Solution 2: Use MagicMock
mock = MagicMock()  # More permissive
```

### Async Mock Not Awaiting

**Problem**: `RuntimeWarning: coroutine 'AsyncMock' was never awaited`
**Solution**: Use `AsyncMock` for async functions

```python
# ❌ WRONG: Mock for async function
mock = Mock()
async def test():
    await mock.async_func()  # Warning!

# ✅ CORRECT: AsyncMock for async
mock = AsyncMock()
async def test():
    await mock.async_func()  # Works!
```

### Mock Call Count Wrong

**Problem**: `assert_called_once()` fails but mock was called
**Solution**: Mock not being reset between tests

```python
# Problem: Mock called in previous test
def test_1(mock_service):
    mock_service.call()

def test_2(mock_service):
    mock_service.call()
    mock_service.assert_called_once()  # Fails! (called twice total)

# Solution: Use function-scoped fixtures (default)
@pytest.fixture  # Fresh mock per test
def mock_service():
    return Mock()
```

---

## Summary

The Deep Agent One test suite uses pytest fixtures as the primary mocking mechanism, centralized in `tests/conftest.py`. This approach provides:

✅ **Consistency**: All tests use same mock implementations
✅ **Simplicity**: Automatic dependency injection via pytest
✅ **Reusability**: Fixtures compose and extend easily
✅ **Maintainability**: Centralized definitions, easy to update
✅ **Speed**: Fast, deterministic tests without external dependencies
✅ **Cost Control**: No charges from paid APIs during testing

Follow the guidelines in this document to create effective mocks that improve test quality, speed, and reliability.
