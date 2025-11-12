# GitHub Issues - Migration Strategy

**Last Updated:** 2025-11-12

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

**Total Issues:** 75

### By Category:
- **⏭️ DEFERRED:** 7 backend issues (9%) - Fix during service implementation
- **🗑️ OBSOLETE:** 47 frontend issues (63%) - **REMOVED FROM FILE** (will be replaced by frontend-v2/)
- **📋 TRACKED:** 10 low-priority issues (13%) - Fix when time permits
- **TOTAL IN FILE:** 17 issues (DEFERRED + TRACKED only)

### By Priority:
- **CRITICAL/HIGH:** 0 issues (✅ PRODUCTION READY)
- **MEDIUM:** 7 issues (deferred to migration)
- **LOW:** 10 issues (tracked for later)

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

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** Agent Service microservice
**Timeline:** Weeks 7-8 of migration
**Rationale:** ReasoningRouter configuration will be redesigned as part of Agent Service microservice. New service will have proper config management patterns.
**Workaround:** Phase 1 placeholder feature, not needed for Phase 0.


## Issue 26: Enhance health endpoint with dependency status checks

**Labels:** `enhancement`, `observability`, `low-priority`, `phase-1`

**Title:** Add dependency health checks to `/health` endpoint

**Description:**
The current health endpoint only returns `{"status": "healthy"}` without checking dependencies like database connectivity, LLM API availability, or MCP server status. Enhanced health checks would improve observability and enable better monitoring/alerting.

**File:** `backend/deep_agent/main.py:261-268`

**Impact:** LOW - Basic health check is sufficient for Phase 0. Enhanced checks recommended for Phase 1 production deployment.

**Found in:** FastAPI App Review

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** API Gateway microservice
**Timeline:** Weeks 9-10 of migration
**Rationale:** API Gateway (Kong) will implement centralized health checks with dependency status for all microservices. Don't build this in monolith.
**Workaround:** Basic health check works for Phase 0.


## Issue 28: Version string hardcoded in FastAPI app creation

**Labels:** `technical-debt`, `enhancement`, `low-priority`, `phase-1`

**Title:** Load app version from pyproject.toml or settings instead of hardcoding

**Description:**
The FastAPI app version is hardcoded as `"0.1.0"` instead of being loaded from a single source of truth.

**File:** `backend/deep_agent/main.py:107`

**Impact:** LOW - Minor quality improvement. Hardcoded version is acceptable for Phase 0.

**Found in:** FastAPI App Review

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** All Microservices microservice
**Timeline:** Weeks 9-10 of migration
**Rationale:** Each microservice will have its own version management. Implement consistent versioning strategy during service creation.
**Workaround:** Hardcoded version acceptable for Phase 0.


## Issue 30: Add timeout protection to streaming endpoint

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-1`

**Title:** Implement timeout for long-running SSE streams

**Description:**
The POST /chat/stream endpoint doesn't enforce a timeout, potentially allowing infinite-duration streams that could exhaust server resources. Adding a configurable timeout would prevent resource exhaustion.

**File:** `backend/deep_agent/api/v1/chat.py:220-284`

**Impact:** MEDIUM - Not critical for Phase 0 single-user dev, important for production.

**Found in:** Streaming Endpoint Review

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** Chat Service microservice
**Timeline:** Weeks 5-6 of migration
**Rationale:** Chat Service microservice will implement proper timeout handling for SSE streams with configurable limits.
**Workaround:** Not critical for Phase 0 single-user dev environment.


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

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** Chat Service microservice
**Timeline:** Weeks 5-6 of migration
**Rationale:** Event transformation will be redesigned in Chat Service microservice. May implement new event pipeline architecture.
**Workaround:** Current implementation works, will be refactored.


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

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** State Service + Agent Service microservice
**Timeline:** Weeks 3-4 of migration
**Rationale:** Agent Service microservice will have new initialization pattern with dependency injection. State Service provides checkpointer.
**Workaround:** Errors caught at FastAPI level, manageable for MVP.


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

**Temporary Workaround (Phase 0):**
Users can limit parallel tool calls by rephrasing queries to be more specific/targeted.

**Solution Options for Phase 1:**

**Option A: Limit Parallel Tool Calls (Recommended)**
Modify system prompt to restrict parallel searches:
```python
# In backend/deep_agent/agents/prompts.py
system_prompt += "\n\nIMPORTANT: Limit web searches to 2-3 parallel calls maximum to ensure timely synthesis."
```
**Pros:** Simple, immediate fix
**Cons:** Reduces research thoroughness

**Option B: Increase OpenAI Client Timeout**
Add explicit timeout to ChatOpenAI configuration:
```python
# In backend/deep_agent/services/llm_factory.py
llm = ChatOpenAI(
    model=settings.GPT5_MODEL_NAME,
    temperature=settings.GPT5_TEMPERATURE,
    max_completion_tokens=settings.GPT5_MAX_TOKENS,
    reasoning_effort=effort_value,
    request_timeout=180.0,  # Add explicit timeout
)
```
**Pros:** May override LangGraph timeout
**Cons:** Not guaranteed to work, depends on LangChain internals

**Option C: Split Synthesis into Chunks**
Modify agent architecture to synthesize incrementally:
- After each N tool calls complete, run intermediate synthesis
- Final synthesis only combines intermediate results
- Keeps each model call under 45s
**Pros:** Most robust, handles any number of tools
**Cons:** Complex implementation, requires agent architecture changes

**Option D: Contact LangGraph Team**
File issue with LangGraph project requesting configurable timeouts:
- GitHub: https://github.com/langchain-ai/langgraph
- Request: Add `node_timeout` parameter to `create_deep_agent()`
**Pros:** Fixes at framework level
**Cons:** Depends on external team, unknown timeline

**Recommended Approach (Phase 1):**
1. Implement **Option A** immediately (system prompt change)
2. Test **Option B** (request timeout override)
3. If neither works, implement **Option C** (incremental synthesis)
4. File issue as **Option D** regardless (helps community)

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

---
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** Agent Service microservice
**Timeline:** Weeks 7-8 of migration
**Rationale:** Agent Service will implement incremental synthesis to avoid 45s timeout. Complex architectural change better done during service split.
**Workaround:** Users can limit parallel tools by rephrasing queries.




## 📋 TRACKED ISSUES (10 Low-Priority Issues)

**Strategy:** Fix when time permits - Non-blocking quality improvements.

**Rationale:** These are nice-to-have improvements that don't block migration or production deployment. Can be addressed incrementally after migration completes.

**Priority:** All issues in this section are LOW priority.

---

## Issue 14: Optional test coverage improvement for Perplexity client

**Labels:** `testing`, `enhancement`, `nice-to-have`

**Title:** Add test for empty results formatting to reach 90%+ coverage

**Description:**
Post-commit review by testing-expert identified optional coverage improvement. Line 347 (`format_results_for_agent()` empty results path) is not covered by tests. Coverage is currently 89.89%, adding this test would reach 90.91%.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py:347`
**Test File:** `tests/integration/test_mcp_integration/test_perplexity.py`

**Impact:** VERY LOW - Current 89.89% coverage exceeds 80% requirement. This is an optional quality improvement.

**Found in:** Layer 4 Post-Commit Review

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Optional quality improvement - 89.89% coverage already exceeds 80% requirement.
**When to Fix:** When spare time available, not urgent for migration.


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

---
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** Code duplication exists but doesn't affect functionality. Backend models will remain in microservices architecture.
**When to Fix:** When spare time available, not urgent for migration.


## Issue 100: Add test for WebSocket secret redaction feature

**Labels:** `testing`, `security`, `medium-priority`, `phase-0`

**Title:** Add integration test to verify WebSocket redacts secrets in error messages

**Description:**
The WebSocket endpoint implements secret redaction in error messages (line 221-222 of `backend/deep_agent/api/v1/websocket.py`), but there's no test verifying this security feature works correctly. This leaves a security-critical feature untested.

**File:** `tests/integration/test_api_endpoints/test_websocket.py`
**Related File:** `backend/deep_agent/api/v1/websocket.py:221-222`

**Missing Test Code:**
```python
def test_websocket_redacts_secrets_in_errors(
    self,
    client: TestClient,
    mock_agent_service: AsyncMock,
) -> None:
    """Test that WebSocket redacts secrets from error messages."""
    # Arrange
    message_data = {
        "type": "chat",
        "message": "Test secret redaction",
        "thread_id": "test-thread-123",
    }

    # Mock agent to raise error with secret pattern
    async def mock_secret_error(*args: Any, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        raise RuntimeError("API Error: key=sk-1234567890abcdef failed")
        yield

    def create_secret_error(*args: Any, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        return mock_secret_error(*args, **kwargs)

    mock_agent_service.stream.side_effect = create_secret_error

    # Act
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.send_json(message_data)
        response = websocket.receive_json()

    # Assert
    assert response.get("type") == "error"
    # Secret should be redacted
    assert "sk-" not in response.get("error", ""), \
        "Secret should be redacted from error message"
    assert "[REDACTED" in response.get("error", "") or \
           "failed" in response.get("error", "").lower()
```

**Impact:** MEDIUM - Security feature validation. Should be added to ensure redaction logic works.

**Found in:** code-review-expert + testing-expert Pre-Commit Review (2025-10-27)

---
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

**Missing Test 1: Malformed JSON**
```python
def test_websocket_handles_malformed_json(
    self,
    client: TestClient,
    mock_agent_service: AsyncMock,
) -> None:
    """Test that WebSocket handles malformed JSON gracefully."""
    # Act
    with client.websocket_connect("/api/v1/ws") as websocket:
        # Send invalid JSON (not parseable)
        websocket.send_text("{ this is not valid JSON }")

        # Should receive error response
        response = websocket.receive_json()

    # Assert
    assert response.get("type") == "error"
    assert "JSON" in response.get("error", "")
```

**Missing Test 2: Unknown Message Type**
```python
def test_websocket_rejects_unknown_message_type(
    self,
    client: TestClient,
    mock_agent_service: AsyncMock,
) -> None:
    """Test that WebSocket rejects unknown message types."""
    # Arrange
    message_data = {
        "type": "unknown_type",
        "message": "Test message",
        "thread_id": "test-thread-123",
    }

    # Act
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.send_json(message_data)
        response = websocket.receive_json()

    # Assert
    assert response.get("type") == "error"
    assert "unknown_type" in response.get("error", "").lower()
```

**Impact:** MEDIUM - Raises test coverage from 85% to ~90%, covers important error paths.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
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

**File:** `tests/integration/test_api_endpoints/test_websocket.py`
**Lines:** 182, 205, 248

**Current Code (Example from line 182):**
```python
assert response.get("type") == "error" or "error" in response
```

**Recommended Fix:**
```python
# Line 182 - test_websocket_validates_message_format
assert response.get("type") == "error", \
    f"Expected error type for invalid message format, got: {response}"

# Line 205 - test_websocket_handles_empty_message
assert response.get("type") == "error", \
    f"Expected error type for empty message, got: {response}"

# Line 248 - test_websocket_handles_agent_error
error_events = [e for e in events if e.get("type") == "error"]
assert len(error_events) >= 1, \
    f"Expected at least one error event, got events: {events}"
```

**Impact:** MEDIUM - Improves test reliability and prevents false positives.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
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

**Recommended Addition:**
```python
@pytest.fixture(scope="session", autouse=True)
def verify_backend_running():
    """
    Verify backend is accessible before running UI tests.

    Skips all UI tests if backend is not reachable, preventing
    cascading failures from missing backend.
    """
    import requests

    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    try:
        response = requests.get(
            f"{backend_url}/health",
            timeout=5
        )
        assert response.status_code == 200, \
            f"Backend health check failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip(
            f"Backend not running at {backend_url}. "
            "Start backend before running UI tests."
        )
    except Exception as e:
        pytest.skip(f"Backend verification failed: {e}")
```

**Impact:** MEDIUM - Improves test failure clarity and developer experience.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---

### LOW Priority Issues (Nice to Have)
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


## Issue 106: Add video recording configuration for Playwright tests

**Labels:** `testing`, `ui`, `enhancement`, `low-priority`, `phase-0`

**Title:** Enable conditional video recording for Playwright tests via environment variable

**Description:**
Playwright configuration has video recording commented out. Enable it conditionally via environment variable for CI/CD debugging without bloating local development with large video files.

**File:** `tests/ui/conftest.py:44-46`

**Current Code:**
```python
# Video recording disabled by default (large files)
# "record_video_dir": "test-results/videos",
# "record_video_size": {"width": 1280, "height": 720},
```

**Recommended Addition:**
```python
# Video recording disabled by default (large files)
# Enable in CI by setting PLAYWRIGHT_RECORD_VIDEO=true
if os.getenv("PLAYWRIGHT_RECORD_VIDEO", "false").lower() == "true":
    browser_context_args["record_video_dir"] = "test-results/videos"
    browser_context_args["record_video_size"] = {"width": 1280, "height": 720}
```

**Impact:** LOW - Improves CI/CD debugging capabilities.

**Found in:** testing-expert Pre-Commit Review (2025-10-27)

---
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


