# Tests

## Purpose

Comprehensive test suite for Deep Agent AGI covering unit tests, integration tests, end-to-end workflows, UI testing with Playwright, and research experiments.

## Directory Structure

```
tests/
├── unit/              # Unit tests (isolated, mocked dependencies)
│   ├── test_agents/       # Agent creation and configuration
│   ├── test_api/          # API endpoints and models
│   ├── test_config/       # Configuration management
│   ├── test_integrations/ # LangSmith, monitoring
│   ├── test_models/       # LLM models and reasoning
│   ├── test_services/     # Core business logic
│   └── test_tools/        # Individual tool implementations
├── integration/       # Integration tests (real components, mocked external services)
│   ├── test_agents/       # Agent workflows with tools
│   ├── test_api/          # API endpoint flows
│   ├── test_checkpointing/ # State persistence
│   ├── test_reasoning/    # Reasoning router integration
│   └── test_tools/        # Tool chain execution
├── e2e/               # End-to-end workflows (complete user journeys)
│   ├── test_complete_workflows/  # Full agent workflows
│   ├── test_hitl_workflows/      # Human-in-the-loop flows
│   └── test_websocket_flows/     # Real-time WebSocket flows
├── ui/                # UI tests with Playwright MCP
│   ├── test_chat_interface/      # Chat UI testing
│   ├── test_tool_transparency/   # Tool execution display
│   └── test_hitl_ui/             # HITL approval interface
├── experiments/       # Research and optimization experiments
│   ├── test_prompt_optimization/     # A/B testing, Opik integration
│   ├── test_reasoning_evaluation/   # Reasoning effort experiments
│   └── test_cost_analysis/          # Token usage and cost optimization
├── fixtures/          # Test fixtures and factory functions
├── mocks/             # Mock implementations
└── scripts/           # Test utilities and scripts
```

## Quick Start

### Run All Tests

```bash
pytest
```

### Run by Category

```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/           # E2E tests only
pytest tests/ui/            # UI tests only
pytest tests/experiments/   # Research experiments only
```

### Run with Coverage

```bash
pytest --cov=deep_agent --cov-report=html
```

### Run Specific Test

```bash
pytest tests/unit/test_agents/test_deep_agent.py::test_create_agent -v
```

### Run with Parallelization

```bash
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

## Testing Strategy

### Test Pyramid

- **Unit Tests (70%)**: Fast, isolated, extensive coverage
  - Test individual functions, classes, and methods
  - Mock all external dependencies
  - Execution time: <100ms per test
  - Coverage target: 90%+

- **Integration Tests (20%)**: Component interactions, mocked external services
  - Test interactions between internal components
  - Mock external APIs (OpenAI, Perplexity, LangSmith)
  - Execution time: <1s per test
  - Coverage target: 85%+

- **E2E Tests (8%)**: Complete workflows, minimal mocking
  - Test complete user journeys end-to-end
  - Mock only external API calls (to avoid costs)
  - Execution time: <5s per test
  - Coverage target: Critical paths only

- **UI Tests (2%)**: Critical user paths, Playwright automation
  - Test UI interactions and visual components
  - Focus on critical workflows (chat, HITL, tool transparency)
  - Execution time: <10s per test
  - Coverage target: Happy paths + critical errors

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Critical modules**: 90%+ coverage (agents, tools, API endpoints)
- **New code**: 100% coverage required (enforced in CI/CD)

## Test Markers

### Pytest Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.ui            # UI test
@pytest.mark.slow          # Slow test (>1s)
@pytest.mark.live_api      # Requires live API calls (not run in CI)
```

### Running Marked Tests

```bash
pytest -m unit                         # Unit tests only
pytest -m "not slow"                   # Exclude slow tests
pytest -m "integration and not slow"   # Fast integration tests
pytest -m live_api -v                  # Live API tests (costs money)
```

## Test Configuration

### pytest.ini

Located in project root, configures:
- Test discovery patterns (`test_*.py`, `*_test.py`)
- Coverage settings (source, omit patterns)
- Markers (unit, integration, e2e, ui, slow, live_api)
- Output format (verbose, color)
- Plugins (asyncio, html, cov)

### conftest.py

Shared fixtures for all tests:
- **Directory fixtures**: `project_root`, `test_data_dir`, `temp_workspace`
- **Mock service fixtures**: `mock_openai_client`, `mock_langsmith`, `mock_perplexity_search`
- **Test data fixtures**: `sample_chat_message`, `sample_chat_response`, `sample_tool_calls`
- **Async support**: `event_loop` fixture
- **Pytest hooks**: `pytest_configure` for marker registration

### .coveragerc

Coverage configuration:
- Source directories to measure
- Files/directories to omit (tests, migrations, __init__.py)
- Report generation settings (HTML, terminal)

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
- Runs on every PR and push to main
- Parallel test execution across multiple Python versions
- Coverage reports uploaded to Codecov
- Blocks merge if coverage <80%
- Blocks merge if any test fails
```

### Pre-Commit Hooks

```bash
# Run before every commit
./scripts/test.sh                    # All tests
./scripts/security_scan.sh           # TheAuditor scan
```

### Quality Gates

- **Coverage**: ≥80% overall, ≥90% for critical modules
- **Tests**: 100% pass rate
- **Security**: Zero critical vulnerabilities (TheAuditor)
- **Type checking**: Zero mypy errors
- **Linting**: Zero ruff errors

## Dependencies

### Core Testing

- **pytest**: Test framework and runner
- **pytest-cov**: Coverage measurement and reporting
- **pytest-asyncio**: Async test support
- **pytest-html**: HTML test reports
- **pytest-xdist**: Parallel test execution

### UI Testing

- **playwright**: Browser automation
- **@modelcontextprotocol/server-playwright**: MCP integration

### Mocking & Fixtures

- **unittest.mock**: Python's built-in mocking
- **pytest-mock**: Pytest plugin for easier mocking
- **factory_boy**: Test fixture factories (optional)

### Performance & Load Testing

- **k6**: Load testing tool (for performance tests)
- **locust**: Alternative load testing (optional)

## Related Documentation

- [Unit Tests](unit/README.md) - Detailed unit testing guide
- [Integration Tests](integration/README.md) - Integration testing patterns
- [E2E Tests](e2e/README.md) - End-to-end workflow testing
- [UI Tests](ui/README.md) - Playwright UI testing guide
- [Fixtures](fixtures/README.md) - Test fixture documentation
- [Mocks](mocks/README.md) - Mock implementation guide
- [Experiments](experiments/README.md) - Research experiments

## Best Practices

### 1. Follow AAA Pattern

```python
def test_example():
    # Arrange: Set up test data and mocks
    input_data = {"key": "value"}
    mock_service = MagicMock()

    # Act: Execute the code under test
    result = my_function(input_data, mock_service)

    # Assert: Verify the outcome
    assert result == expected_value
    mock_service.method.assert_called_once()
```

### 2. Use Descriptive Test Names

```python
# Good
def test_agent_invokes_web_search_tool_when_query_requires_current_information():
    ...

# Bad
def test_agent():
    ...
```

### 3. Mock External Dependencies

```python
@patch("backend.deep_agent.tools.web_search.PerplexityClient")
def test_web_search_tool(mock_client):
    # Mock external API to avoid costs and flakiness
    mock_client.return_value.search.return_value = "Mock results"
    ...
```

### 4. Test Error Cases

```python
def test_agent_handles_api_rate_limit_error():
    # Test error handling, not just happy paths
    with pytest.raises(RateLimitError):
        agent.invoke_with_rate_limit()
```

### 5. Keep Tests Independent

```python
# Each test should be runnable in isolation
def test_first():
    # Don't rely on state from test_second
    ...

def test_second():
    # Don't rely on state from test_first
    ...
```

### 6. Use Fixtures for Setup

```python
@pytest.fixture
def sample_agent():
    """Reusable agent fixture."""
    return create_agent(config=test_config)

def test_agent_invoke(sample_agent):
    # Use fixture instead of duplicating setup
    result = sample_agent.invoke("Hello")
    assert result
```

### 7. Aim for Fast Execution

- Unit tests: <100ms each
- Integration tests: <1s each
- E2E tests: <5s each
- UI tests: <10s each
- **Total suite: <5min** (enables fast feedback loops)

### 8. Write Tests First (TDD)

```python
# 1. Write test (fails)
def test_new_feature():
    result = new_feature()
    assert result == expected

# 2. Implement feature (test passes)
def new_feature():
    return expected

# 3. Refactor (test still passes)
```

## Troubleshooting

### Common Issues

#### Issue: Tests fail with `ImportError`

```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Install dependencies
poetry install
```

#### Issue: Coverage below 80%

```bash
# Find uncovered lines
pytest --cov=deep_agent --cov-report=term-missing

# Generate HTML report for detailed view
pytest --cov=deep_agent --cov-report=html
open htmlcov/index.html
```

#### Issue: Slow test execution

```bash
# Identify slow tests
pytest --durations=10

# Run in parallel
pytest -n auto

# Skip slow tests during development
pytest -m "not slow"
```

#### Issue: Flaky tests

```python
# Use retries for flaky tests (network, timing issues)
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_network_operation():
    ...
```

#### Issue: Async test failures

```python
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Mark async tests correctly
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result
```

#### Issue: Mock not working as expected

```python
# Verify patch path matches import path
# Wrong: @patch("backend.services.OpenAI")
# Right: @patch("backend.deep_agent.services.llm_factory.OpenAI")

# Use `spec=True` to catch attribute errors
mock = MagicMock(spec=RealClass)
```

### Debugging Tests

```bash
# Run with verbose output
pytest -vv

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Run specific test with logging
pytest tests/unit/test_agents/test_deep_agent.py::test_create_agent -v -s
```

### Getting Help

- **Project Documentation**: See `CLAUDE.md` for development guide
- **Test-Specific Questions**: Check subdirectory READMEs (unit/, integration/, etc.)
- **Pytest Documentation**: https://docs.pytest.org/
- **Playwright Documentation**: https://playwright.dev/python/

## Performance Benchmarks

### Expected Execution Times

| Test Category | Count | Avg Time/Test | Total Time |
|---------------|-------|---------------|------------|
| Unit          | ~150  | <100ms        | <15s       |
| Integration   | ~40   | <1s           | <40s       |
| E2E           | ~15   | <5s           | <75s       |
| UI            | ~5    | <10s          | <50s       |
| **Total**     | ~210  | ~850ms        | <3min      |

### Optimization Tips

1. **Use parallel execution**: `pytest -n auto`
2. **Skip slow tests in dev**: `pytest -m "not slow"`
3. **Run subset during development**: `pytest tests/unit/`
4. **Use `--last-failed` to rerun failures**: `pytest --lf`
5. **Cache test results**: `pytest --cache-clear` (when needed)

## Contributing

### Adding New Tests

1. **Choose appropriate directory**: unit/, integration/, e2e/, ui/
2. **Follow naming convention**: `test_*.py` or `*_test.py`
3. **Use AAA pattern**: Arrange, Act, Assert
4. **Add markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
5. **Mock external dependencies**: Avoid live API calls
6. **Ensure 100% coverage** for new code
7. **Run pre-commit checks**: `./scripts/test.sh`
8. **Update documentation**: Add new test to relevant README

### Test Review Checklist

Before committing tests:

- [ ] Tests follow AAA pattern
- [ ] Descriptive test names (what, when, expected)
- [ ] External dependencies mocked
- [ ] Error cases covered
- [ ] Independent tests (no shared state)
- [ ] Fast execution (<5s for non-E2E)
- [ ] Proper markers added
- [ ] Coverage ≥80% (use `--cov`)
- [ ] No flaky tests (run 3x to verify)
- [ ] Documentation updated

### Running Pre-Commit Agents

**MANDATORY**: Run testing-expert and code-review-expert before committing:

```bash
# 1. Run testing-expert (for test code)
# Use Task tool with testing-expert subagent
# Verifies: AAA pattern, coverage, edge cases, mocking

# 2. Run code-review-expert (for implementation code)
# Use Task tool with code-review-expert subagent
# Verifies: Type hints, error handling, security, architecture

# 3. Only after approval: Commit
git add tests/
git commit -m "test(phase-0): add comprehensive test suite"
```

## Maintenance

### Regular Tasks

- **Weekly**: Review test coverage reports, identify gaps
- **Monthly**: Update dependencies, run live API tests (Phase 0.5)
- **Quarterly**: Review and refactor slow/flaky tests
- **Annually**: Audit entire test suite for obsolete tests

### Metrics to Track

- **Coverage**: Overall, per-module, per-test-category
- **Execution time**: Total, per-test-category, slowest tests
- **Flakiness**: Tests that fail intermittently
- **Test count**: Growth over time, by category
- **CI/CD metrics**: Pass rate, average duration, failure patterns

## Roadmap

### Phase 0 (Current)

- [x] Unit test suite (80%+ coverage)
- [x] Integration test suite
- [x] E2E test suite
- [ ] UI test suite (Playwright)
- [x] Test reporting (HTML, coverage)
- [x] CI/CD integration (GitHub Actions)

### Phase 0.5 (Next)

- [ ] Live API integration tests (`tests/live_api/`)
- [ ] Cost-optimized test execution
- [ ] Automated smoke tests on staging

### Phase 1 (Future)

- [ ] Performance testing (k6)
- [ ] Load testing (concurrent users)
- [ ] Security testing (TheAuditor integration)
- [ ] Visual regression testing (Playwright screenshots)

### Phase 2 (Future)

- [ ] Chaos engineering tests (fault injection)
- [ ] Contract testing (API versioning)
- [ ] Property-based testing (hypothesis)
- [ ] Mutation testing (mutpy)

---

**Last Updated**: 2025-11-12
**Maintained By**: Deep Agent AGI Team
