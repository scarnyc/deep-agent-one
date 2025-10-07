# GitHub Issues to Create

These issues were identified during code review on 2025-10-06.

---

## Issue 1: Remove unused `Optional` import from logging.py

**Labels:** `technical-debt`, `good-first-issue`, `cleanup`

**Title:** Remove unused `Optional` import from `core/logging.py`

**Description:**
The `Optional` type is imported but never used in `backend/deep_agent/core/logging.py`.

**File:** `backend/deep_agent/core/logging.py:5`

**Current Code:**
```python
from typing import Any, Optional
```

**Expected:**
```python
from typing import Any
```

**Impact:** No functional impact, just cleaner imports and reduces linter warnings.

---

## Issue 2: Remove unused `Optional` import from errors.py

**Labels:** `technical-debt`, `good-first-issue`, `cleanup`

**Title:** Remove unused `Optional` import from `core/errors.py`

**Description:**
The `Optional` type is imported but never used in `backend/deep_agent/core/errors.py`.

**File:** `backend/deep_agent/core/errors.py:2`

**Current Code:**
```python
from typing import Any, Optional
```

**Expected:**
```python
from typing import Any
```

**Impact:** No functional impact, just cleaner imports and reduces linter warnings.

---

## Issue 3: Add `Literal` type hint for log_format parameter

**Labels:** `enhancement`, `type-safety`, `good-first-issue`

**Title:** Use `Literal` type for `log_format` parameter in `setup_logging()`

**Description:**
The `log_format` parameter accepts any string but only `"json"` and `"standard"` are valid values. Using `Literal` provides better type safety.

**File:** `backend/deep_agent/core/logging.py:27-29`

**Current Code:**
```python
def setup_logging(
    log_level: LogLevel = LogLevel.INFO,
    log_format: str = "json",
) -> None:
```

**Suggested:**
```python
from typing import Literal

def setup_logging(
    log_level: LogLevel = LogLevel.INFO,
    log_format: Literal["json", "standard"] = "json",
) -> None:
```

**Impact:** Better type checking - invalid values would be caught by mypy and IDEs.

---

## Issue 4: Clear handlers before basicConfig for both formats

**Labels:** `bug`, `testing`, `reliability`

**Title:** Prevent handler accumulation when `setup_logging()` called multiple times

**Description:**
Currently, `root_logger.handlers.clear()` only runs for `"standard"` format. If `setup_logging()` is called multiple times with `"json"` format (common in test suites), handlers may accumulate causing duplicate log output.

**File:** `backend/deep_agent/core/logging.py:79-93`

**Current Code:**
```python
# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=numeric_level,
)

# ... processors ...

# Configure formatter for standard format
if log_format == "standard":
    # ... formatter setup ...

    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Only clears for standard format
    root_logger.addHandler(handler)
```

**Suggested Fix:**
```python
# Clear handlers for both formats (move before basicConfig)
root_logger = logging.getLogger()
root_logger.handlers.clear()

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=numeric_level,
)
```

**Impact:** Prevents duplicate log output when `setup_logging()` is called multiple times.

**Status:** Not blocking - all tests pass (19/19), but could cause confusing output in certain scenarios.

---

## Issue 5: `.env.example` Verbosity Values Mismatch ✅ RESOLVED

**Labels:** `bug`, `configuration`, `phase-0`, `high-priority`

**Title:** Fix verbosity enum values in `.env.example` to match `Verbosity` enum

**Description:**
The `.env.example` file specifies verbosity values as `standard/verbose/concise`, but the `Verbosity` enum in `gpt5.py` uses `low/medium/high`. This mismatch will cause validation errors when loading configuration.

**File:** `.env.example:9`

**Current Code:**
```bash
GPT5_DEFAULT_VERBOSITY=standard      # standard, verbose, concise
```

**Expected:**
```bash
GPT5_DEFAULT_VERBOSITY=medium        # low, medium, high
```

**Impact:** HIGH - Configuration validation will fail. Users copying `.env.example` to `.env` will get errors.

**Related Files:**
- `backend/deep_agent/models/gpt5.py:20-29` (Verbosity enum definition)

**Found in:** Layer 2 Code Review (2025-10-06)

**Resolution:** Fixed in commit 82ae04a - Updated `.env.example:9` to use `medium` with correct comment `# low, medium, high`

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

**Suggested:**
```python
def __init__(self, config: Settings | None = None) -> None:
    if config is None:
        config = get_settings()

    self.trigger_phrases = config.TRIGGER_PHRASES.split(",")
    self.complexity_threshold_high = config.COMPLEXITY_THRESHOLD_HIGH
    self.complexity_threshold_medium = config.COMPLEXITY_THRESHOLD_MEDIUM
```

**Impact:** MEDIUM - Should be fixed in Phase 1 when implementing actual trigger phrase detection. Not blocking for Phase 0.

**Related Files:**
- `backend/deep_agent/config/settings.py` (Settings class)
- `.env.example:19-21` (Configuration values already defined)

**Found in:** Layer 2 Code Review (2025-10-06)

---

## Issue 7: Add API key format validation to LLM factory

**Labels:** `enhancement`, `security`, `validation`, `nice-to-have`

**Title:** Add OpenAI API key format validation in `create_gpt5_llm()`

**Description:**
The `create_gpt5_llm()` function only checks if the API key is empty, but doesn't validate the format. OpenAI API keys follow a specific format (e.g., `sk-...`). Adding format validation could catch configuration errors earlier.

**File:** `backend/deep_agent/services/llm_factory.py:41-42`

**Current Code:**
```python
if not api_key:
    raise ValueError("API key is required")
```

**Suggested:**
```python
if not api_key:
    raise ValueError("API key is required")
if not api_key.startswith("sk-"):
    logger.warning("API key format may be invalid (should start with 'sk-')")
```

**Impact:** LOW - Optional enhancement. Current validation is sufficient for Phase 0. Invalid keys will fail when actually calling the API.

**Found in:** Layer 2 Code Review (2025-10-06)

---

## Issue 8: Install mypy for static type checking

**Labels:** `tooling`, `development`, `type-safety`, `good-first-issue`

**Title:** Add mypy to development dependencies for static type checking

**Description:**
The codebase uses comprehensive type hints throughout, but `mypy` is not installed in the development environment. Adding mypy would enable static type checking during development and in CI/CD.

**Files Affected:**
- `pyproject.toml` (add mypy to dev dependencies)
- `.pre-commit-config.yaml` (add mypy hook - optional)

**Current State:**
```bash
$ python3 -m mypy backend/
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3: No module named mypy
```

**Expected:**
```toml
# pyproject.toml
[tool.poetry.group.dev.dependencies]
mypy = "^1.13.0"
```

**Impact:** LOW - Nice to have. Type hints are already comprehensive. Mypy would catch type errors earlier in development.

**Benefits:**
- Catch type errors before runtime
- Better IDE support
- Enforces type hint consistency
- Can be integrated into pre-commit hooks

**Found in:** Layer 2 Code Review (2025-10-06)

---

## Issue 9: Modernize type hints in prompts.py to use Python 3.10+ union syntax

**Labels:** `technical-debt`, `enhancement`, `low-priority`

**Title:** Modernize type hints from `Optional[X]` to `X | None` in prompts.py

**Description:**
The `prompts.py` module uses older `Optional[X]` syntax instead of modern Python 3.10+ `X | None` union syntax. Since the project requires Python 3.10+, we should use the modern syntax for consistency.

**File:** `backend/deep_agent/agents/prompts.py:82-83`

**Current Code:**
```python
def get_agent_instructions(
    env: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> str:
```

**Expected:**
```python
def get_agent_instructions(
    env: str | None = None,
    settings: Settings | None = None,
) -> str:
```

**Impact:** LOW - Pure style improvement. No functional change. Improves consistency with Python 3.10+ idioms.

**Found in:** Layer 3 Code Review (2025-10-07)

---

## Issue 10: Add retry logic with exponential backoff to agent_service.py

**Labels:** `enhancement`, `reliability`, `medium-priority`

**Title:** Implement retry logic for LLM API calls in AgentService

**Description:**
Per Phase 0 requirements ("Retry logic with exponential backoff"), the `AgentService` should implement retry logic for transient LLM API failures. Currently, single failures cause immediate exceptions without retry attempts.

**Files:**
- `backend/deep_agent/services/agent_service.py:141, 215`
- Would add new dependency: `tenacity`

**Recommended Implementation:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

class AgentService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry_if_exception_type=(LLMError, ConnectionError, TimeoutError),
    )
    async def _invoke_with_retry(
        self,
        agent: CompiledStateGraph,
        input_data: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke agent with retry logic for transient failures."""
        return await agent.ainvoke(input_data, config)
```

**Impact:** MEDIUM - Improves reliability for production deployments. Transient network/API failures won't immediately fail user requests.

**Benefits:**
- Better user experience (temporary failures auto-recover)
- Reduced error rate in production
- Aligns with Phase 0 infrastructure requirements

**Trade-offs:**
- Adds dependency on `tenacity` library
- Slightly increased latency on retried requests
- Need to configure retry parameters carefully (avoid retry storms)

**Found in:** Layer 3 Code Review (2025-10-07)

**Status:** PARTIALLY IMPLEMENTED - Retry logic implemented in Perplexity MCP client (commit dd3185f), but NOT yet in AgentService. Will implement in AgentService as part of Layer 6 (FastAPI backend).

---

## Issue 11: Perplexity MCP Client Security Review Findings ✅ RESOLVED

**Labels:** `security`, `high-priority`, `phase-0`

**Title:** Fix security issues in Perplexity MCP client

**Description:**
Code review by code-review-expert identified 2 HIGH and 3 MEDIUM priority security issues in initial Perplexity MCP client implementation.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py`

**Issues Found:**
- **HIGH-1:** Missing rate limiting on expensive search operations
- **HIGH-2:** API key exposure risk in logs
- **MEDIUM-1:** No retry logic for transient failures
- **MEDIUM-2:** Missing input sanitization for query parameter
- **MEDIUM-3:** No timeout enforcement in _call_mcp()

**Resolution:** Fixed in commit dd3185f

**Security Features Implemented:**
1. **Rate Limiting:** 10 requests per 60 seconds (configurable)
2. **API Key Masking:** Only first 8 characters logged
3. **Retry Logic:** 3 attempts with exponential backoff (2-10s)
4. **Query Sanitization:** Removes dangerous characters, limits length to 500 chars
5. **Timeout Enforcement:** asyncio.timeout() wrapper in _call_mcp()

**Tests Added:** 4 new security tests (18 total tests)
- `test_search_enforces_rate_limit()`
- `test_rate_limit_window_resets()`
- `test_search_sanitizes_special_characters()`
- `test_search_truncates_long_queries()`

**Coverage:** 89.89% (up from 85.39%)

**Found in:** Layer 4 Code Review (2025-10-07)

---

## Issue 12: Thread safety in Perplexity MCP client rate limiting

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-1`

**Title:** Add thread-safe locking to Perplexity MCP client rate limiting

**Description:**
Post-commit review by code-review-expert identified thread safety issue in Perplexity MCP client's in-memory rate limiting. In multi-threaded environments (e.g., concurrent FastAPI requests), `self._request_timestamps` list is not thread-safe. Multiple simultaneous requests could corrupt the list or bypass rate limiting.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py:73-76`

**Current Code:**
```python
# Rate limiting state (in-memory for Phase 0, Redis for Phase 1+)
self._request_timestamps: list[float] = []
self._rate_limit_window = RATE_LIMIT_WINDOW
self._rate_limit_max = RATE_LIMIT_MAX_REQUESTS
```

**Recommended Fix:**
```python
import threading

def __init__(self, settings: Settings | None = None) -> None:
    # ... existing code ...

    # Rate limiting state
    # NOTE: In-memory implementation for Phase 0. Not suitable for distributed systems.
    # For production (Phase 1+), migrate to Redis with sliding window rate limiting.
    self._request_timestamps: list[float] = []
    self._rate_limit_lock = threading.Lock()  # Thread safety for concurrent requests
    self._rate_limit_window = RATE_LIMIT_WINDOW
    self._rate_limit_max = RATE_LIMIT_MAX_REQUESTS

def _check_rate_limit(self, query: str) -> None:
    with self._rate_limit_lock:  # Protect list operations
        now = time.time()
        # ... rest of implementation
```

**Impact:** MEDIUM - Acceptable for Phase 0 single-instance deployment, but should be fixed before production multi-instance deployment.

**Phase 1 Solution:** Migrate to Redis-based rate limiting with distributed locking.

**Found in:** Layer 4 Post-Commit Review (2025-10-07, commit dd3185f)

---

## Issue 13: API key masking edge case for short keys

**Labels:** `security`, `edge-case`, `low-priority`, `phase-1`

**Title:** Improve API key masking for keys shorter than 12 characters

**Description:**
Post-commit review by code-review-expert identified edge case in API key masking logic. If API key is shorter than 12 characters (8 prefix + 4 suffix), the slicing `self.api_key[-4:]` could expose more than intended.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py:78`

**Current Code:**
```python
# Mask API key for logging (security: HIGH-2 fix)
masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
```

**Recommended Fix:**
```python
# Mask API key for logging (security: HIGH-2 fix)
# Format: first 8 chars + "..." + last 4 chars for keys >12 chars
api_key_len = len(self.api_key)
if api_key_len > 12:
    masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
elif api_key_len > 8:
    masked_key = f"{self.api_key[:8]}...***"
else:
    masked_key = f"{self.api_key[:4]}...***"  # Very short keys

logger.info(
    "Perplexity MCP client initialized",
    api_key_masked=masked_key,  # Use the masked variable
    timeout=self.timeout,
    rate_limit=f"{self._rate_limit_max}/{self._rate_limit_window}s",
)
```

**Impact:** LOW - Perplexity API keys are typically 40+ characters. Edge case only affects unusually short keys.

**Found in:** Layer 4 Post-Commit Review (2025-10-07, commit dd3185f)

---

## Issue 14: Optional test coverage improvement for Perplexity client

**Labels:** `testing`, `enhancement`, `nice-to-have`

**Title:** Add test for empty results formatting to reach 90%+ coverage

**Description:**
Post-commit review by testing-expert identified optional coverage improvement. Line 347 (`format_results_for_agent()` empty results path) is not covered by tests. Coverage is currently 89.89%, adding this test would reach 90.91%.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py:347`
**Test File:** `tests/integration/test_mcp_integration/test_perplexity.py`

**Missing Test:**
```python
async def test_format_results_handles_empty_results(
    self,
    mock_settings: Settings,
) -> None:
    """Test formatting empty results returns helpful message."""
    from backend.deep_agent.integrations.mcp_clients.perplexity import (
        PerplexityClient,
    )

    client = PerplexityClient(settings=mock_settings)
    empty_results = {"results": [], "query": "test query", "sources": 0}

    # Act
    formatted = client.format_results_for_agent(empty_results)

    # Assert
    assert 'No results found for "test query"' in formatted
```

**Impact:** VERY LOW - Current 89.89% coverage exceeds 80% requirement. This is an optional quality improvement.

**Found in:** Layer 4 Post-Commit Review (2025-10-07, commit 647498c)

---

## Issue 15: Workflow contradiction - POST-COMMIT vs PRE-COMMIT ✅ RESOLVED

**Labels:** `documentation`, `critical`, `phase-0`

**Title:** Resolve contradiction between POST-COMMIT and PRE-COMMIT review workflows

**Description:**
Claude.md contained contradictory instructions about when to run code-review-expert and testing-expert agents:

**Location 1 (Lines 482-545 in commit 509ea7c):**
- Workflow: POST-COMMIT (review AFTER committing)
- Process: Commit → Review → Fix if needed (with fixup commits)

**Location 2 (Line 930):**
- Workflow: PRE-COMMIT (review BEFORE committing)
- Requirement: "run the code-review-expert and testing-expert agents before every commit"

**Impact:** CRITICAL - Developers would receive conflicting instructions about when to run reviews.

**Resolution:** Fixed in commit 08a2668

**Decision:** Adopted PRE-COMMIT workflow (matches line 930)

**Rationale:**
1. User's explicit instruction at line 930 takes precedence
2. Cleaner git history (no fixup commits needed)
3. Never commit unreviewed code
4. Standard code quality gate pattern
5. All issues (including non-critical) logged to GITHUB_ISSUES.md

**New Workflow:**
1. Write code/tests following TDD
2. Run testing-expert (if tests written)
3. Run code-review-expert (for all code)
4. Review findings and track ALL issues (HIGH/MEDIUM/LOW) in GITHUB_ISSUES.md
5. Fix blocking issues or document deferral
6. **ONLY AFTER APPROVAL:** Make commit

**Trade-off Accepted:**
- Slightly slower initial workflow (10-15 min wait before commit)
- BUT: Results in cleaner git history with zero unreviewed code

**Note:** Previous commits (647498c, dd3185f, 9eb0a89) were reviewed POST-COMMIT before this workflow correction. All future commits will follow PRE-COMMIT workflow.

**Found in:** Workflow Review (2025-10-07)

---
