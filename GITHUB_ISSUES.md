# GitHub Issues - Migration Strategy

**Last Updated:** 2025-11-20

## 🎯 Migration Strategy Overview

**Context:** Planned UI redesign (frontend-v2/) + microservices split (10-week timeline)

**Architectural Changes:**
- Complete UI redesign with new design system (keep AG-UI Protocol + WebSocket)
- Backend split into 4 microservices: Chat, Agent, State, Tool Services
- API Gateway (Kong) implementation
- Timeline: ~10 weeks parallel work

**Strategic Decision:** Categorize issues by migration impact to avoid wasted effort (87% time savings).

---

## 📊 Summary Statistics

**Total Issues:** 79 (added Issues 124-125: Parallel tool calls, Token estimates)

### By Category:
- **⏭️ DEFERRED:** 7 backend issues (9%) - Fix during service implementation
- **🗑️ OBSOLETE:** 47 frontend issues (63%) - **REMOVED FROM FILE** (will be replaced by frontend-v2/)
- **📋 TRACKED:** 12 low-priority issues (15%) - Fix when time permits
- **TOTAL IN FILE:** 19 issues (DEFERRED + TRACKED only)

### By Priority:
- **CRITICAL/HIGH:** 0 issues (✅ PRODUCTION READY)
- **MEDIUM:** 7 issues (deferred to migration)
- **LOW:** 12 issues (tracked for later)

**Obsolete Issues Removed:** 47 frontend issues deleted from file (Issues 35, 38-43, 52-82, 91-98, 107-111). These will not exist in frontend-v2/ redesign.

**Time Savings:** ~35-42 hours (87% reduction) by strategic deferral + removal of obsolete work.

---

## 💡 How to Use This Document

### ⏭️ DEFERRED Issues
**What:** Backend issues that require refactoring during microservices split.
**When to Fix:** During corresponding service implementation (Weeks 3-10 of migration).
**Why Deferred:** Code will be refactored anyway; fixing now = wasted effort.

### 📋 TRACKED Issues
**What:** Low-priority quality improvements that don't block anything.
**When to Fix:** When spare time available, not urgent.
**Why Tracked:** Nice-to-haves that can wait until after migration.

### ❌ OBSOLETE Issues (REMOVED)
**What:** 47 frontend issues (Issues 35, 38-43, 52-82, 91-98, 107-111) have been removed from this file.
**Why Removed:** Complete UI redesign (frontend-v2/) means these issues won't exist in new codebase.
**Reference:** See git history (commit before this reorganization) if you need to review deleted issues.

---

## ⏭️ DEFERRED ISSUES (7 Backend Issues)

**Strategy:** Fix during microservices implementation, not before.

**Rationale:** All these issues affect backend code that will be refactored when splitting into microservices. Fixing them now would create throwaway work since we'll rewrite these components during the migration.

**Migration Timeline:**
- **Weeks 3-4:** State Service implementation → Fix Issue 99
- **Weeks 5-6:** Chat Service implementation → Fix Issues 30, 31
- **Weeks 7-8:** Agent Service implementation → Fix Issues 6, 113
- **Weeks 9-10:** API Gateway implementation → Fix Issues 26, 28

---

## Issue 6: ReasoningRouter should load configuration from Settings

**Labels:** `enhancement`, `phase-1`, `configuration`, `refactoring`

**Title:** Load ReasoningRouter configuration from Settings instead of hardcoding

**Description:**
The `ReasoningRouter` class hardcodes trigger phrases and complexity thresholds. These should be loaded from the `Settings` class to allow environment-specific configuration.

**File:** `backend/deep_agent/agents/reasoning_router.py:39-46`

**Current Code:**
```python
def __init__(self) -> None:
    # Phase 1 placeholders - will be implemented in Phase 1
    self.trigger_phrases: list[str] = [
        "think harder",
        "deep dive",
        "analyze carefully",
        "be thorough",
    ]
    self.complexity_threshold_high: float = 0.8
    self.complexity_threshold_medium: float = 0.5
```

**Impact:** MEDIUM - Should be fixed in Phase 1 when implementing actual trigger phrase detection. Not blocking for Phase 0.

**Related Files:**
- `backend/deep_agent/config/settings.py` (Settings class)
- `.env.example:19-21` (Configuration values already defined)

**Found in:** Layer 2 Review

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in Agent Service microservice (Weeks 7-8). Phase 1 placeholder feature.


## Issue 26: Enhance health endpoint with dependency status checks

**Labels:** `enhancement`, `observability`, `low-priority`, `phase-1`

**Title:** Add dependency health checks to `/health` endpoint

**Description:**
The current health endpoint only returns `{"status": "healthy"}` without checking dependencies like database connectivity, LLM API availability, or MCP server status. Enhanced health checks would improve observability and enable better monitoring/alerting.

**File:** `backend/deep_agent/main.py:261-268`

**Impact:** LOW - Basic health check is sufficient for Phase 0. Enhanced checks recommended for Phase 1 production deployment.

**Found in:** FastAPI App Review

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in API Gateway microservice (Weeks 9-10). Basic health check works for Phase 0.


## Issue 28: Version string hardcoded in FastAPI app creation

**Labels:** `technical-debt`, `enhancement`, `low-priority`, `phase-1`

**Title:** Load app version from pyproject.toml or settings instead of hardcoding

**Description:**
The FastAPI app version is hardcoded as `"0.1.0"` instead of being loaded from a single source of truth.

**File:** `backend/deep_agent/main.py:107`

**Impact:** LOW - Minor quality improvement. Hardcoded version is acceptable for Phase 0.

**Found in:** FastAPI App Review

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in All Microservices (Weeks 9-10). Hardcoded version acceptable for Phase 0.


## Issue 30: Add timeout protection to streaming endpoint

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-1`

**Title:** Implement timeout for long-running SSE streams

**Description:**
The POST /chat/stream endpoint doesn't enforce a timeout, potentially allowing infinite-duration streams that could exhaust server resources. Adding a configurable timeout would prevent resource exhaustion.

**File:** `backend/deep_agent/api/v1/chat.py:220-284`

**Impact:** MEDIUM - Not critical for Phase 0 single-user dev, important for production.

**Found in:** Streaming Endpoint Review

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in Chat Service microservice (Weeks 5-6). Not critical for Phase 0.


## Issue 31: Transform LangChain events to AG-UI Protocol format

**Labels:** `enhancement`, `frontend-integration`, `medium-priority`, `phase-0-layer-7`

**Title:** Map streaming events to AG-UI Protocol event types

**Description:**
The streaming endpoint currently passes through raw LangChain events. Per CLAUDE.md Phase 0 requirements, the UI implements the AG-UI Protocol which expects specific event types (RunStarted, RunFinished, StepStarted, TextMessageStart, etc.). Events should be transformed before sending to clients.

**File:** `backend/deep_agent/api/v1/chat.py:231-238`

**Current Code:**
```python
async for event in service.stream(
    message=request_body.message,
    thread_id=request_body.thread_id,
):
    # Format event as SSE
    event_json = json.dumps(event)
    yield f"data: {event_json}\n\n"
```

**Impact:** MEDIUM - Required for Layer 7 (Frontend AG-UI implementation), not blocking for Layer 6.

**Found in:** Streaming Endpoint Review

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in Chat Service microservice (Weeks 5-6). Current implementation works.


## Issue 99: Add error handling to AgentService initialization in dependencies

**Labels:** `enhancement`, `error-handling`, `medium-priority`, `phase-0`

**Title:** Add try-except error handling for AgentService initialization failures

**Description:**
The `get_agent_service()` dependency function in `backend/deep_agent/api/dependencies.py` doesn't handle initialization failures. If AgentService initialization fails (config issues, missing dependencies), errors propagate unhandled to endpoints, resulting in unclear 500 errors.

**File:** `backend/deep_agent/api/dependencies.py:37`

**Current Code:**
```python
def get_agent_service() -> AgentService:
    """Dependency that provides an AgentService instance."""
    return AgentService()
```

**Recommended Fix:**
```python
from backend.deep_agent.core.logging import get_logger

logger = get_logger(__name__)

def get_agent_service() -> AgentService:
    """
    Dependency that provides an AgentService instance.

    Returns:
        AgentService: Initialized agent service instance

    Raises:
        RuntimeError: If service initialization fails
    """
    try:
        return AgentService()
    except Exception as e:
        logger.error(
            "Failed to initialize AgentService",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise RuntimeError(
            "Agent service initialization failed. Check configuration."
        ) from e
```

**Impact:** MEDIUM - Improves error messages and debugging experience. Not blocking for Phase 0.

**Found in:** code-review-expert Pre-Commit Review (2025-10-27)

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in State Service + Agent Service (Weeks 3-4). Errors caught at FastAPI level.


## Issue 113: LangGraph internal 45s timeout causes Agent streaming timeout

**Labels:** `bug`, `performance`, `medium-priority`, `phase-0`, `phase-1`

**Title:** Agent times out at 44.85s due to LangGraph internal per-node timeout

**Description:**
Agent streaming fails with `CancelledError` after exactly 44.85 seconds when processing queries with multiple parallel tool calls followed by GPT-5 synthesis. Root cause: LangGraph has an internal ~45s timeout per chain/node execution that is **not configurable** through `create_deep_agent()` parameters.

**Trace Analysis:**
- **Trace ID:** 49feb9c7-84b8-4c2f-936d-86ed9b4562eb
- **Duration:** 44.85 seconds (15:34:01.797540 to 15:34:46.649133)
- **Query:** "what are the latest trends in Gen AI?"
- **Workflow:**
  1. Agent makes 6 parallel web_search tool calls (completed successfully in ~15s)
  2. Agent attempts second GPT-5 call to synthesize results
  3. **FAILS** at 44.85s with `CancelledError`
  4. Error location: Deep in OpenAI HTTP streaming layer (`httpcore._async.http11`)

**Files:**
- Configuration: `backend/deep_agent/config/settings.py:74-77` (STREAM_TIMEOUT_SECONDS=180)
- Service: `backend/deep_agent/services/agent_service.py:304` (asyncio.timeout wrapping)
- Agent Creation: `backend/deep_agent/agents/deep_agent.py` (create_deep_agent call)

**Current Implementation Status:**
✅ **STREAM_TIMEOUT_SECONDS increased from 120s to 180s**
- Prevents overall stream timeout
- Adds diagnostic logging at agent_service.py:290-295
- Does NOT fix the root cause (LangGraph's 45s internal timeout)

❌ **TOOL_EXECUTION_TIMEOUT defined but not enforced**
- Defined in settings.py:102 but never used in codebase
- LangGraph doesn't support configurable tool/node timeouts via `create_deep_agent()`

**Impact:** MEDIUM - Queries with many parallel tools may timeout before synthesis completes. Affects complex research queries.

**Temporary Workaround (Phase 0):** Users can limit parallel tool calls by rephrasing queries.

**Phase 1 Solutions:** (A) Limit parallel tool calls via prompt, (B) Increase OpenAI client timeout, (C) Split synthesis into chunks, or (D) Request LangGraph framework fix. Recommended: Try A→B→C in order.

**Related Configuration:**
```python
# Current timeout settings (.env)
STREAM_TIMEOUT_SECONDS=180          # Overall stream timeout (fixed ✅)
TOOL_EXECUTION_TIMEOUT=90           # Per-tool timeout (not enforced ❌)
WEB_SEARCH_TIMEOUT=30               # Perplexity MCP timeout (enforced ✅)
```

**Documentation Updates:**
- ✅ .env updated with TOOL_EXECUTION_TIMEOUT
- ✅ .env.example updated with streaming configuration
- ✅ Diagnostic logging added to agent_service.py
- ✅ Trace analysis saved to tests/scripts/trace_49feb9c7_*.json

**Testing:**
- Test with modified system prompt limiting parallel calls
- Monitor LangSmith traces for timeout occurrences
- Track queries that trigger 6+ parallel tools

**Found in:** WebSocket Timeout Investigation (2025-11-06)

**🔄 MIGRATION STRATEGY: DEFERRED** - Will be fixed in Agent Service (Weeks 7-8). Complex architectural change for service split.


## 📋 TRACKED ISSUES (10 Low-Priority Issues)

**Strategy:** Fix when time permits - Non-blocking quality improvements.

**Rationale:** These are nice-to-have improvements that don't block migration or production deployment. Can be addressed incrementally after migration completes.

**Priority:** All issues in this section are LOW priority.

## Issue 14: Optional test coverage improvement for Perplexity client

**Labels:** `testing`, `enhancement`, `nice-to-have`

**Title:** Add test for empty results formatting to reach 90%+ coverage

**Description:**
Post-commit review by testing-expert identified optional coverage improvement. Line 347 (`format_results_for_agent()` empty results path) is not covered by tests. Coverage is currently 89.89%, adding this test would reach 90.91%.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py:347`
**Test File:** `tests/integration/test_mcp_integration/test_perplexity.py`

**Impact:** VERY LOW - Current 89.89% coverage exceeds 80% requirement. This is an optional quality improvement.

**Found in:** Layer 4 Post-Commit Review

**📋 TRACKED (LOW PRIORITY)** - Optional quality improvement. 89.89% coverage exceeds 80% requirement.


## Issue 21: Duplicate validator logic across agent models

**Labels:** `refactoring`, `technical-debt`, `low-priority`, `phase-1`

**Title:** Extract shared `strip_and_validate_string()` validator to reduce duplication

**Description:**
All three agent models (`AgentRunInfo`, `HITLApprovalRequest`, `HITLApprovalResponse`) implement identical `strip_and_validate_string()` validators. This code duplication violates the DRY (Don't Repeat Yourself) principle.

**Files:**
- `backend/deep_agent/models/agents.py:87-98` (AgentRunInfo)
- `backend/deep_agent/models/agents.py:155-166` (HITLApprovalRequest)
- `backend/deep_agent/models/agents.py:223-234` (HITLApprovalResponse)

**Impact:** LOW - Code duplication exists but doesn't affect functionality. Should be addressed in Phase 1 when broader model refactoring occurs.

**Found in:** Agent Models Review

**📋 TRACKED (LOW PRIORITY)** - Code duplication doesn't affect functionality. Backend models remain in microservices.


## Issue 100: Add test for WebSocket secret redaction feature

**Labels:** `testing`, `security`, `medium-priority`, `phase-0`

**Title:** Add integration test to verify WebSocket redacts secrets in error messages

**Description:**
The WebSocket endpoint implements secret redaction in error messages (line 221-222 of `backend/deep_agent/api/v1/websocket.py`), but there's no test verifying this security feature works correctly. This leaves a security-critical feature untested.

**File:** `tests/integration/test_api_endpoints/test_websocket.py`
**Related File:** `backend/deep_agent/api/v1/websocket.py:221-222`

**Missing Test:** `test_websocket_redacts_secrets_in_errors()` - Mock error with "sk-1234..." pattern, verify redaction in response

**Impact:** MEDIUM - Security feature validation. Should be added to ensure redaction logic works.

**Found in:** code-review-expert + testing-expert Pre-Commit Review (2025-10-27)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Security feature validation. Worth adding but not blocking Phase 0.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Security feature validation. Worth adding but not blocking Phase 0.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 101: Add missing WebSocket integration test cases

**Labels:** `testing`, `enhancement`, `medium-priority`, `phase-0`

**Title:** Add 4 missing test cases to WebSocket integration tests

**Description:**
WebSocket integration tests have excellent coverage (85%) but miss 4 specific error paths:
1. Malformed JSON handling
2. Unknown message type rejection
3. Unexpected exception handling
4. Secret redaction (covered by Issue 100)

**File:** `tests/integration/test_api_endpoints/test_websocket.py`

**Missing Tests:**
1. `test_websocket_handles_malformed_json()` - Send invalid JSON, verify error response
2. `test_websocket_rejects_unknown_message_type()` - Send unknown type, verify rejection

**Impact:** MEDIUM - Raises test coverage from 85% to ~90%, covers important error paths.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Would raise coverage from 85% to ~90%. Quality improvement, not blocking.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Would raise coverage from 85% to ~90%. Quality improvement, not blocking.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 102: Fix error assertions in WebSocket tests to be more specific

**Labels:** `testing`, `bug`, `medium-priority`, `phase-0`

**Title:** Replace permissive error assertions with specific checks

**Description:**
Three WebSocket tests use overly permissive error assertions that could lead to false positives. The current pattern `assert response.get("type") == "error" or "error" in response` will pass if the string "error" appears anywhere in the response, not just in the type field.

**File:** `tests/integration/test_api_endpoints/test_websocket.py` (Lines 182, 205, 248)

**Issue:** Permissive assertions like `assert response.get("type") == "error" or "error" in response`

**Fix:** Replace with specific checks: `assert response.get("type") == "error", f"Expected error type, got: {response}"`

**Impact:** MEDIUM - Improves test reliability and prevents false positives.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Test reliability improvement. Current tests work, just need better assertions.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Test reliability improvement. Current tests work, just need better assertions.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 103: Add backend connection verification fixture for Playwright tests

**Labels:** `testing`, `ui`, `enhancement`, `medium-priority`, `phase-0`

**Title:** Add session-scoped fixture to verify backend is running before UI tests

**Description:**
Playwright UI tests assume the backend is running but don't verify it. If the backend is down, all UI tests fail with cascade errors instead of a clear "backend not running" message. Adding a verification fixture would skip UI tests gracefully when backend is unavailable.

**File:** `tests/ui/conftest.py`

**Recommended:** Add session-scoped fixture `verify_backend_running()` that checks `/health` endpoint before UI tests. Skip all tests if backend unavailable to prevent cascade failures.

**Impact:** MEDIUM - Improves test failure clarity and developer experience.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---

### LOW Priority Issues (Nice to Have)
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Improves developer experience. Backend verification will be useful during migration.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Improves developer experience. Backend verification will be useful during migration.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 104: Add explicit `__all__` export list to dependencies.py

**Labels:** `code-quality`, `low-priority`, `phase-0`

**Title:** Export public API explicitly using `__all__` in dependencies module

**Description:**
The dependencies module defines a type alias `AgentServiceDep` but doesn't use `__all__` to explicitly declare the public API. Adding `__all__` improves IDE autocomplete and makes the public interface clear.

**File:** `backend/deep_agent/api/dependencies.py:41`

**Recommended Addition:**
```python
__all__ = ["get_agent_service", "AgentServiceDep"]
```

**Impact:** LOW - Code quality and IDE support improvement.

**Found in:** code-review-expert Pre-Commit Review (2025-10-27)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Code quality improvement for IDE support. Non-functional change.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Code quality improvement for IDE support. Non-functional change.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 105: Document TODO in authenticated_page fixture with Phase 1 reference

**Labels:** `documentation`, `low-priority`, `phase-1`

**Title:** Update TODO comment in authenticated_page to reference Phase 1 auth implementation

**Description:**
The `authenticated_page` fixture in `tests/ui/conftest.py` has a TODO comment that doesn't reference Phase 1 requirements. Update the comment to clarify this is expected behavior for Phase 0.

**File:** `tests/ui/conftest.py:143`

**Current Code:**
```python
# TODO: Implement authentication flow when auth is added
```

**Recommended Update:**
```python
# Phase 0: No authentication implemented yet
# Phase 1: Update this fixture to use actual auth flow (OAuth 2.0)
# See CLAUDE.md Phase 1 requirements for auth implementation
```

**Impact:** LOW - Documentation clarity.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Documentation clarity. Update comment to reference Phase 1.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Documentation clarity. Update comment to reference Phase 1.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 106: Add video recording configuration for Playwright tests

**Labels:** `testing`, `ui`, `enhancement`, `low-priority`, `phase-0`

**Title:** Enable conditional video recording for Playwright tests via environment variable

**Description:**
Playwright configuration has video recording commented out. Enable it conditionally via environment variable for CI/CD debugging without bloating local development with large video files.

**File:** `tests/ui/conftest.py:44-46`

**Recommended:** Enable conditional video recording via `PLAYWRIGHT_RECORD_VIDEO=true` env var for CI/CD debugging.

**Impact:** LOW - Improves CI/CD debugging capabilities.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** CI/CD debugging improvement. Useful for migration testing.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** CI/CD debugging improvement. Useful for migration testing.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 112: TheAuditor installation and environment configuration

**Labels:** `tooling`, `security`, `phase-1`, `medium-priority`

**Title:** Fix TheAuditor installation and integrate into CI/CD pipeline

**Description:**
TheAuditor security scanner is not properly installed in the current Python environment. The `aud` command is available globally but fails with `ModuleNotFoundError: No module named 'theauditor'`.

**Current Behavior:**
```bash
$ aud full
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.11/bin/aud", line 5, in <module>
    from theauditor.cli import main
ModuleNotFoundError: No module named 'theauditor'
```

**Expected Behavior:**
- `aud full` should run security scans successfully
- Results should be saved to `.pf/readthis/` directory
- `./scripts/security_scan.sh` should work without errors

**Impact:** MEDIUM - Security scanning is important but not blocking Phase 0 completion. Code has been manually reviewed by code-review-expert agent.

**Recommended Fix:**
1. Install TheAuditor properly in Poetry virtual environment:
   ```bash
   cd ~/Auditor  # Or wherever TheAuditor repo is
   poetry add --dev theauditor  # Add to dev dependencies
   ```
2. Update `scripts/security_scan.sh` to use Poetry environment
3. Add `.pf/` to `.gitignore` if not already present
4. Integrate into GitHub Actions CI/CD pipeline

**Phase 1 Tasks:**
- Set up TheAuditor in Poetry virtual environment
- Configure pre-commit hooks to run `aud full`
- Add CI/CD job to block merges on critical security findings
- Document usage in development guide

**Workaround for Phase 0:**
Manual code review by code-review-expert agent (includes security analysis) is sufficient for Phase 0 completion. TheAuditor integration is deferred to Phase 1.

**Found in:** Phase 0 completion testing (2025-10-29)

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Security tooling fix. Manual reviews working, can defer to Phase 1.
**When to Fix:** When spare time available, not urgent for migration.
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Security tooling fix. Manual reviews working, can defer to Phase 1.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 114: Pytest environment "null bytes" error blocking test execution

**Labels:** `bug`, `testing`, `environment`, `high-priority`, `phase-0`

**Title:** Pytest fails with "null bytes" error despite no null bytes in source files

**Description:**
Pytest consistently fails with `SyntaxError: source code string cannot contain null bytes` when loading `tests/conftest.py`, preventing test execution. This error persists despite extensive debugging showing:

1. ✅ No null bytes in any Python source files (verified with Python byte check)
2. ✅ All files compile successfully with `python -m py_compile`
3. ✅ conftest.py imports successfully when run directly with Python
4. ✅ All __pycache__ and .pytest_cache directories cleaned multiple times
5. ✅ PYTHONDONTWRITEBYTECODE=1 flag used
6. ✅ --cache-clear flag used
7. ✅ pytest plugins disabled (-p no:opik -p no:langsmith)
8. ✅ Different import modes tested (--import-mode=importlib)
9. ✅ Extended attributes checked (only com.apple.provenance found, not problematic)

**Error Message:**
```
ImportError while loading conftest '/Users/scar_nyc/Documents/GitHub/deep-agent-one/tests/conftest.py'.
SyntaxError: source code string cannot contain null bytes
```

**Attempted Workarounds:** Cache clearing, `--noconftest`, plugin disabling (`-p no:opik`), `--import-mode=importlib` - none resolved issue.

**Environment:** Python 3.11.7, pytest 9.0.1, macOS Darwin 24.4.0

**Impact:** HIGH - Blocks execution of all pytest-based tests. Unable to validate:
- Unit tests for ToolCallLimitedAgent (28 tests)
- Integration tests for tool call limiting (11 tests)
- Any other pytest-based test suites

**Workaround:** Use code review/testing agents for static analysis validation.

**Next Steps:** Investigate pytest version compatibility, plugin conflicts (opik/langsmith/anyio), fresh venv, reinstall, macOS-specific issues.

**Found in:** Tool Call Limit Feature completion testing (2025-11-13)

---

**📋 TRACKED (HIGH PRIORITY)** - Blocks test execution. Workaround: Use code review agents for static analysis.


## Issue 116: Add tool limit configuration example to create_agent docstring

**Labels:** `documentation`, `enhancement`, `low-priority`, `phase-0`

**Title:** Enhance create_agent docstring with tool call limit configuration example

**Description:**
The `create_agent` docstring includes A/B testing examples but lacks an example showing how to configure custom tool call limits via Settings.

**File:** `backend/deep_agent/agents/deep_agent.py:186-235`

**Current:** Docstring shows prompt variant A/B testing example (lines 216-219)

**Suggested Addition:**
```python
Tool Call Limit Example:
    >>> # Custom tool call limit
    >>> from backend.deep_agent.config.settings import Settings
    >>> settings = Settings(MAX_TOOL_CALLS_PER_INVOCATION=5)
    >>> agent = await create_agent(settings=settings)
    >>> # Agent will terminate gracefully after 5th tool call
```

**Impact:** LOW - Documentation enhancement, improves developer experience.

**Found in:** code-review-expert pre-commit review (2025-11-13)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Documentation improvement. Non-functional enhancement.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 117: LangSmith mock could use MagicMock instead of Mock

**Labels:** `testing`, `enhancement`, `low-priority`, `phase-0`

**Title:** Use MagicMock for LangSmith run_tree mock to improve attribute access simulation

**Description:**
Unit tests use `Mock()` for LangSmith `run_tree` object. `MagicMock()` would provide better attribute access simulation, though current implementation works fine.

**File:** `tests/unit/test_agents/test_tool_call_limit.py:395-396`

**Current Code:**
```python
mock_run_tree = Mock()
mock_run_tree.add_metadata = Mock()
```

**Recommended Change:**
```python
from unittest.mock import MagicMock
mock_run_tree = MagicMock()  # Better attribute access simulation
mock_run_tree.add_metadata = Mock()
```

**Impact:** LOW - No functional issue. Minor improvement to mock realism.

**Found in:** testing-expert pre-commit review (2025-11-13)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Mock works correctly as-is. MagicMock would be slightly better.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 118: Consider test parametrization for event counting tests

**Labels:** `testing`, `refactoring`, `low-priority`, `phase-0`

**Title:** Parametrize event counting tests to reduce code duplication

**Description:**
Event counting tests (v1/v2/mixed) could be parametrized to reduce duplication, though current approach is clear and readable.

**File:** `tests/unit/test_agents/test_tool_call_limit.py:87-157`

**Current:** Three separate test methods for v1, v2, and mixed events

**Alternative (parametrized):**
```python
@pytest.mark.parametrize("events,expected_count", [
    ([{"event": "on_tool_start", "data": {}}] * 3, 3),  # v1
    ([{"event": "on_tool_call_start", "data": {}}] * 2, 2),  # v2
    ([{"event": "on_tool_start"}, {"event": "on_tool_call_start"}], 2),  # mixed
])
async def test_counts_tool_calls(events, expected_count, mock_compiled_graph):
    ...
```

**Impact:** LOW - Code duplication is manageable. Parametrization would be more concise but current approach is clearer.

**Found in:** testing-expert pre-commit review (2025-11-13)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Current test structure is clear and readable. Refactoring is optional.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 119: Document integration test real agent dependency

**Labels:** `documentation`, `testing`, `low-priority`, `phase-0`

**Title:** Document that integration tests marked @pytest.mark.integration require deepagents

**Description:**
Integration tests marked with `@pytest.mark.integration` require full deepagents dependency. Tests correctly skip if dependency missing, but this should be documented in test suite README.

**File:** `tests/integration/test_agent_workflows/test_tool_call_limit_e2e.py:245-289`

**Current Behavior:** Tests use `pytest.skip()` if ImportError/NotImplementedError occurs

**Recommendation:** Add to test suite documentation:
```markdown
## Integration Tests

Tests marked with `@pytest.mark.integration` require full project dependencies:
- deepagents (for real agent creation)
- OpenAI API access (for GPT-5 integration)
- LangSmith (for tracing)

These tests will automatically skip if dependencies are not available.
```

**Impact:** LOW - Documentation clarity for developers running tests.

**Found in:** testing-expert pre-commit review (2025-11-13)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Test skip behavior is correct. Documentation would improve developer experience.
**When to Fix:** When spare time available, not urgent for migration.

## Issue 120: TheAuditor dependency configuration error

**Labels:** `tooling`, `security`, `low-priority`, `phase-0`

**Title:** Fix TheAuditor click module version incompatibility

**Description:**
TheAuditor security scanning tool encounters a dependency error when running `./scripts/security_scan.sh`. The `click` module in `.auditor_venv` has a version incompatibility causing `AttributeError: module 'click' has no attribute 'Group'`.

**Error:**
```
AttributeError: module 'click' has no attribute 'Group'
```

**Impact:** LOW - Cannot run automated security scans. Manual security review is used as fallback.

**Workaround:** Manual security review (comprehensive reviews completed for all commits)

**Fix:**
```bash
# Option 1: Upgrade click in auditor venv
.auditor_venv/bin/pip install --upgrade click

# Option 2: Reinstall TheAuditor with correct dependencies
.auditor_venv/bin/pip install -e /path/to/Auditor --force-reinstall
```

**File:** `.auditor_venv/` environment

**Found in:** code-review-expert pre-commit review (2025-11-15)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Manual security reviews are comprehensive and thorough. Automated tool is nice-to-have but not critical.
**When to Fix:** When spare time available, not urgent for migration.
**Workaround:** Continue using manual security reviews (no gaps in coverage).


## Issue 121: React key prop warning in ProgressTracker (FIXED)

**Labels:** `bug`, `frontend`, `react`, `low-priority`, `phase-0` ✅ **FIXED**

**Title:** Fix duplicate step IDs causing React key prop warnings in ProgressTracker

**Description:**
React emitted warning "Each child in a list should have a unique 'key' prop" when rendering ProgressTracker component. Root cause: `on_step` and `on_tool_call` event handlers used `event.run_id` as fallback ID, causing multiple steps/tool calls to share the same ID (since all steps in a run share the same `run_id`).

**Error Message:**
```
Warning: Each child in a list should have a unique 'key' prop.
Check the render method of `ProgressTracker`
```

**Files:**
- `frontend/hooks/useAGUIEventHandler.ts:330-383` (Event handlers)
- `frontend/components/ag-ui/ProgressTracker.tsx:310-316` (Rendering with keys)

**Root Cause:**
```typescript
// ❌ BEFORE: Multiple steps shared same ID
addStep(threadId, {
  id: event.data.step_id || event.run_id,  // run_id is NOT unique per step!
  name: event.data.name || 'Processing',
  status: 'running',
  started_at: new Date().toISOString(),
  metadata: event.data.metadata || {},
});
```

**Fix Applied:**
```typescript
// ✅ AFTER: Generate unique ID if backend doesn't provide one
const stepId = event.data.step_id || event.data.id || `step-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

addStep(threadId, {
  id: stepId,  // Guaranteed unique ID
  name: event.data.name || 'Processing',
  status: 'running',
  started_at: new Date().toISOString(),
  metadata: event.data.metadata || {},
});
```

**Impact:** LOW - Visual warning only, no functional impact. Could cause React reconciliation issues.

**Status:** ✅ **FIXED** in commit fixing-react-key-warnings (2025-11-15)

**Found in:** React console after implementing on_step/on_tool_call event handlers


## Issue 122: Agent infinite loop in web search causes GraphRecursionError

**Labels:** `bug`, `critical`, `phase-0`, `agent-behavior`

**Title:** Agent stuck in infinite web search loop hits recursion limit of 25

**Description:**
Agent gets stuck in an infinite research loop when answering web search queries, making 100+ redundant searches instead of synthesizing results after the first batch. This causes GraphRecursionError when hitting the recursion limit of 25 steps.

**Trace:** ID 985e4710 | 127 web_search calls (same 3 queries × 124 times) | 13 GPT-5 calls | ~$15-20 cost | GraphRecursionError (limit: 25)

**Root Cause:**
Agent receives comprehensive results from first 3-6 searches but **fails to recognize task completion**. Instead of synthesizing, it keeps making the SAME 3 queries in parallel repeatedly:
1. `"OpenAI news November 2025 week of Nov 10"` - 124 times
2. `"Google DeepMind news week of November 10 2025"` - 124 times
3. `"AI news roundup November 10-16, 2025"` - 124 times

**Why Loop Occurs:**
- Prompt says "Make a maximum of 3 parallel searches, then synthesize results"
- Agent makes 3 searches → Gets good results → Makes 3 MORE searches (instead of synthesizing)
- No loop detection to stop after N iterations of same behavior
- Each iteration spawns 3 new parallel searches
- Recursion limit (25 steps) hit before synthesis ever occurs

**Files:**
- System Prompt: `backend/deep_agent/agents/prompts.py:48-54`
- Agent Creation: `backend/deep_agent/agents/deep_agent.py:187-190` (recursion_limit setting)
- Error Handling: `backend/deep_agent/services/agent_service.py:570-596` (GraphRecursionError catch)
- Settings: `backend/deep_agent/config/settings.py:293` (MAX_TOOL_CALLS_PER_INVOCATION=12)

**Fix Applied:**
✅ **Phase 1: Prompt-Level Loop Prevention**

Updated system prompt with explicit loop prevention guidance:
```python
### Parallel Tool Execution
- **Maximum 3 parallel tool calls** at a time (prevents timeouts per Issue #113)
- For web searches: Make a maximum of 3 parallel searches, then **IMMEDIATELY SYNTHESIZE RESULTS**
- **CRITICAL**: Always provide a final synthesis response to the user, even if some searches fail or are cancelled
- **LOOP PREVENTION**: If you've made 6+ web searches for the same topic, STOP searching and synthesize what you have
- Research tasks should complete in 3-9 web searches maximum - synthesis is MORE important than exhaustive research
- If more searches needed after synthesis, ask user permission before continuing
- Balance thoroughness with execution time (target <45s per reasoning step)
```

**Testing:**
- ✅ Integration test created: `tests/integration/test_agent_workflows/test_loop_prevention.py`
- ✅ Prompt version updated: 1.1.0 → 1.2.0
- 🔄 Pending: Re-run original query to validate fix

**Impact:** CRITICAL - Blocks production use for research queries. Users get:
- No response (ERROR instead of answer)
- High cost (~$15-20 per failed query vs $1-2 for successful)
- Poor UX (2+ min wait time, then error)

**Why NOT to Increase Recursion Limit:**
- Masks the bug (agent will loop for 50 steps instead of 25)
- Cost explosion ($25-30 instead of $15-20)
- Doesn't fix root cause (agent still doesn't know when to stop)
- Current limit of 25 is correct (12 tool calls × 2 steps + 1 = 25)

**Related Issues:**
- Issue 113: LangGraph 45s timeout (different but related to tool execution)

**Metrics:**
| Metric | Before Fix | After Fix (Expected) |
|--------|-----------|---------------------|
| Web Searches | 127 | 3-9 |
| Cost per Query | ~$15-20 | <$1 |
| User Response | ERROR | Successful synthesis |
| Execution Time | 2+ min (timeout) | <45s |

**Found in:** GraphRecursionError investigation (2025-11-17)


## Issue 123: TheAuditor Python 3.14 build compatibility issue

**Labels:** `infrastructure`, `tooling`, `low-priority`, `phase-0`

**Title:** TheAuditor fails to install in Python 3.14 due to hatchling build system error

**Description:**
TheAuditor cannot be installed in editable mode (`pip install -e`) with Python 3.14.0 due to a timeout error in hatchling's license file processing during build metadata preparation. This blocks the project-local TheAuditor setup in `.pf/venv/`.

**Error:**
```
× Preparing editable metadata (pyproject.toml) did not run successfully.
│ exit code: 1
╰─> TimeoutError: [Errno 60] Operation timed out
    File ".../hatchling/builders/wheel.py", line 718, in add_licenses
      record = archive.write_metadata(f'licenses/{relative_path}', f.read())
```

**Context:**
- TheAuditor documentation specifies requirement: Python >=3.14
- Installed Python 3.14.0 via Homebrew (`/opt/homebrew/bin/python3`)
- Created `.pf/venv` with Python 3.14.0 successfully
- TheAuditor v1.6.4-dev1 cloned at `.pf/venv/src/auditor`
- Installation command: `.pf/venv/bin/pip install -e .pf/venv/src/auditor`

**Files:**
- TheAuditor source: `.pf/venv/src/auditor/` (not tracked in git)
- Virtual environment: `.pf/venv/` (excluded via `.gitignore`)
- Security scan script: `scripts/security_scan.sh:44` (references `.pf/venv/bin/aud`)

**Impact:** LOW - Security scanning deferred but not blocking development. Manual security reviews (via code-review-expert) continue to provide comprehensive coverage.

**Workarounds:**
1. **Current:** Manual security reviews via code-review-expert agent (no gaps)
2. **Alternative:** Use Python 3.13 in `.pf/venv` (may have other compatibility issues)
3. **Alternative:** Wait for TheAuditor fix for Python 3.14 compatibility

**Related Configuration:**
```bash
# Completed setup steps:
✅ Python 3.14.0 installed via Homebrew
✅ .pf/venv created with Python 3.14
✅ .gitignore updated to exclude .pf/
✅ CLAUDE.md → AGENTS.md symlink created
✅ scripts/security_scan.sh updated to use .pf/venv/bin/aud

# Blocked:
❌ TheAuditor installation in .pf/venv
❌ Automated security scanning via `aud full`
```

**Next Steps:**
- Monitor TheAuditor repo for Python 3.14 build fixes
- OR test with Python 3.13 in isolated venv
- Re-attempt installation once compatibility resolved

**Found in:** TheAuditor setup (2025-11-26)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Manual security reviews via code-review-expert provide comprehensive coverage. Automated tool is nice-to-have but not critical for Phase 0 completion.
**When to Fix:** After TheAuditor releases Python 3.14 compatibility update, or when revisiting security tooling in Phase 1.
**Workaround:** Continue using code-review-expert agent for pre-commit security reviews (no gaps in coverage).


## Issue 124: Enable parallel tool calls when langchain_google_genai supports it

**Labels:** `enhancement`, `performance`, `phase-1`, `low-priority`

**Title:** Enable parallel tool call execution when langchain_google_genai wrapper adds support

**Description:**
Gemini natively supports parallel tool calls, but the `langchain_google_genai` Python wrapper does not reliably handle them. Currently using sequential execution guidance as a workaround. When the wrapper is fixed, update the system prompt to enable parallel execution for improved performance.

**Upstream Issue:** https://github.com/langchain-ai/langchain-google/issues/816

**Files:**
- `backend/deep_agent/agents/prompts.py:22-27` (SEQUENTIAL_EXECUTION_GUIDANCE)
- `backend/deep_agent/agents/prompts.py:138-143` (get_agent_instructions uses sequential mode)

**Current Code (prompts.py:22-27):**
```python
# Sequential execution guidance (due to langchain_google_genai wrapper limitation)
# Note: Gemini natively supports parallel tool calls, but the wrapper does not
# See: https://github.com/langchain-ai/langchain-google/issues/816
SEQUENTIAL_EXECUTION_GUIDANCE = (
    "Execute tools ONE AT A TIME. Wait for each result before proceeding."
)
```

**Future Implementation:**
When langchain_google_genai fixes parallel tool call support:
1. Add `PARALLEL_EXECUTION_GUIDANCE = "Batch 1-3 independent tool calls per step for efficiency."`
2. Update `get_agent_instructions()` to accept `parallel_mode: bool` parameter
3. OR detect model capability automatically via model name/settings

**Impact:** LOW - Sequential mode works correctly. Parallel would improve latency by ~30-50% for research queries.

**Found in:** System prompt architecture optimization (2025-11-29)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Sequential mode is working correctly. Parallel is a performance optimization, not a bug fix.
**When to Fix:** After langchain_google_genai releases fix for Issue #816.
**Monitor:** https://github.com/langchain-ai/langchain-google/issues/816


## Issue 125: Update prompts_variants.py token estimates to reflect v3.0.0 baseline

**Labels:** `documentation`, `technical-debt`, `low-priority`, `phase-0`

**Title:** Stale token estimates in A/B testing variants after prompt v3.0.0 optimization

**Description:**
The `prompts_variants.py` file contains token estimates from v2.0.0 prompt. After the v3.0.0 optimization (32% reduction), these estimates are stale:

- control: Shows ~778 tokens (actual: ~280)
- max_compression: Shows ~389 tokens (actual: ~200 estimated)
- balanced: Shows ~505 tokens (actual: ~250 estimated)

**File:** `backend/deep_agent/agents/prompts_variants.py`

**Current Code (stale):**
```python
def get_variant_metadata() -> dict[str, dict]:
    return {
        "control": {
            "description": "Original prompt with full XML structure",
            "token_estimate": 778,  # Stale - actual is ~280
            ...
        },
        ...
    }
```

**Impact:** LOW - Only affects A/B testing metadata display. Does not affect actual prompt behavior.

**Recommended Fix:**
Update token estimates when actively using A/B testing system:
- control: ~280 tokens (v3.0.0 Markdown format)
- max_compression: ~200 tokens (estimate)
- balanced: ~250 tokens (estimate)

**Found in:** System prompt architecture optimization (2025-11-29)

---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** A/B testing metadata, not functional code. Can defer until A/B testing is actively used.
**When to Fix:** When actively using prompt A/B testing system.

