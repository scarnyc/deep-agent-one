# Testing Guide

Deep Agent AGI follows **Test-Driven Development (TDD)** principles with comprehensive test coverage. This guide explains how to run, write, and maintain tests.

---

## Table of Contents

- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [Continuous Integration](#continuous-integration)
- [Best Practices](#best-practices)

---

## Test Structure

Tests are organized by type and scope:

```
tests/
├── unit/                       # Unit tests (isolated)
│   ├── test_agents/
│   │   ├── test_checkpointer.py
│   │   ├── test_deep_agent.py
│   │   ├── test_prompts.py
│   │   └── test_reasoning_router.py
│   ├── test_models/
│   │   ├── test_agents.py
│   │   ├── test_chat.py
│   │   └── test_gpt5.py
│   ├── test_services/
│   │   └── test_llm_factory.py
│   ├── test_tools/
│   │   └── test_web_search.py
│   ├── test_integrations/
│   │   └── test_langsmith.py
│   ├── test_config.py
│   ├── test_errors.py
│   └── test_logging.py
├── integration/                # Integration tests (multiple components)
│   ├── test_agent_workflows/
│   │   └── test_agent_service.py
│   ├── test_api_endpoints/
│   │   ├── test_chat.py
│   │   ├── test_chat_stream.py
│   │   ├── test_agents.py
│   │   ├── test_websocket.py
│   │   └── test_main.py
│   └── test_mcp_integration/
│       └── test_perplexity.py
├── e2e/                        # End-to-end tests (complete workflows)
│   ├── test_complete_workflows/
│   │   ├── test_basic_chat.py
│   │   ├── test_hitl_workflow.py
│   │   └── test_tool_usage.py
│   ├── test_reasoning_scenarios/
│   └── test_user_journeys/
├── ui/                         # Frontend UI tests (Playwright)
│   ├── test_agent_state.py
│   └── test_websocket_connection.py
├── fixtures/                   # Test fixtures
│   └── mock_responses/
├── mocks/                      # Mock implementations
└── conftest.py                 # Shared fixtures
```

### Test Categories

| Category | Purpose | Mocking | Example |
|----------|---------|---------|---------|
| **Unit** | Test individual functions/classes in isolation | Heavy | `test_models/test_chat.py` |
| **Integration** | Test multiple components working together | Moderate | `test_api_endpoints/test_chat.py` |
| **E2E** | Test complete user workflows end-to-end | Minimal | `test_complete_workflows/test_basic_chat.py` |
| **UI** | Test frontend components with Playwright | Browser | `test_ui/test_agent_state.py` |

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend/deep_agent

# Run specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Comprehensive Test Suite

```bash
# Run full suite with reports
./scripts/test.sh
```

This generates:
- **HTML Test Report:** `reports/test_report.html`
- **Coverage Report:** `reports/coverage/index.html`
- **JSON Report:** `reports/report.json`

### Run Specific Tests

```bash
# Run specific file
pytest tests/unit/test_models/test_chat.py

# Run specific test class
pytest tests/unit/test_models/test_chat.py::TestChatRequest

# Run specific test method
pytest tests/unit/test_models/test_chat.py::TestChatRequest::test_valid_chat_request

# Run tests matching pattern
pytest -k "test_chat"
```

### Run Tests with Options

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run tests in parallel (faster)
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

### Coverage Options

```bash
# Coverage with missing lines
pytest --cov=backend/deep_agent --cov-report=term-missing

# HTML coverage report
pytest --cov=backend/deep_agent --cov-report=html

# Coverage for specific module
pytest --cov=backend/deep_agent/models tests/unit/test_models/

# Fail if coverage below threshold
pytest --cov=backend/deep_agent --cov-fail-under=80
```

### UI Tests (Playwright)

```bash
# Install Playwright browsers (first time)
npx playwright install

# Run UI tests (requires frontend running)
npm run dev  # In separate terminal
pytest tests/ui/ -v

# Run with headed browser (see what's happening)
pytest tests/ui/ --headed

# Debug mode
pytest tests/ui/ --debug
```

---

## Writing Tests

### TDD Workflow

1. **Write test first** (Red)
2. **Write minimal code to pass** (Green)
3. **Refactor** (Refactor)

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data and mocks
    user_input = "Hello, agent!"
    expected_output = "Hello, user!"

    # Act - Execute the code being tested
    result = process_message(user_input)

    # Assert - Verify the result
    assert result == expected_output
```

### Unit Test Example

```python
# tests/unit/test_models/test_chat.py

import pytest
from pydantic import ValidationError
from backend.deep_agent.models.chat import ChatRequest, ChatResponse

class TestChatRequest:
    """Unit tests for ChatRequest model."""

    def test_valid_chat_request(self):
        """Test creating a valid chat request."""
        # Arrange
        data = {
            "message": "Hello",
            "thread_id": "thread-001"
        }

        # Act
        request = ChatRequest(**data)

        # Assert
        assert request.message == "Hello"
        assert request.thread_id == "thread-001"
        assert request.metadata is None

    def test_empty_message_raises_validation_error(self):
        """Test that empty message raises validation error."""
        # Arrange
        data = {
            "message": "",
            "thread_id": "thread-001"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(**data)

        assert "message" in str(exc_info.value)

    def test_message_too_long_raises_error(self):
        """Test that message exceeding max length raises error."""
        # Arrange
        data = {
            "message": "A" * 10001,  # Max is 10000
            "thread_id": "thread-001"
        }

        # Act & Assert
        with pytest.raises(ValidationError):
            ChatRequest(**data)
```

### Integration Test Example

```python
# tests/integration/test_api_endpoints/test_chat.py

import pytest
from fastapi.testclient import TestClient
from backend.deep_agent.main import app

@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)

class TestChatEndpoint:
    """Integration tests for /api/v1/chat endpoint."""

    def test_chat_endpoint_success(self, client):
        """Test successful chat request."""
        # Arrange
        request_data = {
            "message": "Hello, how can you help?",
            "thread_id": "test-thread-001"
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert data["thread_id"] == "test-thread-001"
        assert data["status"] == "success"

    def test_chat_endpoint_validation_error(self, client):
        """Test chat endpoint with invalid input."""
        # Arrange
        invalid_request = {
            "message": "",  # Empty message
            "thread_id": "test-thread-002"
        }

        # Act
        response = client.post("/api/v1/chat", json=invalid_request)

        # Assert
        assert response.status_code == 422
```

### E2E Test Example

```python
# tests/e2e/test_complete_workflows/test_basic_chat.py

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Create test client."""
    from backend.deep_agent.main import app
    return TestClient(app)

class TestBasicChatWorkflow:
    """E2E tests for complete chat workflow."""

    def test_complete_chat_request_response_cycle(self, client):
        """
        Test complete chat workflow from request to response.

        Flow:
        1. Client sends chat request
        2. FastAPI validates and processes request
        3. AgentService creates agent
        4. Agent invokes with message
        5. Response returned to client
        """
        # Arrange
        request_data = {
            "message": "Hello, how can you help me?",
            "thread_id": "e2e-test-thread-001"
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert - Response structure
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "thread_id" in data
        assert data["status"] == "success"

        # Assert - Response values
        assert data["thread_id"] == "e2e-test-thread-001"
        assert len(data["messages"]) >= 1
```

### UI Test Example (Playwright)

```python
# tests/ui/test_agent_state.py

import pytest
from playwright.sync_api import Page, expect

class TestAgentStateManagement:
    """UI tests for agent state management."""

    def test_create_new_thread(self, page: Page):
        """Test creating a new conversation thread."""
        # Arrange: Navigate to chat page
        page.goto("http://localhost:3000/chat")

        # Act: Create a new thread (via UI or programmatically)
        # The store should automatically create a thread on mount

        # Assert: Thread ID exists in UI
        thread_id_element = page.locator('[data-testid="thread-id"]')
        expect(thread_id_element).to_be_visible(timeout=5000)
```

### Mocking

```python
from unittest.mock import AsyncMock, MagicMock, patch

# Mock external API
@patch('backend.deep_agent.services.llm_factory.ChatOpenAI')
def test_with_mocked_openai(mock_openai_class):
    mock_llm = MagicMock()
    mock_openai_class.return_value = mock_llm
    # Test code...

# Mock async function
@pytest.mark.asyncio
async def test_async_function():
    mock_service = AsyncMock()
    mock_service.process.return_value = {"result": "success"}
    result = await mock_service.process()
    assert result["result"] == "success"

# Mock environment variables
@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_with_env_var():
    # Test code...
```

### Fixtures

```python
# conftest.py

import pytest
from backend.deep_agent.config.settings import get_settings

@pytest.fixture
def test_settings():
    """Provide test settings."""
    settings = get_settings()
    settings.env = "test"
    return settings

@pytest.fixture
async def mock_agent_service():
    """Provide mocked agent service."""
    from unittest.mock import AsyncMock
    service = AsyncMock()
    service.chat.return_value = {"response": "test"}
    return service
```

---

## Test Coverage

### Current Coverage

**Phase 0 MVP:** 77.02% (287 tests passing)

### Coverage Goals

- **Overall:** ≥80% (Phase 0 requirement)
- **Critical Modules:** ≥90% (models, services, API)
- **New Code:** 100% (all new features)

### Check Coverage

```bash
# Terminal report
pytest --cov=backend/deep_agent --cov-report=term-missing

# HTML report (easier to browse)
pytest --cov=backend/deep_agent --cov-report=html
open reports/coverage/index.html
```

### Coverage Reports

Coverage reports show:
- **Stmts** - Total statements
- **Miss** - Missed statements
- **Cover** - Coverage percentage
- **Missing** - Line numbers not covered

Example:

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend/deep_agent/models/chat.py          97     13  86.60%  66, 118, 146
backend/deep_agent/services/llm.py         45      5  88.89%  23-27
```

### Improving Coverage

1. **Identify gaps:**
   ```bash
   pytest --cov=backend/deep_agent --cov-report=term-missing
   ```

2. **Write tests for missing lines:**
   Focus on:
   - Error handling paths
   - Edge cases
   - Conditional branches

3. **Run again to verify:**
   ```bash
   pytest --cov=backend/deep_agent --cov-fail-under=80
   ```

---

## Continuous Integration

### Pre-Commit Workflow

**MANDATORY before EVERY commit:**

1. **Run testing-expert agent** (if tests written)
2. **Run code-review-expert agent** (for all code)
3. **Fix issues or log to GITHUB_ISSUES.md**
4. **Only commit after approval**

See CLAUDE.md:743-844 for complete pre-commit workflow.

### GitHub Actions

Tests run automatically on:
- Every push
- Every pull request
- Daily schedule

**Workflow:** `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: pytest --cov=backend/deep_agent --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Best Practices

### DO:

✅ **Write tests first** (TDD)
✅ **Follow AAA pattern** (Arrange, Act, Assert)
✅ **One assertion per test** (when possible)
✅ **Use descriptive test names** (`test_empty_message_raises_validation_error`)
✅ **Test edge cases** (empty, null, max length, etc.)
✅ **Mock external dependencies** (APIs, databases)
✅ **Keep tests isolated** (no shared state)
✅ **Use fixtures** for common setup
✅ **Document complex tests** (docstrings)
✅ **Run tests before committing**

### DON'T:

❌ **Test implementation details** (test behavior, not internals)
❌ **Skip error cases** (always test failure paths)
❌ **Use hardcoded values** (use fixtures/constants)
❌ **Test external APIs** (mock them)
❌ **Write flaky tests** (ensure determinism)
❌ **Commit without tests** (TDD required)
❌ **Ignore test failures** (fix or document)

### Test Naming Conventions

```python
# Good
def test_create_agent_with_valid_settings():
    ...

def test_empty_message_raises_validation_error():
    ...

def test_chat_endpoint_returns_200_on_success():
    ...

# Bad
def test_agent():  # Too vague
    ...

def test_1():  # No context
    ...

def testChatWorks():  # Not snake_case
    ...
```

### Test Organization

```python
# Group related tests in classes
class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_valid_chat_request(self):
        ...

    def test_invalid_chat_request(self):
        ...

class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_valid_chat_response(self):
        ...
```

---

## Troubleshooting

### Tests Fail Locally But Pass in CI

**Cause:** Environment differences
**Solution:**
```bash
# Match CI environment
ENV=test pytest

# Check Python version
python --version  # Should match CI
```

### Import Errors

**Cause:** Python path not set
**Solution:**
```bash
# Ensure you're in project root
cd /path/to/deep-agent-agi

# Activate virtual environment
source venv/bin/activate

# Install in editable mode
pip install -e .
```

### Async Test Failures

**Cause:** Missing `@pytest.mark.asyncio`
**Solution:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

### Playwright Tests Fail

**Cause:** Browsers not installed
**Solution:**
```bash
npx playwright install
npx playwright install-deps
```

### Coverage Not Updating

**Cause:** `.coverage` file cached
**Solution:**
```bash
rm .coverage
pytest --cov=backend/deep_agent
```

---

## Additional Resources

- **CLAUDE.md** - TDD workflow and pre-commit requirements
- **pytest documentation** - https://docs.pytest.org/
- **Playwright documentation** - https://playwright.dev/python/
- **Coverage.py** - https://coverage.readthedocs.io/

---

## Getting Help

- **Check test output carefully** - Error messages are descriptive
- **Review existing tests** - Find similar test for examples
- **Run with `-vv`** - More verbose output
- **Use `--pdb`** - Drop into debugger on failure
- **Ask in discussions** - https://github.com/yourusername/deep-agent-agi/discussions
