# Unit Tests

Isolated unit tests for Deep Agent AGI components. Fast, focused tests with extensive mocking.

## Purpose

Unit tests validate individual functions, classes, and methods in isolation from external dependencies (databases, APIs, file systems). They execute quickly (<1s per test) and provide immediate feedback during development.

**Key Characteristics:**
- **Isolated**: Each test focuses on a single unit of code
- **Fast**: Complete test suite runs in seconds
- **Mocked**: External dependencies are mocked (OpenAI API, database, file system)
- **Deterministic**: Same input always produces same output
- **High Coverage**: Target 90%+ coverage for critical modules

## Directory Structure

```
tests/unit/
├── README.md                           # This file
├── __init__.py                         # Test package marker
├── test_config.py                      # Settings and configuration
├── test_errors.py                      # Custom exception classes
├── test_logging.py                     # Structured logging
├── test_agents/                        # Agent-related tests
│   ├── __init__.py
│   ├── test_checkpointer.py           # State persistence
│   ├── test_deep_agent.py             # Agent creation
│   ├── test_prompts.py                # Prompt management
│   └── test_reasoning_router.py       # Reasoning effort routing
├── test_api/                          # API endpoint tests (placeholder)
│   └── __init__.py
├── test_integrations/                 # Third-party integrations
│   ├── __init__.py
│   └── test_langsmith.py              # LangSmith tracing
├── test_models/                       # Pydantic models
│   ├── __init__.py
│   ├── test_agents.py                 # Agent-related models
│   ├── test_chat.py                   # Chat API models
│   └── test_gpt5.py                   # GPT-5 configuration
├── test_services/                     # Service layer
│   ├── __init__.py
│   └── test_llm_factory.py            # LLM creation factory
└── test_tools/                        # Agent tools
    ├── __init__.py
    ├── test_prompt_optimization.py    # Prompt optimization tool
    └── test_web_search.py             # Web search tool

```

**Structure mirrors backend codebase:**
- `tests/unit/test_agents/` → `backend/deep_agent/agents/`
- `tests/unit/test_models/` → `backend/deep_agent/models/`
- `tests/unit/test_tools/` → `backend/deep_agent/tools/`

## Running Unit Tests

### All unit tests
```bash
pytest tests/unit/ -v
```

### Specific test file
```bash
pytest tests/unit/test_config.py -v
```

### Specific test class
```bash
pytest tests/unit/test_config.py::TestSettings -v
```

### Specific test function
```bash
pytest tests/unit/test_config.py::TestSettings::test_settings_loads_from_env -v
```

### With coverage report
```bash
pytest tests/unit/ --cov=backend/deep_agent --cov-report=html
```

### Only failed tests
```bash
pytest tests/unit/ --lf  # Last failed
pytest tests/unit/ --ff  # Failed first
```

### With output capture disabled (see print statements)
```bash
pytest tests/unit/ -v -s
```

### Parallel execution (faster)
```bash
pytest tests/unit/ -n auto  # Uses pytest-xdist
```

## Writing Unit Tests

### Test Structure (AAA Pattern)

All tests follow the **Arrange-Act-Assert** pattern:

```python
def test_example_function():
    """
    Test example_function with valid input.

    Scenario:
        Call example_function with x=5

    Expected:
        Returns x * 2 = 10
    """
    # Arrange - Set up test data and mocks
    x = 5
    expected = 10

    # Act - Execute the function under test
    result = example_function(x)

    # Assert - Verify the result
    assert result == expected
```

### Naming Convention

Test names clearly describe what is being tested:

```python
def test_<function_name>_<scenario>_<expected_outcome>():
    pass

# Examples:
def test_create_agent_with_valid_settings_returns_compiled_graph():
    pass

def test_web_search_with_empty_query_returns_error_message():
    pass
```

### Docstring Format (Google Style)

```python
def test_example():
    """
    Brief one-line description of what's being tested.

    Scenario:
        Detailed description of the test scenario

    Expected:
        Expected outcome or behavior
    """
    pass
```

### Mocking Guidelines

#### Mock External APIs

```python
from unittest.mock import Mock, AsyncMock, patch

@patch("backend.deep_agent.tools.web_search.PerplexityClient")
def test_search_with_mock(MockClient):
    """Test web search with mocked Perplexity client."""
    # Arrange
    mock_client = Mock()
    mock_client.search = AsyncMock(return_value={"results": []})
    MockClient.return_value = mock_client

    # Act & Assert
    ...
```

#### Mock Settings

```python
from unittest.mock import Mock
from backend.deep_agent.config.settings import Settings

@pytest.fixture
def mock_settings():
    """Fixture providing mocked Settings."""
    settings = Mock(spec=Settings)
    settings.OPENAI_API_KEY = "test-key-123"
    settings.GPT5_MODEL_NAME = "gpt-5"
    return settings
```

#### Mock Async Functions

```python
from unittest.mock import AsyncMock

mock_checkpointer = AsyncMock()
mock_checkpointer.create_checkpointer = AsyncMock(return_value=mock_instance)
```

### Fixtures

Use pytest fixtures for reusable test data and mocks:

```python
@pytest.fixture
def mock_llm():
    """Fixture providing mocked ChatOpenAI instance."""
    llm = Mock(spec=ChatOpenAI)
    llm.model_name = "gpt-5"
    return llm

def test_using_fixture(mock_llm):
    """Test that uses mock_llm fixture."""
    assert mock_llm.model_name == "gpt-5"
```

**Common fixtures are defined in `tests/conftest.py`** (shared across all test types).

### Testing Async Code

Use `@pytest.mark.asyncio` for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test asynchronous function."""
    # Arrange
    mock_checkpointer = AsyncMock()

    # Act
    result = await checkpointer.create_checkpointer()

    # Assert
    assert result is not None
```

### Error Testing

Test that errors are raised correctly:

```python
def test_invalid_input_raises_error():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="API key is required"):
        create_llm(api_key="")
```

### Pydantic Model Testing

Test validation, serialization, and deserialization:

```python
def test_chat_request_validation():
    """Test ChatRequest validates required fields."""
    # Valid
    req = ChatRequest(message="Hello", thread_id="123")
    assert req.message == "Hello"

    # Invalid - missing required field
    with pytest.raises(ValidationError):
        ChatRequest(message="Hello")  # Missing thread_id
```

## Coverage Requirements

**Target: 90%+ coverage for critical modules**

### Critical Modules (Must have ≥90% coverage)
- `backend/deep_agent/agents/` - Agent creation, prompts, checkpointing
- `backend/deep_agent/models/` - Pydantic models
- `backend/deep_agent/services/` - LLM factory
- `backend/deep_agent/tools/` - Agent tools
- `backend/deep_agent/core/` - Errors, logging, configuration

### Check Coverage

```bash
# Generate HTML coverage report
pytest tests/unit/ --cov=backend/deep_agent --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Report Interpretation

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
backend/deep_agent/agents/deep_agent.py    45      2    96%
backend/deep_agent/tools/web_search.py     38      5    87%
-----------------------------------------------------------
TOTAL                                     500     25    95%
```

- **Stmts**: Total statements in file
- **Miss**: Statements not covered by tests
- **Cover**: Percentage covered

**Goal: Minimize "Miss" column for critical modules**

## Test Categories

### 1. Configuration Tests (`test_config.py`)
- Settings loading from environment variables
- Required field validation
- Default value application
- Singleton pattern (get_settings cache)

### 2. Error Handling Tests (`test_errors.py`)
- Custom exception classes
- Error message handling
- Inheritance chain validation
- Raise/catch behavior

### 3. Logging Tests (`test_logging.py`)
- Structured logging setup
- Log level configuration
- JSON vs. standard format
- Context field inclusion

### 4. Agent Tests (`test_agents/`)
- **Checkpointer**: State persistence, cleanup, resource management
- **Deep Agent**: Agent creation, LLM integration, checkpointer integration
- **Prompts**: Environment-based prompt selection, versioning
- **Reasoning Router**: Effort determination (Phase 0 always returns MEDIUM)

### 5. Model Tests (`test_models/`)
- **Chat**: Request/response validation, serialization
- **GPT-5**: Configuration validation, reasoning effort, verbosity
- **Agents**: AgentRequest/Response models

### 6. Service Tests (`test_services/`)
- **LLM Factory**: ChatOpenAI creation, configuration, reasoning effort

### 7. Tool Tests (`test_tools/`)
- **Web Search**: Query handling, result formatting, error handling
- **Prompt Optimization**: Tool signature validation (Phase 1)

### 8. Integration Tests (`test_integrations/`)
- **LangSmith**: Environment variable setup, tracing configuration

## Common Patterns

### 1. Testing with monkeypatch (Environment Variables)

```python
def test_with_env_var(monkeypatch):
    """Test function that reads environment variable."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    settings = Settings()
    assert settings.OPENAI_API_KEY == "test-key"
```

### 2. Testing Pydantic Validation

```python
def test_pydantic_validation():
    """Test Pydantic model validation."""
    # Valid
    config = GPT5Config(reasoning_effort="medium")
    assert config.reasoning_effort == ReasoningEffort.MEDIUM

    # Invalid
    with pytest.raises(ValidationError):
        GPT5Config(reasoning_effort="invalid")
```

### 3. Testing Async Context Managers

```python
@pytest.mark.asyncio
async def test_async_context_manager():
    """Test CheckpointerManager as async context manager."""
    async with CheckpointerManager(settings=mock_settings) as manager:
        checkpointer = await manager.create_checkpointer()
        assert checkpointer is not None
```

### 4. Testing Tool Calls (LangChain)

```python
@pytest.mark.asyncio
async def test_tool_invocation():
    """Test LangChain tool invocation."""
    from backend.deep_agent.tools.web_search import web_search

    result = await web_search.ainvoke({"query": "python tutorial"})
    assert isinstance(result, str)
    assert "python" in result.lower()
```

### 5. Testing Error Handling

```python
@pytest.mark.asyncio
async def test_error_handling():
    """Test that ConnectionError is handled gracefully."""
    with patch("backend.deep_agent.tools.web_search.PerplexityClient") as MockClient:
        mock_client = Mock()
        mock_client.search = AsyncMock(side_effect=ConnectionError("Failed"))
        MockClient.return_value = mock_client

        result = await web_search.ainvoke({"query": "test"})

        assert "error" in result.lower()
```

### 6. Testing Logging

```python
def test_logging_behavior(capsys):
    """Test that function logs expected message."""
    logger = get_logger("test")
    logger.info("test message", request_id="123")

    captured = capsys.readouterr()
    assert "test message" in captured.out
```

## Dependencies

### Test Libraries
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.4.2"              # Test framework
pytest-asyncio = "^0.25.4"     # Async test support
pytest-cov = "^7.0.1"          # Coverage reporting
pytest-mock = "^3.14.0"        # Enhanced mocking
```

### Mocking
- `unittest.mock`: Standard library mocking (Mock, AsyncMock, patch, MagicMock)
- `pytest-mock`: pytest integration for mocking

### Async Testing
- `pytest-asyncio`: Provides `@pytest.mark.asyncio` decorator
- `AsyncMock`: For mocking async functions

## Related Documentation

- **E2E Tests**: `/tests/e2e/README.md` - End-to-end workflow tests
- **Integration Tests**: `/tests/integration/README.md` - Component interaction tests
- **UI Tests**: `/tests/ui/README.md` - Playwright UI tests
- **Main Test Fixtures**: `/tests/conftest.py` - Shared fixtures and configuration
- **Phase 0 Testing Guide**: `/CLAUDE.md` - TDD workflow and testing requirements

## Best Practices

### 1. One Assertion Per Test (Guideline)
While not a hard rule, prefer focused tests:

```python
# Good - Focused test
def test_settings_loads_openai_key():
    """Test OPENAI_API_KEY loads from environment."""
    settings = Settings()
    assert settings.OPENAI_API_KEY == "test-key"

# Acceptable - Related assertions
def test_settings_loads_all_required_fields():
    """Test all required fields load from environment."""
    settings = Settings()
    assert settings.OPENAI_API_KEY is not None
    assert settings.GPT5_MODEL_NAME is not None
```

### 2. Use Descriptive Test Names
Test names should be self-documenting:

```python
# Good
def test_create_agent_with_missing_api_key_raises_value_error():
    pass

# Bad
def test_agent():
    pass
```

### 3. Mock at the Boundary
Mock external dependencies at the lowest level:

```python
# Good - Mock at API client level
@patch("backend.deep_agent.tools.web_search.PerplexityClient")
def test_search(MockClient):
    pass

# Bad - Mock internal implementation details
@patch("backend.deep_agent.tools.web_search._format_results")
def test_search(mock_format):
    pass
```

### 4. Test Edge Cases
Always test boundary conditions:

```python
def test_reasoning_router_empty_query():
    """Test with empty string."""
    pass

def test_reasoning_router_very_long_query():
    """Test with 10,000 word query."""
    pass
```

### 5. Use Fixtures for Reusable Mocks
Define fixtures in `conftest.py` or test files:

```python
@pytest.fixture
def mock_settings():
    """Fixture providing test settings."""
    return Mock(spec=Settings, OPENAI_API_KEY="test-key")
```

### 6. Keep Tests Independent
Each test should be runnable in isolation:

```python
# Good - Independent test
@pytest.fixture(autouse=True)
def clear_cache():
    """Clear settings cache before each test."""
    get_settings.cache_clear()

# Bad - Tests depend on execution order
def test_1_create_resource():
    global resource
    resource = create()

def test_2_use_resource():
    assert resource.exists()  # Depends on test_1
```

### 7. Test Behavior, Not Implementation
Focus on observable behavior:

```python
# Good - Tests behavior
def test_create_agent_returns_compiled_graph():
    """Test that create_agent returns CompiledStateGraph."""
    agent = await create_agent()
    assert isinstance(agent, CompiledStateGraph)

# Bad - Tests implementation details
def test_create_agent_calls_internal_setup():
    """Test that create_agent calls _setup_internal()."""
    with patch("backend.deep_agent.agents._setup_internal"):
        await create_agent()
        _setup_internal.assert_called_once()  # Implementation detail
```

### 8. Use Type Hints
Include type hints in test functions:

```python
def test_example(mock_settings: Settings) -> None:
    """Test with type hints for clarity."""
    pass
```

---

**Last Updated**: 2025-11-12
**Coverage**: 85% (Target: 90%+)
**Test Count**: 150+ unit tests
