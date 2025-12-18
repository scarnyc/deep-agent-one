# Files and Tests to Delete After Verification

**IMPORTANT:** Only delete these after verifying all integration tests pass.

---

## Complete Files to Delete

### 1. tests/unit/test_agents/test_prompts.py
**Reason:** All 19 tests are trivial constant checks
**Details:**
- TestPromptConstants (4 tests) - Check string exists and has length
- TestPromptContent (4 tests) - Check keywords in strings
- TestGetAgentInstructions (5 tests) - Trivial string equality
- TestGetAgentInstructionsWithSettings (3 tests) - Trivial parameter passing
- TestPromptOpikCompatibility (3 tests) - Check string types

**Command:**
```bash
rm tests/unit/test_agents/test_prompts.py
```

---

### 2. tests/unit/test_agents/test_reasoning_router.py
**Reason:** All 11 tests verify Phase 0 stub (always returns MEDIUM)
**Details:**
- TestReasoningRouterPhase0 (8 tests) - All assert MEDIUM is returned
- TestReasoningRouterPlaceholder (2 tests) - Check placeholder attributes exist
- TestReasoningRouterDocumentation (1 test) - Check docstring exists

**Note:** When Phase 1 implements real routing logic, create NEW integration tests.

**Command:**
```bash
rm tests/unit/test_agents/test_reasoning_router.py
```

---

## Partial File Cleanup (Manual Editing Required)

### 3. tests/unit/test_agents/test_checkpointer.py

**Keep These Test Classes:**
- None (all valuable tests converted to integration tests)

**Delete These Test Classes:**

#### TestCheckpointerManagerInit (3 tests)
```python
class TestCheckpointerManagerInit:
    def test_init_with_settings(self, mock_settings):
        # Trivial: just checks manager is not None

    def test_init_without_settings(self):
        # Trivial: checks default Settings usage

    def test_init_sets_db_path_from_settings(self, mock_settings):
        # Trivial: checks attribute assignment
```

**Reason:** Tests trivial initialization with no business logic.

#### TestConfiguration (partial)
```python
class TestConfiguration:
    def test_settings_integration(self):
        # Trivial: checks hasattr for CHECKPOINT_DB_PATH

    def test_environment_specific_configuration(self, temp_db_dir):
        # Duplicate: already covered in integration test
```

**Reason:** Tests trivial attribute checks and duplicate coverage.

**Command:**
```bash
# Manually edit file to remove these test classes
nano tests/unit/test_agents/test_checkpointer.py
```

---

### 4. tests/unit/test_agents/test_deep_agent.py

**Keep These Test Classes:**
- None (all valuable tests converted to integration tests)

**Delete These Test Classes:**

#### TestCreateAgentBasics (partial)
```python
class TestCreateAgentBasics:
    @pytest.mark.asyncio
    async def test_create_agent_with_default_settings_uses_get_settings(
        self,
        mock_llm: ChatOpenAI,
    ) -> None:
        # Already covered by integration tests with mocking
```

**Reason:** Duplicate coverage in integration tests.

#### TestSystemInstructions (2 tests)
```python
class TestSystemInstructions:
    @pytest.mark.asyncio
    async def test_system_instructions_include_file_tools_description(
        self,
        mock_settings: Settings,
    ) -> None:
        # Uses inspect.getsource() to grep source code

    @pytest.mark.asyncio
    async def test_system_instructions_mention_hitl(
        self,
        mock_settings: Settings,
    ) -> None:
        # Uses inspect.getsource() to grep source code
```

**Reason:** Tests inspect source code, not behavior. Fragile and not valuable.

#### TestLoggingAndObservability (2 tests)
```python
class TestLoggingAndObservability:
    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_llm")
    async def test_agent_creation_logs_configuration(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        # Tests logging strings (fragile)

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.create_llm")
    async def test_agent_creation_logs_llm_creation(
        self,
        mock_llm_factory: Mock,
        mock_settings: Settings,
        mock_llm: ChatOpenAI,
    ) -> None:
        # Tests logging strings (fragile)
```

**Reason:** Tests log message strings. Fragile and not testing actual behavior.

#### TestDeepAgentsIntegration
```python
class TestDeepAgentsIntegration:
    @pytest.mark.skipif(find_spec("deepagents") is None, reason="deepagents package not installed")
    @pytest.mark.asyncio
    async def test_create_agent_with_real_deepagents(
        self,
        mock_settings: Settings,
    ) -> None:
        # Skipped in test environment
```

**Reason:** Always skipped (deepagents not installed in test env).

**Command:**
```bash
# Manually edit file to remove these test classes
nano tests/unit/test_agents/test_deep_agent.py
```

---

## Alternative: Move to Archive

If you want to preserve the original tests for reference:

```bash
# Create archive directory
mkdir -p tests/archive/unit/test_agents

# Move original files
mv tests/unit/test_agents/test_prompts.py tests/archive/unit/test_agents/
mv tests/unit/test_agents/test_reasoning_router.py tests/archive/unit/test_agents/

# Add note to README
echo "Archived trivial unit tests after conversion to integration tests on $(date)" > tests/archive/unit/test_agents/README.md
```

---

## Summary

### Complete Deletions:
- **test_prompts.py** - 19 tests (all trivial)
- **test_reasoning_router.py** - 11 tests (Phase 0 stub)

### Partial Deletions:
- **test_checkpointer.py** - Remove 7 test methods (trivial init/config checks)
- **test_deep_agent.py** - Remove 7 test methods (source inspection, logging strings)

### Keep (unchanged):
- **test_tool_call_limit.py** - All 3 tests converted to integration tests, but keep originals if they use different mocking strategies

---

## Verification Before Deletion

**CRITICAL:** Run this checklist before deleting any files:

1. [ ] All integration tests pass (`pytest tests/integration/test_agents/ -v`)
2. [ ] Coverage is acceptable (~60-70% for modules)
3. [ ] No regressions in full test suite (`pytest tests/ -v`)
4. [ ] Integration tests provide equivalent or better coverage
5. [ ] Team has reviewed conversion decisions
6. [ ] Documentation updated to reflect new test locations

---

## Post-Deletion Verification

After deletion, verify:

```bash
# Run full test suite
pytest tests/ -v

# Verify no missing imports
python -c "import backend.deep_agent.agents.checkpointer; import backend.deep_agent.agents.deep_agent"

# Check test count
pytest tests/integration/test_agents/ --collect-only | grep "test session starts"
# Expected: 25 tests collected
```

---

## Rollback Plan

If deletion causes issues:

```bash
# Restore from git
git checkout tests/unit/test_agents/test_prompts.py
git checkout tests/unit/test_agents/test_reasoning_router.py

# Or restore from archive
cp tests/archive/unit/test_agents/test_prompts.py tests/unit/test_agents/
cp tests/archive/unit/test_agents/test_reasoning_router.py tests/unit/test_agents/
```

---

**Deletion Date:** _____________

**Deleted By:** _____________

**Rollback Available:** [ ] Yes (git) [ ] Yes (archive) [ ] No

**Notes:**
