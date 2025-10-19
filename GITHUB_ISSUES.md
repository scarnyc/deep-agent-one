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

## Issue 16: PerplexityClient logs unused masked_key variable

**Labels:** `security`, `logging`, `medium-priority`, `phase-0`

**Title:** Use masked_key variable in PerplexityClient logging instead of raw prefix

**Description:**
The PerplexityClient computes a `masked_key` variable (line 78) but doesn't use it in the logger.info() call (line 82). Instead, it logs `api_key_prefix=self.api_key[:8]`. This is inconsistent and the masked format (`sk-abc...xyz`) is more standard for API key logging.

**File:** `backend/deep_agent/integrations/mcp_clients/perplexity.py:78-85`

**Current Code:**
```python
# Mask API key for logging (security: HIGH-2 fix)
masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"

logger.info(
    "Perplexity MCP client initialized",
    api_key_prefix=self.api_key[:8],  # Should use masked_key
    timeout=self.timeout,
    rate_limit=f"{self._rate_limit_max}/{self._rate_limit_window}s",
)
```

**Expected:**
```python
# Mask API key for logging (security: HIGH-2 fix)
masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"

logger.info(
    "Perplexity MCP client initialized",
    api_key_masked=masked_key,  # Use the masked variable
    timeout=self.timeout,
    rate_limit=f"{self._rate_limit_max}/{self._rate_limit_window}s",
)
```

**Impact:** MEDIUM - Minor security improvement. Current approach works but masked format is more standard and informative.

**Benefits:**
- Uses computed variable (avoids waste)
- Standard API key masking format (prefix...suffix)
- More informative than prefix-only
- Consistent with security best practices

**Found in:** Web Search Tool Code Review (2025-10-07)

---

## Issue 17: Add debug logging for web_search tool result

**Labels:** `enhancement`, `logging`, `low-priority`, `phase-0`

**Title:** Add debug log statement before returning results in web_search tool

**Description:**
The web_search tool logs search initiation and completion (via PerplexityClient), but doesn't log the final result summary before returning to the agent. Adding a debug log would help troubleshoot agent behavior.

**File:** `backend/deep_agent/tools/web_search.py:74`

**Current Code:**
```python
# Format results for agent consumption
formatted_results = client.format_results_for_agent(results)

return formatted_results
```

**Suggested:**
```python
# Format results for agent consumption
formatted_results = client.format_results_for_agent(results)

logger.debug(
    "Returning formatted results to agent",
    result_length=len(formatted_results),
    query=query,
)

return formatted_results
```

**Impact:** VERY LOW - Optional debug enhancement. Current logging via PerplexityClient is sufficient.

**Benefits:**
- Easier debugging of tool output
- Trace result size before agent consumption
- Consistent debug-level granularity

**Found in:** Web Search Tool Code Review (2025-10-07)

---

## Issue 18: Enhance web_search docstring with failure mode details

**Labels:** `documentation`, `enhancement`, `low-priority`, `phase-0`

**Title:** Add retry and rate limit failure details to web_search tool docstring

**Description:**
The web_search tool docstring mentions rate limiting and timeout, but doesn't explain that the tool automatically retries on failures or what happens when rate limits are exceeded. Agents could benefit from understanding failure modes.

**File:** `backend/deep_agent/tools/web_search.py:44-47`

**Current Code:**
```python
Note:
    - Queries are automatically sanitized for security
    - Rate limiting: 10 requests per minute
    - Timeout: 30 seconds (configurable)
```

**Suggested:**
```python
Note:
    - Queries are automatically sanitized for security
    - Rate limiting: 10 requests per minute (raises error if exceeded)
    - Timeout: 30 seconds (configurable)
    - Retries automatically on transient failures (3 attempts with exponential backoff)
```

**Impact:** VERY LOW - Documentation improvement. Helps agents understand when searches might fail.

**Benefits:**
- Agent awareness of retry behavior
- Clearer error expectations
- Better agent decision-making on failures

**Found in:** Web Search Tool Code Review (2025-10-07)

---

## Issue 19: Extract API key masking logic to shared utility function

**Labels:** `refactoring`, `security`, `medium-priority`, `phase-0`

**Title:** Create shared utility for API key masking to reduce code duplication

**Description:**
Both PerplexityClient and LangSmith integration implement API key masking with slightly different logic. The LangSmith version (lines 70-78) is more robust, handling edge cases for short keys. This logic should be extracted to a shared utility function to ensure consistent security practices across all integrations.

**Files:**
- `backend/deep_agent/integrations/mcp_clients/perplexity.py:78` (simpler masking)
- `backend/deep_agent/integrations/langsmith.py:70-78` (robust masking with edge cases)

**Current Duplication:**

**PerplexityClient (simpler):**
```python
# Mask API key for logging (security: HIGH-2 fix)
masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
```

**LangSmith (robust with edge cases):**
```python
# Mask API key for logging (show prefix only)
# Format: lsv2_abc...xyz for keys >12 chars, else partial masking
api_key_len = len(api_key)
if api_key_len > 12:
    masked_key = f"{api_key[:8]}...{api_key[-4:]}"
elif api_key_len > 8:
    masked_key = f"{api_key[:4]}...***"
else:
    masked_key = "***"
```

**Recommended Solution:**

Create `backend/deep_agent/core/security.py`:
```python
def mask_api_key(api_key: str, prefix_len: int = 8, suffix_len: int = 4) -> str:
    """
    Mask an API key for safe logging.

    Shows prefix and suffix of key, masks the middle. Handles edge cases
    for short keys to avoid exposing too much information.

    Args:
        api_key: The API key to mask
        prefix_len: Number of characters to show at start (default: 8)
        suffix_len: Number of characters to show at end (default: 4)

    Returns:
        Masked API key string (e.g., "sk-abc12...xyz9" or "***" for short keys)

    Examples:
        >>> mask_api_key("sk-proj-1234567890abcdefghij")
        "sk-proj-1...ghij"

        >>> mask_api_key("short")
        "***"
    """
    api_key_len = len(api_key)
    min_len = prefix_len + suffix_len

    if api_key_len > min_len:
        return f"{api_key[:prefix_len]}...{api_key[-suffix_len:]}"
    elif api_key_len > prefix_len:
        return f"{api_key[:prefix_len]}...***"
    else:
        return "***"
```

Then update both integrations:
```python
from backend.deep_agent.core.security import mask_api_key

# PerplexityClient
masked_key = mask_api_key(self.api_key)

# LangSmith
masked_key = mask_api_key(api_key)
```

**Impact:** MEDIUM - Improves security consistency and reduces duplication. Not blocking for Phase 0 as current implementations work correctly.

**Benefits:**
- Single source of truth for API key masking
- Consistent security behavior across all integrations
- Easier to audit and test security logic
- Reduces code duplication (DRY principle)

**Testing:**
- Add `tests/unit/test_core/test_security.py` with edge case tests
- Update existing tests in PerplexityClient and LangSmith to use utility

**Found in:** LangSmith Integration Code Review (2025-10-07)

---

## Issue 20: LangSmith setup docstring incorrectly states function raises on missing API key

**Labels:** `documentation`, `low-priority`, `phase-0`

**Title:** Correct setup_langsmith() docstring to clarify it only validates API key

**Description:**
The `setup_langsmith()` docstring (line 29) says "Raises: ValueError: If LANGSMITH_API_KEY is not configured." This is slightly misleading - the function validates the API key but doesn't verify authentication with LangSmith. The actual API call (when tracing happens) will fail if the key is invalid.

**File:** `backend/deep_agent/integrations/langsmith.py:29`

**Current Docstring:**
```python
    Raises:
        ValueError: If LANGSMITH_API_KEY is not configured.
```

**Suggested Improvement:**
```python
    Raises:
        ValueError: If LANGSMITH_API_KEY is missing or empty. Note that this
            only validates the key exists - authentication with LangSmith API
            is verified when actual tracing occurs (lazy validation).
```

**Impact:** VERY LOW - Minor documentation clarity improvement. Current docstring is accurate but could be more explicit.

**Benefits:**
- Clearer expectations about when authentication actually occurs
- Helps developers understand lazy validation pattern
- Reduces confusion about when API errors might appear

**Found in:** LangSmith Integration Code Review (2025-10-07)

---

## Issue 21: Duplicate validator logic across agent models

**Labels:** `refactoring`, `technical-debt`, `low-priority`, `phase-1`

**Title:** Extract shared `strip_and_validate_string()` validator to reduce duplication

**Description:**
All three agent models (`AgentRunInfo`, `HITLApprovalRequest`, `HITLApprovalResponse`) implement identical `strip_and_validate_string()` validators. This code duplication violates the DRY (Don't Repeat Yourself) principle.

**Files:**
- `backend/deep_agent/models/agents.py:87-98` (AgentRunInfo)
- `backend/deep_agent/models/agents.py:155-166` (HITLApprovalRequest)
- `backend/deep_agent/models/agents.py:223-234` (HITLApprovalResponse)

**Current Duplication:**
```python
@field_validator("run_id", "thread_id", mode="before")
@classmethod
def strip_and_validate_string(cls, v: Any) -> str:
    """Strip whitespace and validate string is not empty."""
    if not isinstance(v, str):
        raise ValueError("Value must be a string")

    stripped = v.strip()
    if not stripped:
        raise ValueError("Value cannot be empty or whitespace-only")

    return stripped
```

**Recommended Solution:**

**Option 1:** Create shared validator utility in `backend/deep_agent/models/validators.py`:
```python
"""Shared Pydantic validators for Deep Agent models."""
from typing import Any

from pydantic import field_validator


def strip_and_validate_string_field(v: Any) -> str:
    """
    Strip whitespace and validate string is not empty.

    Shared validator for string fields across all models.

    Args:
        v: Value to validate

    Returns:
        Stripped string

    Raises:
        ValueError: If value is not a string or is empty/whitespace-only
    """
    if not isinstance(v, str):
        raise ValueError("Value must be a string")

    stripped = v.strip()
    if not stripped:
        raise ValueError("Value cannot be empty or whitespace-only")

    return stripped
```

Then in models:
```python
from backend.deep_agent.models.validators import strip_and_validate_string_field

class AgentRunInfo(BaseModel):
    # ...

    @field_validator("run_id", "thread_id", mode="before")
    @classmethod
    def strip_and_validate_string(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        return strip_and_validate_string_field(v)
```

**Option 2:** Create base model class (more comprehensive):
```python
class BaseAgentModel(BaseModel):
    """Base model with common validators for agent models."""

    @field_validator("*", mode="before")
    @classmethod
    def strip_and_validate_string(cls, v: Any, field: FieldInfo) -> Any:
        """Strip whitespace and validate string fields are not empty."""
        if not isinstance(v, str):
            return v  # Only process strings

        stripped = v.strip()
        if not stripped and field.is_required():
            raise ValueError(f"{field.field_name} cannot be empty or whitespace-only")

        return stripped if stripped else v

class AgentRunInfo(BaseAgentModel):
    # Inherits validator, no need to duplicate
    ...
```

**Impact:** LOW - Code duplication exists but doesn't affect functionality. Should be addressed in Phase 1 when broader model refactoring occurs.

**Benefits:**
- Single source of truth for string validation
- Easier to enhance validation logic (e.g., add Unicode normalization)
- Reduces code duplication by ~30 lines
- Improves maintainability

**Trade-offs:**
- Option 1: Adds one more import per model file
- Option 2: More invasive refactoring, affects all models

**Note:** This same duplication exists in `chat.py` models (lines 60-71, 112-123, 179-190, 245-256). Should be addressed consistently across all models.

**Found in:** Agent Models Code Review (2025-10-07)

---

## Issue 22: Migrate from deprecated `datetime.utcnow()` to `datetime.now(timezone.utc)`

**Labels:** `technical-debt`, `python-3.12`, `low-priority`, `phase-1`

**Title:** Replace deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` in all models

**Description:**
The `datetime.utcnow()` method is deprecated as of Python 3.12 in favor of `datetime.now(timezone.utc)`. All timestamp fields using `default_factory=datetime.utcnow` should be updated for future Python compatibility.

**Files Affected:**
- `backend/deep_agent/models/agents.py:71` (AgentRunInfo.started_at)
- `backend/deep_agent/models/chat.py:56` (Message.timestamp)
- `backend/deep_agent/models/chat.py:237` (StreamEvent.timestamp)

**Current Code:**
```python
from datetime import datetime

started_at: datetime = Field(
    default_factory=datetime.utcnow,
    description="When the run started",
)
```

**Recommended:**
```python
from datetime import datetime, timezone

started_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="When the run started (UTC)",
)
```

**Impact:** LOW - Python 3.12 compatibility. Not urgent for Phase 0 as project currently uses Python 3.11.

**Benefits:**
- Future-proof for Python 3.12+
- Explicit timezone awareness (better practice)
- Aligns with modern Python datetime best practices
- Consistent across all timestamp fields

**Migration Steps:**
1. Update all 3 occurrences in models
2. Add timezone import where needed
3. Update field descriptions to clarify UTC timezone
4. Run existing tests (should pass without changes)

**Python Version Timeline:**
- Python 3.11: `datetime.utcnow()` works but soft-deprecated
- Python 3.12+: May show deprecation warnings
- Future versions: May be removed entirely

**Found in:** Agent Models Code Review (2025-10-07)

---

## Issue 23: Duplicate CORS origin parsing logic in main.py and settings.py

**Labels:** `refactoring`, `technical-debt`, `medium-priority`, `phase-1`

**Title:** Use `Settings.cors_origins_list` property instead of inline parsing in main.py

**Description:**
The CORS origin parsing logic (`settings.CORS_ORIGINS.split(",")`) is duplicated between `main.py` (lines 114-116) and the `Settings.cors_origins_list` property in `settings.py`. This violates the DRY principle and creates potential for inconsistency if the parsing logic needs enhancement (e.g., URL validation).

**Files:**
- `backend/deep_agent/main.py:114-116`
- `backend/deep_agent/config/settings.py:143-145` (has cors_origins_list property)

**Current Code (main.py):**
```python
allowed_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",")
]
```

**Expected:**
```python
allowed_origins = settings.cors_origins_list  # Use the property
```

**Impact:** MEDIUM - Code duplication. Should be fixed in Phase 1 refactoring. Not blocking for Phase 0 as current implementation works correctly.

**Benefits:**
- Single source of truth for origin parsing
- Easier to enhance (e.g., add URL validation)
- Better maintainability
- Reduces duplication

**Found in:** FastAPI App Code Review (2025-10-07)

---

## Issue 24: Logging initialization should occur in lifespan startup

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-1`

**Title:** Initialize structlog configuration in FastAPI lifespan startup

**Description:**
Logging configuration should be initialized during application startup (in the lifespan context manager) rather than relying on lazy initialization. This ensures consistent logging format/level from the very first log message and respects `LOG_LEVEL` and `LOG_FORMAT` settings.

**File:** `backend/deep_agent/main.py:59-66`

**Impact:** MEDIUM - Logging currently works via lazy initialization, but explicit startup configuration ensures consistency.

**Benefits:**
- Ensures consistent logging format from first log message
- Respects `LOG_LEVEL` and `LOG_FORMAT` settings explicitly
- Makes logging configuration visible in startup flow

**Found in:** FastAPI App Code Review (2025-10-07)

---

## Issue 25: Add request timeout middleware

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-1`, `infrastructure`

**Title:** Implement request timeout enforcement middleware

**Description:**
Phase 0 requirements specify "Request timeout: 300 seconds" as an infrastructure feature. FastAPI doesn't enforce request timeouts by default. While the `REQUEST_TIMEOUT` setting exists (300s), it's not actively enforced. Long-running requests could tie up resources.

**Impact:** MEDIUM - Not critical for Phase 0 single-instance dev environment, but should be implemented for Phase 1 production deployment.

**Settings Already Defined:** `REQUEST_TIMEOUT: int = 300` in settings.py

**Found in:** FastAPI App Code Review (2025-10-07)

---

## Issue 26: Enhance health endpoint with dependency status checks

**Labels:** `enhancement`, `observability`, `low-priority`, `phase-1`

**Title:** Add dependency health checks to `/health` endpoint

**Description:**
The current health endpoint only returns `{"status": "healthy"}` without checking dependencies like database connectivity, LLM API availability, or MCP server status. Enhanced health checks would improve observability and enable better monitoring/alerting.

**File:** `backend/deep_agent/main.py:261-268`

**Impact:** LOW - Basic health check is sufficient for Phase 0. Enhanced checks recommended for Phase 1 production deployment.

**Found in:** FastAPI App Code Review (2025-10-07)

---

## Issue 27: TODO comment should reference Layer 6 implementation phase

**Labels:** `documentation`, `low-priority`, `phase-0`

**Title:** Update TODO comment to reference Layer 6 in development roadmap

**Description:**
The TODO comment for API router inclusion doesn't reference the specific development phase/layer where routers will be implemented.

**File:** `backend/deep_agent/main.py:271-275`

**Impact:** VERY LOW - Documentation clarity improvement.

**Found in:** FastAPI App Code Review (2025-10-07)

---

## Issue 28: Version string hardcoded in FastAPI app creation

**Labels:** `technical-debt`, `enhancement`, `low-priority`, `phase-1`

**Title:** Load app version from pyproject.toml or settings instead of hardcoding

**Description:**
The FastAPI app version is hardcoded as `"0.1.0"` instead of being loaded from a single source of truth.

**File:** `backend/deep_agent/main.py:107`

**Impact:** LOW - Minor quality improvement. Hardcoded version is acceptable for Phase 0.

**Found in:** FastAPI App Code Review (2025-10-07)

---

## Issue 29: Extract secret patterns to shared configuration constant

**Labels:** `refactoring`, `security`, `low-priority`, `phase-1`

**Title:** Centralize API key/secret patterns for consistent sanitization

**Description:**
Secret pattern sanitization logic is duplicated in chat.py (lines 140, 263 - POST /chat and POST /chat/stream). These patterns should be extracted to a shared constant for maintainability and consistency.

**Files:**
- `backend/deep_agent/api/v1/chat.py:140, 263`

**Current Code:**
```python
if any(pattern in error_msg for pattern in ["sk-", "lsv2_", "key=", "token=", "password="]):
    error_msg = "[REDACTED: Potential secret in error message]"
```

**Suggested Fix:**
Create `backend/deep_agent/core/security.py` or add to `backend/deep_agent/core/errors.py`:
```python
# Secret patterns to detect in error messages
SECRET_PATTERNS = [
    "sk-",        # OpenAI API keys
    "lsv2_",      # LangSmith tokens
    "key=",       # Generic key parameters
    "token=",     # Generic token parameters
    "password=",  # Passwords
]

def sanitize_error_message(error_msg: str) -> str:
    """Sanitize error messages to prevent secret leakage."""
    if any(pattern in error_msg for pattern in SECRET_PATTERNS):
        return "[REDACTED: Potential secret in error message]"
    return error_msg
```

**Impact:** LOW - Code duplication. Current implementation works correctly.

**Benefits:**
- Single source of truth for secret patterns
- Easier to add new patterns (just update one list)
- Consistent sanitization across all endpoints
- Testable in isolation

**Found in:** Streaming Endpoint Code Review (2025-10-19)

---

## Issue 30: Add timeout protection to streaming endpoint

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-1`

**Title:** Implement timeout for long-running SSE streams

**Description:**
The POST /chat/stream endpoint doesn't enforce a timeout, potentially allowing infinite-duration streams that could exhaust server resources. Adding a configurable timeout would prevent resource exhaustion.

**File:** `backend/deep_agent/api/v1/chat.py:220-284`

**Recommended Implementation:**
```python
import asyncio
from backend.deep_agent.config.settings import get_settings

async def event_generator() -> AsyncGenerator[str, None]:
    """Generate SSE-formatted events from agent stream."""
    settings = get_settings()
    
    try:
        service = AgentService()
        
        # Add timeout protection (default: 5 minutes)
        timeout_seconds = settings.STREAM_TIMEOUT or 300
        
        async with asyncio.timeout(timeout_seconds):
            async for event in service.stream(
                message=request_body.message,
                thread_id=request_body.thread_id,
            ):
                event_json = json.dumps(event)
                yield f"data: {event_json}\n\n"
                
    except asyncio.TimeoutError:
        logger.warning(
            "Chat stream timeout",
            request_id=request_id,
            thread_id=request_body.thread_id,
            timeout=timeout_seconds,
        )
        error_event = {
            "event_type": "error",
            "data": {
                "error": f"Stream timeout exceeded ({timeout_seconds}s)",
                "status": "timeout"
            },
        }
        yield f"data: {json.dumps(error_event)}\n\n"
```

**Configuration Addition:**
```python
# In backend/deep_agent/config/settings.py
STREAM_TIMEOUT: int = Field(
    default=300,
    description="Maximum duration for SSE streams (seconds)",
)
```

**Impact:** MEDIUM - Not critical for Phase 0 single-user dev, important for production.

**Benefits:**
- Prevents resource exhaustion from stuck/infinite streams
- Configurable per-environment (dev vs prod)
- Graceful timeout with error event sent to client
- Better observability (timeout logged)

**Found in:** Streaming Endpoint Code Review (2025-10-19)

---

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

**Suggested Enhancement:**
```python
from backend.deep_agent.integrations.ag_ui import transform_to_ag_ui_event

async for event in service.stream(
    message=request_body.message,
    thread_id=request_body.thread_id,
):
    # Transform LangChain event to AG-UI Protocol format
    ag_ui_event = transform_to_ag_ui_event(event, thread_id=request_body.thread_id)
    
    if ag_ui_event:  # Some events may be filtered
        event_json = json.dumps(ag_ui_event)
        yield f"data: {event_json}\n\n"
```

**Implementation Location:** `backend/deep_agent/integrations/ag_ui.py`

**Required AG-UI Events (per CLAUDE.md):**
- **Lifecycle:** RunStarted, RunFinished, RunError
- **Steps:** StepStarted, StepFinished
- **Messages:** TextMessageStart, TextMessageContent, TextMessageEnd
- **Tools:** ToolCallStart, ToolCallArgs, ToolCallEnd, ToolCallResult
- **HITL:** Custom events for approval workflows

**Impact:** MEDIUM - Required for Layer 7 (Frontend AG-UI implementation), not blocking for Layer 6.

**Benefits:**
- Frontend receives properly formatted events
- Consistent event structure across UI
- Enables AG-UI features (progress tracking, tool transparency, HITL)
- Decouples backend event format from frontend expectations

**Dependencies:**
- Requires AG-UI SDK integration (Layer 7)
- Event mapping logic needs LangChain event documentation

**Found in:** Streaming Endpoint Code Review (2025-10-19)

---
