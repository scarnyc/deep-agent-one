# Integration Test Verification Checklist

This checklist helps verify that all converted integration tests are working correctly.

---

## Quick Verification Commands

### Run All Integration Tests
```bash
cd /home/runner/workspace
pytest tests/integration/test_agents/ -v
```

### Run Individual Test Files
```bash
# Test checkpointer integration
pytest tests/integration/test_agents/test_checkpointer_integration.py -v

# Test deep agent integration
pytest tests/integration/test_agents/test_deep_agent_integration.py -v

# Test recursion limit integration
pytest tests/integration/test_agents/test_recursion_limit_integration.py -v
```

### Run with Coverage
```bash
pytest tests/integration/test_agents/ \
  --cov=backend.deep_agent.agents \
  --cov-report=html \
  --cov-report=term
```

### Run Specific Test Classes
```bash
# Checkpointer creation tests
pytest tests/integration/test_agents/test_checkpointer_integration.py::TestCheckpointerCreation -v

# LLM integration tests
pytest tests/integration/test_agents/test_deep_agent_integration.py::TestLLMIntegration -v

# Recursion limit tests
pytest tests/integration/test_agents/test_recursion_limit_integration.py::TestRecursionLimitConfiguration -v
```

---

## Expected Test Results

### test_checkpointer_integration.py (14 tests)

#### TestCheckpointerCreation (3 tests)
- [ ] `test_create_checkpointer_creates_database_file` - PASS
- [ ] `test_create_checkpointer_with_nested_directories` - PASS
- [ ] `test_get_sqlite_checkpointer_custom_path` - PASS

#### TestStatePersistence (2 tests)
- [ ] `test_checkpointer_saves_and_loads_state` - PASS
- [ ] `test_multiple_checkpointers_isolated` - PASS

#### TestCleanupOperations (4 tests)
- [ ] `test_cleanup_old_checkpoints_removes_old_data` - PASS
- [ ] `test_cleanup_with_custom_retention_days` - PASS
- [ ] `test_cleanup_with_no_checkpoints_returns_zero` - PASS
- [ ] `test_cleanup_handles_missing_database` - PASS

#### TestResourceManagement (3 tests)
- [ ] `test_close_cleans_up_resources` - PASS
- [ ] `test_async_context_manager_cleanup` - PASS
- [ ] `test_close_is_idempotent` - PASS

#### TestErrorHandling (2 tests)
- [ ] `test_create_checkpointer_with_invalid_path_raises_error` - PASS
- [ ] `test_create_checkpointer_with_permission_denied` - PASS

**Expected:** 14/14 passing

---

### test_deep_agent_integration.py (8 tests)

#### TestLLMIntegration (2 tests)
- [ ] `test_agent_creates_primary_and_fallback_llm` - PASS
- [ ] `test_agent_uses_custom_model_config_from_settings` - PASS

#### TestCheckpointerIntegration (2 tests)
- [ ] `test_agent_creates_checkpointer_manager` - PASS
- [ ] `test_checkpointer_passed_to_create_deep_agent` - PASS

#### TestErrorHandling (3 tests)
- [ ] `test_create_agent_missing_api_key_raises_error` - PASS
- [ ] `test_create_agent_checkpointer_failure_propagates` - PASS
- [ ] `test_create_agent_invalid_model_config_raises_error` - PASS

#### TestSubAgentSupport (1 test)
- [ ] `test_create_agent_accepts_subagents_parameter` - PASS

**Expected:** 8/8 passing

---

### test_recursion_limit_integration.py (3 tests)

#### TestRecursionLimitConfiguration (3 tests)
- [ ] `test_create_agent_applies_recursion_limit` - PASS
- [ ] `test_recursion_limit_calculation_formula` - PASS
- [ ] `test_returns_compiled_state_graph_with_config` - PASS

**Expected:** 3/3 passing

---

## Common Issues and Fixes

### Issue: Import Errors

**Symptom:**
```
ImportError: cannot import name 'CheckpointerManager' from 'backend.deep_agent.agents.checkpointer'
```

**Fix:**
```bash
# Ensure you're in the workspace directory
cd /home/runner/workspace

# Verify Python path
export PYTHONPATH=/home/runner/workspace:$PYTHONPATH

# Reinstall dependencies
pip install -e .
```

---

### Issue: Missing Dependencies

**Symptom:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**Fix:**
```bash
pip install -r requirements.txt
# or
poetry install
```

---

### Issue: Async Test Failures

**Symptom:**
```
RuntimeError: Event loop is closed
```

**Fix:**
Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

---

### Issue: Database Permission Errors

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/tmp/...'
```

**Fix:**
Tests use temporary directories that should be writable. If this fails, check:
```bash
# Verify temp directory permissions
ls -la /tmp

# Run tests with different temp directory
TMPDIR=/home/runner/tmp pytest tests/integration/test_agents/
```

---

## Validation Steps

### Step 1: Verify Imports
```bash
python -c "
from backend.deep_agent.agents.checkpointer import CheckpointerManager
from backend.deep_agent.agents.deep_agent import create_agent
print('✓ Imports successful')
"
```

### Step 2: Run Quick Smoke Test
```bash
# Run just one test to verify setup
pytest tests/integration/test_agents/test_checkpointer_integration.py::TestCheckpointerCreation::test_create_checkpointer_creates_database_file -v
```

### Step 3: Run All Tests
```bash
pytest tests/integration/test_agents/ -v --tb=short
```

### Step 4: Check Coverage
```bash
pytest tests/integration/test_agents/ --cov=backend.deep_agent.agents --cov-report=term-missing
```

### Step 5: Verify No Regressions
```bash
# Run full test suite to ensure no breakage
pytest tests/ -v -k "not slow"
```

---

## Expected Coverage Metrics

### Module Coverage Targets

| Module | Expected Coverage |
|--------|-------------------|
| checkpointer.py | ~70% |
| deep_agent.py | ~65% |
| prompts.py | ~50% (mostly constants) |
| reasoning_router.py | ~40% (Phase 0 stub) |

**Note:** Coverage is lower than unit tests because integration tests focus on:
- Real interaction paths
- Error handling
- Component integration

They intentionally skip testing:
- Trivial getters/setters
- Constant definitions
- Docstrings
- Private helper methods

---

## Troubleshooting Guide

### Debug Test Failures

1. **Run with verbose output:**
   ```bash
   pytest tests/integration/test_agents/ -vvv --tb=long
   ```

2. **Run specific failing test:**
   ```bash
   pytest tests/integration/test_agents/test_checkpointer_integration.py::TestCheckpointerCreation::test_create_checkpointer_creates_database_file -vvv
   ```

3. **Check test fixtures:**
   ```bash
   pytest tests/integration/test_agents/ --fixtures
   ```

4. **Enable debug logging:**
   ```bash
   pytest tests/integration/test_agents/ -v --log-cli-level=DEBUG
   ```

### Verify Mock Behavior

If mocks aren't working as expected:

```python
# Add to test for debugging
print(f"Mock called: {mock_object.called}")
print(f"Call count: {mock_object.call_count}")
print(f"Call args: {mock_object.call_args}")
print(f"All calls: {mock_object.call_args_list}")
```

---

## Post-Verification Tasks

After all tests pass:

1. **Delete Original Unit Tests:**
   - [ ] Remove `tests/unit/test_agents/test_prompts.py` (all trivial)
   - [ ] Remove `tests/unit/test_agents/test_reasoning_router.py` (Phase 0 stub)
   - [ ] Remove deleted test classes from test_checkpointer.py
   - [ ] Remove deleted test classes from test_deep_agent.py

2. **Update Documentation:**
   - [ ] Update `tests/unit/test_agents/README.md` (if exists)
   - [ ] Update `tests/integration/README.md` with new test locations

3. **Update CI/CD:**
   - [ ] Verify GitHub Actions run integration tests
   - [ ] Update test count expectations in CI config

4. **Review Coverage Reports:**
   - [ ] Generate HTML coverage report
   - [ ] Review uncovered lines
   - [ ] Decide if additional tests needed

---

## Success Criteria

### All Tests Pass ✓
```
tests/integration/test_agents/test_checkpointer_integration.py::TestCheckpointerCreation ... 3 passed
tests/integration/test_agents/test_checkpointer_integration.py::TestStatePersistence ... 2 passed
tests/integration/test_agents/test_checkpointer_integration.py::TestCleanupOperations ... 4 passed
tests/integration/test_agents/test_checkpointer_integration.py::TestResourceManagement ... 3 passed
tests/integration/test_agents/test_checkpointer_integration.py::TestErrorHandling ... 2 passed

tests/integration/test_agents/test_deep_agent_integration.py::TestLLMIntegration ... 2 passed
tests/integration/test_agents/test_deep_agent_integration.py::TestCheckpointerIntegration ... 2 passed
tests/integration/test_agents/test_deep_agent_integration.py::TestErrorHandling ... 3 passed
tests/integration/test_agents/test_deep_agent_integration.py::TestSubAgentSupport ... 1 passed

tests/integration/test_agents/test_recursion_limit_integration.py::TestRecursionLimitConfiguration ... 3 passed

======================== 25 passed in X.XXs ========================
```

### Coverage Acceptable ✓
- Checkpointer: ~70% (focuses on integration paths)
- Deep Agent: ~65% (focuses on LLM/checkpointer integration)
- Recursion Limit: 100% (all logic covered)

### No Regressions ✓
- Full test suite passes
- No broken imports
- No new failures in other test files

---

## Final Checklist

- [ ] All 25 integration tests pass
- [ ] Coverage meets targets (60-70% for modules)
- [ ] No import errors
- [ ] No regressions in full test suite
- [ ] Documentation updated
- [ ] Original unit tests marked for deletion
- [ ] CI/CD pipeline updated (if needed)

---

**Verification Date:** _____________

**Verified By:** _____________

**Status:** [ ] PASS [ ] FAIL [ ] NEEDS REVIEW

**Notes:**
