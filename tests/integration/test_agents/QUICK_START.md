# Quick Start Guide

**Agent 3 - test_agents/ Integration Tests**

---

## TL;DR

```bash
# Run all integration tests
cd /home/runner/workspace
pytest tests/integration/test_agents/ -v

# Expected: 25 passed
```

---

## What Was Done

**Converted:** 25 valuable tests from unit tests to integration tests
**Deleted:** 44 trivial tests (constant checks, Phase 0 stubs, source inspection)

### Files Created

1. **test_checkpointer_integration.py** (14 tests) - Real database operations
2. **test_deep_agent_integration.py** (8 tests) - LLM and checkpointer integration
3. **test_recursion_limit_integration.py** (3 tests) - Recursion limit calculation

---

## Quick Verification

### Step 1: Run Tests
```bash
pytest tests/integration/test_agents/ -v
```

**Expected Output:**
```
test_checkpointer_integration.py .......... 14 passed
test_deep_agent_integration.py ........ 8 passed
test_recursion_limit_integration.py ... 3 passed

======================== 25 passed ========================
```

### Step 2: Check Coverage
```bash
pytest tests/integration/test_agents/ \
  --cov=backend.deep_agent.agents \
  --cov-report=term
```

**Expected Coverage:**
- checkpointer.py: ~70%
- deep_agent.py: ~65%

### Step 3: Verify No Regressions
```bash
pytest tests/ -v -k "not slow"
```

---

## Files to Delete (After Verification)

### Complete Deletions
```bash
rm tests/unit/test_agents/test_prompts.py          # 19 trivial tests
rm tests/unit/test_agents/test_reasoning_router.py # 11 Phase 0 stub tests
```

### Partial Cleanup
- **test_checkpointer.py:** Remove 7 test methods (init checks)
- **test_deep_agent.py:** Remove 7 test methods (source inspection, logging)

**Details:** See [FILES_TO_DELETE.md](FILES_TO_DELETE.md)

---

## Test Breakdown

### Checkpointer Integration (14 tests)
- ✓ Database file creation
- ✓ State persistence (save/load)
- ✓ Cleanup operations
- ✓ Resource management
- ✓ Error handling

### Deep Agent Integration (8 tests)
- ✓ LLM factory integration (Gemini + GPT fallback)
- ✓ Checkpointer integration
- ✓ Error propagation
- ✓ Sub-agent support

### Recursion Limit (3 tests)
- ✓ Limit calculation: (max_calls * 2) + 1
- ✓ Formula verification
- ✓ Configuration application

---

## What Was Deleted

### test_prompts.py (19 tests)
- All tests checked static constants
- No business logic tested
- Examples: "assert 'deep agent' in PROMPT.lower()"

### test_reasoning_router.py (11 tests)
- Phase 0 always returns MEDIUM
- No routing logic to test
- Will need rewrite in Phase 1

### test_checkpointer.py (7 tests)
- Trivial initialization checks
- hasattr() assertions
- No I/O tested

### test_deep_agent.py (7 tests)
- Source code inspection (inspect.getsource)
- Log message string checks
- Fragile, not testing behavior

---

## Conversion Criteria

**CONVERTED (25 tests):**
- ✓ Tests real component interactions
- ✓ Tests business logic with I/O
- ✓ Tests error handling paths
- ✓ Tests API contracts

**DELETED (44 tests):**
- ✗ Tests static constants
- ✗ Tests trivial attribute checks
- ✗ Tests source code content
- ✗ Tests Phase 0 stubs

---

## Troubleshooting

### Import Error
```bash
export PYTHONPATH=/home/runner/workspace:$PYTHONPATH
```

### Missing Dependencies
```bash
pip install -e .
```

### Async Test Failures
```bash
pip install pytest-asyncio
```

**More help:** See [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

---

## Documentation

- **README.md** - Full overview and usage guide
- **CONVERSION_SUMMARY.md** - Detailed conversion decisions
- **VERIFICATION_CHECKLIST.md** - Step-by-step verification
- **FILES_TO_DELETE.md** - Cleanup instructions

---

## Success Criteria

- [ ] All 25 tests pass
- [ ] Coverage ~60-70% for modules
- [ ] No regressions in full test suite
- [ ] Original unit tests marked for deletion

---

**Status:** ✓ Conversion Complete

**Next Steps:**
1. Run verification (above)
2. Review conversion decisions
3. Delete original unit tests
4. Update CI/CD (if needed)
