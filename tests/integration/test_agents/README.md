# Integration Tests: test_agents/

**Conversion Date:** 2025-12-18
**Agent:** Agent 3 (Parallel Swarm)
**Task:** Convert valuable unit tests to integration tests

---

## Overview

This directory contains integration tests for the agent components, converted from unit tests in `tests/unit/test_agents/`. The conversion focused on retaining tests that verify real component interactions, business logic with I/O, and error handling paths, while removing trivial tests.

---

## Test Files

### 1. test_checkpointer_integration.py (14 tests)

Tests real database operations for CheckpointerManager:

**TestCheckpointerCreation (3 tests):**
- Database file creation
- Nested directory handling
- Custom path configuration

**TestStatePersistence (2 tests):**
- Save and load checkpoint state
- Multiple checkpointer isolation

**TestCleanupOperations (4 tests):**
- Old checkpoint removal
- Custom retention periods
- Empty database handling
- Missing database handling

**TestResourceManagement (3 tests):**
- Resource cleanup
- Async context manager lifecycle
- Idempotent close operations

**TestErrorHandling (2 tests):**
- Invalid path handling
- Permission error handling

**Run:**
```bash
pytest tests/integration/test_agents/test_checkpointer_integration.py -v
```

---

### 2. test_deep_agent_integration.py (8 tests)

Tests agent creation with real LLM and checkpointer integration:

**TestLLMIntegration (2 tests):**
- Primary (Gemini) and fallback (GPT) LLM creation
- Custom model configuration

**TestCheckpointerIntegration (2 tests):**
- CheckpointerManager instantiation
- Checkpointer parameter passing

**TestErrorHandling (3 tests):**
- Missing API key validation
- Checkpointer failure propagation
- Invalid model configuration

**TestSubAgentSupport (1 test):**
- Subagent parameter passing

**Run:**
```bash
pytest tests/integration/test_agents/test_deep_agent_integration.py -v
```

---

### 3. test_recursion_limit_integration.py (3 tests)

Tests recursion limit calculation and application:

**TestRecursionLimitConfiguration (3 tests):**
- Recursion limit calculation: `(max_tool_calls * 2) + 1`
- Formula verification with multiple values
- Configuration application to graph

**Run:**
```bash
pytest tests/integration/test_agents/test_recursion_limit_integration.py -v
```

---

## Running All Tests

### Basic Run
```bash
pytest tests/integration/test_agents/ -v
```

### With Coverage
```bash
pytest tests/integration/test_agents/ \
  --cov=backend.deep_agent.agents \
  --cov-report=html \
  --cov-report=term
```

### Specific Test Class
```bash
pytest tests/integration/test_agents/test_checkpointer_integration.py::TestStatePersistence -v
```

---

## Expected Results

**Total Tests:** 25
**Expected Pass Rate:** 100%

```
tests/integration/test_agents/test_checkpointer_integration.py .......... 14 passed
tests/integration/test_agents/test_deep_agent_integration.py ........ 8 passed
tests/integration/test_agents/test_recursion_limit_integration.py ... 3 passed

======================== 25 passed in X.XXs ========================
```

---

## Conversion Summary

### Tests Converted: 25 (36%)

| Source File | Tests | Converted | Integration File |
|-------------|-------|-----------|------------------|
| test_checkpointer.py | 21 | 14 | test_checkpointer_integration.py |
| test_deep_agent.py | 15 | 8 | test_deep_agent_integration.py |
| test_tool_call_limit.py | 3 | 3 | test_recursion_limit_integration.py |
| **Total** | **39** | **25** | **3 files** |

### Tests Deleted: 44 (64%)

| Source File | Tests | Reason |
|-------------|-------|--------|
| test_prompts.py | 19 | All trivial constant checks |
| test_reasoning_router.py | 11 | Phase 0 stub (always returns MEDIUM) |
| test_checkpointer.py | 7 | Trivial initialization checks |
| test_deep_agent.py | 7 | Source inspection, logging strings |
| **Total** | **44** | **Removed** |

**Details:** See [CONVERSION_SUMMARY.md](CONVERSION_SUMMARY.md)

---

## Coverage Targets

Integration tests focus on real interaction paths, not trivial code:

| Module | Expected Coverage | Focus Areas |
|--------|-------------------|-------------|
| checkpointer.py | ~70% | Database operations, cleanup, error handling |
| deep_agent.py | ~65% | LLM integration, checkpointer setup |
| reasoning_router.py | ~40% | Phase 0 stub (minimal logic) |
| prompts.py | ~50% | Environment-specific selection |

**Note:** Lower coverage than unit tests is expected. Integration tests intentionally skip:
- Trivial getters/setters
- Constant definitions
- Docstrings
- Private helper methods

---

## Documentation Files

### CONVERSION_SUMMARY.md
Detailed breakdown of conversion decisions:
- Test-by-test analysis
- Conversion rationale
- Test freshness validation
- Quality improvements

### VERIFICATION_CHECKLIST.md
Step-by-step verification guide:
- Run commands
- Expected results
- Troubleshooting
- Success criteria

### FILES_TO_DELETE.md
List of files and tests to delete:
- Complete file deletions
- Partial cleanup instructions
- Verification checklist
- Rollback plan

---

## Design Decisions

### Why Integration Tests?

1. **Real Behavior:** Tests actual database operations, LLM calls, and error paths
2. **Less Fragile:** No dependency on log strings or source code inspection
3. **Better Coverage:** Focuses on component interactions, not trivial assertions
4. **Maintainable:** Tests survive refactoring, focus on API contracts

### What Was Deleted?

1. **Trivial Tests:**
   - Static constant checks
   - Docstring existence
   - Attribute existence (hasattr)
   - String keyword searches

2. **Fragile Tests:**
   - Source code inspection (inspect.getsource)
   - Log message string matching
   - Trivial initialization checks

3. **Stub Tests:**
   - Phase 0 reasoning router (always returns MEDIUM)
   - Tests with no real logic to verify

---

## Future Improvements

### Phase 1: Reasoning Router

When implementing real routing logic, create integration tests for:
- Trigger phrase detection with real queries
- Complexity calculation with various input types
- Historical pattern analysis
- Performance under load

### Additional Coverage

Consider adding tests for:
- Concurrent checkpointer access
- Database migration scenarios
- LLM fallback behavior under load
- Sub-agent delegation chains

---

## Troubleshooting

### Import Errors
```bash
export PYTHONPATH=/home/runner/workspace:$PYTHONPATH
pip install -e .
```

### Async Test Failures
```bash
pip install pytest-asyncio
```

### Database Permission Errors
```bash
TMPDIR=/home/runner/tmp pytest tests/integration/test_agents/
```

**More details:** See [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

---

## Contributing

When adding new integration tests:

1. **Focus on behavior:** Test what the code does, not how it's implemented
2. **Use real dependencies:** Test with actual databases, files, etc.
3. **Test error paths:** Verify proper error handling and propagation
4. **Keep tests independent:** Each test should be runnable in isolation
5. **Use descriptive names:** Test names should describe the behavior being tested

### Example Test Pattern

```python
class TestFeatureName:
    """Test feature description."""

    @pytest.mark.asyncio
    async def test_behavior_under_condition(self, fixtures):
        """Test that feature behaves correctly under specific condition."""
        # Arrange
        setup_data = ...

        # Act
        result = await function_under_test(setup_data)

        # Assert
        assert result == expected_outcome
        # Verify side effects (database state, file creation, etc.)
```

---

## Related Documentation

- **Source Code:** `backend/deep_agent/agents/`
- **Original Unit Tests:** `tests/unit/test_agents/` (to be archived)
- **Integration Test Guidelines:** `tests/integration/README.md`
- **Coverage Reports:** Generated with `pytest --cov`

---

**Last Updated:** 2025-12-18
**Maintainer:** Agent 3 (Parallel Swarm)
**Status:** ✓ Conversion Complete, Awaiting Verification
