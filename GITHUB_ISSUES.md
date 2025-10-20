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

## Issue 32: Fix bare except clause in WebSocket endpoint ✅ RESOLVED

**Labels:** `bug`, `code-quality`, `medium-priority`, `phase-0`

**Title:** Replace bare except with specific exception types in websocket.py

**Description:**
The WebSocket endpoint uses a bare `except:` clause which catches all exceptions including system-level ones like KeyboardInterrupt and SystemExit. This can prevent graceful shutdown and hide real bugs.

**File:** `backend/deep_agent/api/v1/websocket.py:264`

**Current Code:**
```python
try:
    await websocket.close()
except:
    pass  # Connection may already be closed
```

**Expected:**
```python
try:
    await websocket.close()
except (WebSocketDisconnect, RuntimeError):
    pass  # Connection may already be closed
```

**Impact:** MEDIUM - Could prevent graceful shutdown, mask real errors, break async task cancellation.

**Why This Matters:**
- Bare `except:` catches KeyboardInterrupt (Ctrl+C) → prevents user from stopping app
- Catches SystemExit → prevents application from exiting cleanly
- Catches asyncio.CancelledError → breaks async task cancellation
- Hides real bugs that should be surfaced

**Linter:** Ruff (E722) - "Do not use bare `except`"

**Found in:** WebSocket Endpoint Linting Review (2025-10-19)

---

## Issue 33: Modernize typing.Dict to dict in WebSocket endpoint ✅ RESOLVED

**Labels:** `technical-debt`, `code-quality`, `low-priority`, `phase-0`

**Title:** Replace deprecated typing.Dict with built-in dict type

**Description:**
The WebSocket endpoint uses `typing.Dict` which is deprecated in Python 3.9+ per PEP 585. Python 3.10+ (our target) uses the built-in `dict` type directly for type annotations.

**Files:**
- `backend/deep_agent/api/v1/websocket.py:9` (import statement)
- `backend/deep_agent/api/v1/websocket.py:45` (type annotation)

**Current Code:**
```python
# Line 9
from typing import Any, Dict

# Line 45
metadata: Dict[str, Any] | None = Field(...)
```

**Expected:**
```python
# Line 9
from typing import Any

# Line 45
metadata: dict[str, Any] | None = Field(...)
```

**Impact:** LOW - Pure style/modernization issue. No functional impact.

**Benefits:**
- Follows Python 3.10+ best practices (PEP 585)
- Consistent with modern Python idioms
- Simpler syntax (no import needed)
- Aligns with rest of codebase

**Linter:** Ruff (UP035, UP006) - "`typing.Dict` is deprecated, use `dict` instead"

**Fix Strategy:** Find/replace all `Dict[` → `dict[` in file

**Found in:** WebSocket Endpoint Linting Review (2025-10-19)

---

## Issue 34: Fix bare except clauses in WebSocket test file ✅ RESOLVED

**Labels:** `bug`, `testing`, `code-quality`, `medium-priority`, `phase-0`

**Title:** Replace bare except with specific exception types in test_websocket.py

**Description:**
The WebSocket integration tests use bare `except:` clauses when receiving WebSocket events. This caused tests to hang indefinitely when `receive_json()` waits for events that never arrive, because no timeout exceptions were ever caught.

**File:** `tests/integration/test_api_endpoints/test_websocket.py`

**Locations Fixed:**
- Line 107: `test_websocket_accepts_chat_message`
- Line 138: `test_websocket_streams_multiple_events`
- Line 228: `test_websocket_handles_agent_error`
- Line 287: `test_websocket_handles_concurrent_messages` (first loop)
- Line 303: `test_websocket_handles_concurrent_messages` (second loop)

**Current Code:**
```python
try:
    event = websocket.receive_json()
    events.append(event)
except:  # BAD - hangs indefinitely
    break
```

**Fixed Code:**
```python
try:
    event = websocket.receive_json()
    events.append(event)
except (WebSocketDisconnect, Exception):  # GOOD - specific exceptions
    break
```

**Impact:** MEDIUM-HIGH - Tests were hanging for >10 minutes each due to this issue.

**Root Cause:**
1. `receive_json()` waits indefinitely for events without a timeout
2. Bare `except:` was meant to catch exceptions and break the loop
3. Without timeouts, no exceptions were raised → infinite wait
4. Bare `except:` also catches system exceptions (KeyboardInterrupt, SystemExit)

**Benefits of Fix:**
- Tests no longer hang indefinitely
- Proper exception handling (doesn't catch system-level exceptions)
- Follows Python best practices (explicit exception types)
- Consistent with production code (Issue #32)

**Linter:** Ruff (E722) - "Do not use bare `except`"

**Resolution:** Fixed in commit alongside Issue #32 and #33 (2025-10-19)

**Found in:** WebSocket Test Investigation (2025-10-19)

---

## Issue 35: Playwright WebSocket tests assume unimplemented UI components

**Labels:** `testing`, `ui`, `medium-priority`, `phase-0-layer-7`

**Title:** WebSocket UI tests depend on chat interface not yet implemented

**Description:**
All Playwright tests in `test_websocket_connection.py` navigate to `http://localhost:3000/chat` and expect specific data-testid attributes that don't exist yet. According to CLAUDE.md Layer 7 TODO list, the chat interface hasn't been implemented. Tests will fail immediately until UI components are created.

**File:** `tests/ui/test_websocket_connection.py` (all 10 tests)

**Missing Prerequisites:**
- `frontend/app/chat/page.tsx` (not created yet)
- Required data-testid attributes:
  - `[data-testid="ws-status"]` - Connection status indicator
  - `[data-testid="message-input"]` - Message input field
  - `[data-testid="send-button"]` - Send message button
  - `[data-testid="chat-history"]` - Chat message display
  - `[data-testid="ws-error"]` - Error indicator

**Impact:** MEDIUM - Tests cannot run until Layer 7 UI components exist. This creates a dependency order issue for TDD workflow.

**Recommended Solutions:**

**Option 1: Skip tests until UI ready (quick fix)**
```python
@pytest.mark.skip(reason="Pending Layer 7 UI implementation (ChatInterface)")
class TestWebSocketConnection:
    ...
```

**Option 2: Implement tests alongside UI (TDD best practice)**
- Create chat interface first (Layer 7 TODO)
- Implement tests as UI components are built
- Ensure data-testid attributes match test expectations

**Option 3: Create minimal test harness (compromise)**
Create `tests/ui/fixtures/websocket_test_page.html`:
```html
<!DOCTYPE html>
<html>
<body>
  <div data-testid="ws-status">disconnected</div>
  <input data-testid="message-input" type="text" />
  <button data-testid="send-button">Send</button>
  <div data-testid="chat-history"></div>
  <div data-testid="ws-error" style="display:none"></div>
  <script src="useWebSocket-bundle.js"></script>
</body>
</html>
```

**Benefits:**
- Option 1: Unblocks other testing work
- Option 2: Follows TDD principles correctly
- Option 3: Allows hook testing independently of full UI

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 36: Missing Playwright configuration for UI tests

**Labels:** `testing`, `ui`, `configuration`, `medium-priority`, `phase-0`

**Title:** Add conftest.py with Playwright fixtures and configuration

**Description:**
Playwright UI tests use `page: Page` fixture but there's no `conftest.py` to provide Playwright configuration. Tests need proper setup including browser context, base URL, timeout settings, and screenshot-on-failure.

**Missing File:** `tests/ui/conftest.py`

**Current Impact:** Tests likely won't run or will use default Playwright configuration without project-specific settings.

**Required Configuration:**

```python
"""Playwright UI test configuration and fixtures."""
import pytest
from playwright.sync_api import Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": "test-results/videos",
        "record_video_size": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="session")
def base_url():
    """Base URL for frontend application."""
    return "http://localhost:3000"


@pytest.fixture
def page(page: Page, base_url: str):
    """Page fixture with base URL configured."""
    page.set_default_timeout(10000)  # 10s default timeout
    yield page
    # Screenshot on failure handled by pytest-playwright


@pytest.fixture(scope="session", autouse=True)
def verify_backend_running():
    """Ensure backend WebSocket server is running before tests."""
    import requests
    import websocket

    try:
        # Check health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200

        # Test WebSocket connection
        ws = websocket.create_connection(
            "ws://localhost:8000/api/v1/ws",
            timeout=5
        )
        ws.close()
    except Exception as e:
        pytest.skip(f"Backend server not available: {e}")


@pytest.fixture(scope="session", autouse=True)
def verify_frontend_running(base_url: str):
    """Ensure frontend is running before tests."""
    import requests

    try:
        response = requests.get(base_url, timeout=5)
        assert response.status_code == 200
    except Exception as e:
        pytest.skip(f"Frontend not available at {base_url}: {e}")
```

**Additional Configuration Files:**

**pytest.ini section for UI tests:**
```ini
[tool:pytest]
markers =
    ui: Playwright UI tests (slow, require frontend/backend running)

# Playwright settings
playwright_timeout = 30000
playwright_headed = false
playwright_slow_mo = 0
playwright_browser = chromium
```

**Benefits:**
- Proper browser configuration
- Automatic video recording on failure
- Backend/frontend availability checks (skip tests if not running)
- Consistent timeout settings
- Better test isolation

**Impact:** MEDIUM - Tests can't run reliably without proper configuration.

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 37: Weak assertions in WebSocket tests don't verify connection state

**Labels:** `testing`, `ui`, `enhancement`, `medium-priority`, `phase-0`

**Title:** Strengthen WebSocket status assertions to verify actual connection state

**Description:**
WebSocket tests use `to_have_text("connected")` to verify connection status, but this only checks UI text without verifying the underlying WebSocket connection state. The text could be hardcoded or come from any source.

**Files:** `tests/ui/test_websocket_connection.py` (lines 28, 35, 54, 72, 92, 112, 127, 148, 168)

**Current Code:**
```python
connection_status = page.locator('[data-testid="ws-status"]')
expect(connection_status).to_have_text("connected", timeout=5000)
```

**Problem:**
- Doesn't verify WebSocket is actually open
- Text could be static or mocked
- No state machine verification
- Doesn't check WebSocket readyState

**Recommended Improvement:**

**UI Implementation:** Add data attribute for state
```tsx
// In ChatInterface or WebSocket status component
<div
  data-testid="ws-status"
  data-status={connectionStatus}  // "connecting" | "connected" | "disconnected" | "reconnecting"
  data-ready-state={ws?.readyState}  // WebSocket.OPEN = 1
>
  {connectionStatus}
</div>
```

**Test Code:**
```python
connection_status = page.locator('[data-testid="ws-status"]')

# Verify initial state
expect(connection_status).to_have_attribute("data-status", "connecting")

# Wait for connected state
expect(connection_status).to_have_attribute("data-status", "connected", timeout=5000)

# Verify WebSocket readyState
expect(connection_status).to_have_attribute("data-ready-state", "1")  # OPEN

# Also verify text for user visibility
expect(connection_status).to_have_text("connected")
```

**Benefits:**
- Verifies actual WebSocket state (not just UI text)
- Can differentiate between connection states
- Catches bugs where UI shows "connected" but WebSocket is broken
- Tests state machine transitions properly

**Impact:** MEDIUM - Current tests may pass even if WebSocket isn't actually connected.

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 38: WebSocket tests don't verify AG-UI Protocol events received

**Labels:** `testing`, `ui`, `enhancement`, `medium-priority`, `phase-0-layer-7`

**Title:** Add assertions to verify AG-UI Protocol events are received and displayed

**Description:**
Tests `test_websocket_receives_events()` and `test_websocket_multiple_threads()` claim to verify AG-UI event handling but only check for generic "assistant" text. They don't verify specific AG-UI Protocol events (RunStartedEvent, TextMessageContentEvent, RunFinishedEvent) are received and processed correctly.

**Files:** `tests/ui/test_websocket_connection.py:49-65, 163-182`

**Current Code:**
```python
def test_websocket_receives_events(self, page: Page) -> None:
    """Test WebSocket receives AG-UI events from backend."""
    # ... send message ...

    # Wait for streaming response (AG-UI events)
    # Should see assistant message appear
    chat_history = page.locator('[data-testid="chat-history"]')
    expect(chat_history).to_contain_text("assistant", timeout=10000)
```

**What's Missing:**
- No verification of RunStartedEvent received
- No verification of streaming tokens (TextMessageContentEvent)
- No verification of RunFinishedEvent received
- No verification of tool call events
- No verification of event order/sequence

**Recommended Implementation:**

**UI Changes Needed:**
```tsx
// In chat interface, render AG-UI events for testing
{events.map(event => (
  <div
    key={event.run_id}
    data-testid={`event-${event.event}`}
    data-event-type={event.event}
    data-run-id={event.run_id}
  >
    {/* Event content */}
  </div>
))}
```

**Test Code:**
```python
def test_websocket_receives_events(self, page: Page) -> None:
    """Test WebSocket receives AG-UI events from backend."""
    # Arrange
    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Act: Send message
    page.fill('[data-testid="message-input"]', "Test message")
    page.click('[data-testid="send-button"]')

    # Assert: Verify AG-UI Protocol event sequence

    # 1. RunStartedEvent (on_chain_start or on_llm_start)
    run_started = page.locator('[data-testid="event-on_chain_start"]').first
    expect(run_started).to_be_visible(timeout=5000)

    # 2. TextMessageContentEvent (streaming tokens)
    message_stream = page.locator('[data-testid="message-stream"]')
    expect(message_stream).to_be_visible()
    expect(message_stream).not_to_be_empty()

    # 3. RunFinishedEvent (on_chain_end or on_llm_end)
    run_finished = page.locator('[data-testid="event-on_chain_end"]').first
    expect(run_finished).to_be_visible(timeout=10000)

    # 4. Verify message in chat history
    chat_history = page.locator('[data-testid="chat-history"]')
    expect(chat_history).to_contain_text("Test message")  # User message
    expect(chat_history).to_contain_text(/\w+/)  # Assistant response (non-empty)
```

**Benefits:**
- Verifies actual AG-UI Protocol implementation
- Catches event parsing errors
- Verifies event order/sequence
- Tests core framework integration (not just UI text)

**Impact:** MEDIUM - Tests don't verify the core functionality they claim to test.

**Dependencies:** Requires Layer 7 AG-UI integration (Issue #31 - transform LangChain events to AG-UI format)

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 39: Remove or fix synthetic invalid JSON test

**Labels:** `testing`, `ui`, `bug`, `medium-priority`, `phase-0`

**Title:** Fix test_websocket_invalid_json_error to actually test error handling

**Description:**
The test `test_websocket_invalid_json_error()` admits in its own comments that it's "synthetic" and doesn't actually test invalid JSON handling. It only verifies that an error indicator isn't visible during normal operation, which doesn't test error handling at all.

**File:** `tests/ui/test_websocket_connection.py:107-121`

**Current Code:**
```python
def test_websocket_invalid_json_error(self, page: Page) -> None:
    """Test WebSocket handles invalid JSON gracefully."""
    page.goto("http://localhost:3000/chat")

    # Wait for connection
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Inject invalid JSON via console (simulate error)
    # This is a synthetic test - real implementation would handle parse errors
    # We verify error state is shown
    error_indicator = page.locator('[data-testid="ws-error"]')

    # In normal operation, error should not be visible
    expect(error_indicator).not_to_be_visible()
```

**Problem:**
- Docstring says "handles invalid JSON gracefully" but test doesn't inject invalid JSON
- Test only verifies error indicator hidden during normal operation
- No actual error handling tested
- Provides zero coverage of JSON parsing error paths

**Recommended Solutions:**

**Option 1: Remove the test (simplest)**
```python
# Delete test_websocket_invalid_json_error() entirely
# Invalid JSON from backend would be caught by backend tests, not UI tests
```

**Option 2: Test real error handling via backend mock**
```python
def test_websocket_invalid_json_error(self, page: Page) -> None:
    """Test WebSocket handles invalid JSON gracefully."""
    # Arrange: Set up route to inject bad JSON
    page.route("**/api/v1/ws", lambda route: route.fulfill(
        body="{invalid json}",  # Malformed JSON
        headers={"Content-Type": "application/json"}
    ))

    page.goto("http://localhost:3000/chat")

    # Act: Try to connect (will receive invalid JSON)

    # Assert: Error state shown
    error_indicator = page.locator('[data-testid="ws-error"]')
    expect(error_indicator).to_be_visible(timeout=5000)
    expect(error_indicator).to_contain_text("Failed to parse")

    # Connection status should show error
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("error")
```

**Option 3: Use console injection (complex, brittle)**
```python
# Use page.evaluate() to simulate parse error in WebSocket handler
# Not recommended - too coupled to implementation details
```

**Recommendation:** Option 1 (remove test) is best. Invalid JSON errors should be tested at the integration level (backend tests), not UI tests. UI tests should focus on user-visible error states, not low-level parsing errors.

**Impact:** MEDIUM - Test provides zero value and misleads about coverage.

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 40: Missing edge case tests for WebSocket hook

**Labels:** `testing`, `ui`, `enhancement`, `low-priority`, `phase-0`

**Title:** Add edge case tests for WebSocket error conditions

**Description:**
The WebSocket test suite covers happy paths and basic error scenarios, but misses important edge cases that could cause issues in production.

**File:** `tests/ui/test_websocket_connection.py`

**Missing Test Cases:**

**1. Send message before connection established**
```python
def test_websocket_send_before_connected(self, page: Page) -> None:
    """Test sending message before WebSocket connects is handled gracefully."""
    # Arrange: Navigate but don't wait for connection
    page.goto("http://localhost:3000/chat")

    # Act: Try to send immediately (before connected)
    page.fill('[data-testid="message-input"]', "Test message")
    page.click('[data-testid="send-button"]')

    # Assert: Error message shown OR message queued until connected
    # (Depends on implementation choice)
```

**2. Rapid reconnection cycling (network flapping)**
```python
def test_websocket_handles_network_flapping(self, page: Page) -> None:
    """Test WebSocket handles rapid connect/disconnect cycles."""
    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected")

    # Rapidly toggle network on/off 5 times
    for i in range(5):
        page.context.set_offline(True)
        page.wait_for_timeout(100)
        page.context.set_offline(False)
        page.wait_for_timeout(100)

    # Should eventually stabilize to connected
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=15000)
```

**3. Max reconnection attempts (if implemented)**
```python
def test_websocket_max_reconnection_attempts(self, page: Page) -> None:
    """Test WebSocket stops reconnecting after max attempts."""
    # Only if maxReconnectAttempts is implemented in useWebSocket
    # Verify it gives up after N attempts and shows permanent error
```

**4. Large message handling**
```python
def test_websocket_handles_large_messages(self, page: Page) -> None:
    """Test WebSocket handles or rejects very large messages."""
    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected")

    # Try to send 10MB message
    large_message = "A" * (10 * 1024 * 1024)
    page.fill('[data-testid="message-input"]', large_message)

    # Should either:
    # 1. Show validation error (recommended)
    # 2. Send successfully if backend supports it
    # 3. Show network error if too large
```

**5. Concurrent disconnect during reconnection**
```python
def test_websocket_disconnect_during_reconnection(self, page: Page) -> None:
    """Test disconnect() called during active reconnection attempt."""
    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected")

    # Trigger disconnect
    page.context.set_offline(True)
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("reconnecting", timeout=3000)

    # Navigate away during reconnection (calls disconnect())
    page.goto("http://localhost:3000/")

    # Should cleanly disconnect without errors
    # Check console for errors
```

**Impact:** LOW - Edge cases unlikely in normal operation but would improve robustness.

**Benefits:**
- Catches rare but critical bugs
- Improves production reliability
- Demonstrates thorough testing
- Prevents user-facing errors in edge conditions

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 41: WebSocket tests missing performance assertions

**Labels:** `testing`, `ui`, `enhancement`, `low-priority`, `phase-0`

**Title:** Add performance metrics to WebSocket tests for regression detection

**Description:**
WebSocket tests verify functionality but don't measure or assert on performance characteristics like connection time, message latency, or reconnection speed. Adding performance metrics would enable regression detection.

**File:** `tests/ui/test_websocket_connection.py`

**Missing Metrics:**

**1. Connection establishment time**
```python
def test_websocket_connection_performance(self, page: Page) -> None:
    """Test WebSocket connects within acceptable time."""
    import time

    # Measure connection time
    start = time.time()
    page.goto("http://localhost:3000/chat")

    connection_status = page.locator('[data-testid="ws-status"]')
    expect(connection_status).to_have_text("connected", timeout=5000)

    connection_time = time.time() - start

    # Assert reasonable connection time
    assert connection_time < 2.0, f"Connection took {connection_time:.2f}s (expected <2s)"
    print(f"✓ Connection established in {connection_time:.2f}s")
```

**2. Message roundtrip latency**
```python
def test_websocket_message_latency(self, page: Page) -> None:
    """Test message roundtrip time is acceptable."""
    import time

    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected")

    # Send message and measure response time
    start = time.time()
    page.fill('[data-testid="message-input"]', "Test latency")
    page.click('[data-testid="send-button"]')

    # Wait for response
    chat_history = page.locator('[data-testid="chat-history"]')
    expect(chat_history).to_contain_text("assistant", timeout=10000)

    latency = time.time() - start

    # Per Phase 0 requirements: <2s for simple queries
    assert latency < 2.0, f"Message roundtrip took {latency:.2f}s (expected <2s)"
    print(f"✓ Message roundtrip in {latency:.2f}s")
```

**3. Reconnection speed**
```python
def test_websocket_reconnection_speed(self, page: Page) -> None:
    """Test reconnection completes within reasonable time."""
    import time

    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected")

    # Trigger disconnect and measure reconnection time
    start = time.time()
    page.context.set_offline(True)
    page.wait_for_timeout(100)
    page.context.set_offline(False)

    # Wait for reconnection
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=10000)

    reconnect_time = time.time() - start

    # Should reconnect within 5 seconds (first attempt, no backoff)
    assert reconnect_time < 5.0, f"Reconnection took {reconnect_time:.2f}s (expected <5s)"
    print(f"✓ Reconnected in {reconnect_time:.2f}s")
```

**4. Memory usage tracking (advanced)**
```python
def test_websocket_memory_usage(self, page: Page) -> None:
    """Test WebSocket doesn't leak memory over extended session."""
    page.goto("http://localhost:3000/chat")

    # Get initial memory
    initial_memory = page.evaluate("() => performance.memory.usedJSHeapSize")

    # Send 100 messages
    for i in range(100):
        page.fill('[data-testid="message-input"]', f"Message {i}")
        page.click('[data-testid="send-button"]')
        page.wait_for_timeout(100)

    # Check memory hasn't grown excessively
    final_memory = page.evaluate("() => performance.memory.usedJSHeapSize")
    memory_growth = (final_memory - initial_memory) / (1024 * 1024)  # MB

    # Memory growth should be reasonable (<50MB for 100 messages)
    assert memory_growth < 50, f"Memory grew {memory_growth:.2f}MB (expected <50MB)"
    print(f"✓ Memory growth: {memory_growth:.2f}MB")
```

**Impact:** VERY LOW - Nice to have for performance regression detection, not critical for Phase 0.

**Benefits:**
- Detects performance regressions early
- Validates Phase 0 success criteria (latency <2s)
- Provides baseline metrics for optimization
- Catches memory leaks before production

**Trade-offs:**
- Performance tests can be flaky (network variance)
- May need to run multiple times and average results
- Thresholds may need adjustment per environment

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 42: WebSocket tests don't follow AAA pattern consistently

**Labels:** `testing`, `ui`, `code-quality`, `low-priority`, `phase-0`

**Title:** Improve test readability by consistently applying AAA pattern with clear comments

**Description:**
While most tests loosely follow Arrange-Act-Assert pattern, some have implicit arrange phases mixed with act phases, making tests harder to read and understand. Adding clear section comments would improve maintainability.

**File:** `tests/ui/test_websocket_connection.py` (multiple tests)

**Current Code Example:**
```python
def test_websocket_sends_valid_message(self, page: Page) -> None:
    """Test WebSocket sends properly formatted messages."""
    page.goto("http://localhost:3000/chat")  # Arrange part 1

    # Wait for connection  # Still Arrange
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Type message and send  # Act part 1
    message_input = page.locator('[data-testid="message-input"]')
    message_input.fill("Hello from test")

    send_button = page.locator('[data-testid="send-button"]')  # Act part 2
    send_button.click()

    # Verify message was sent  # Assert
    chat_history = page.locator('[data-testid="chat-history"]')
    expect(chat_history).to_contain_text("Hello from test", timeout=3000)
```

**Improved Structure:**
```python
def test_websocket_sends_valid_message(self, page: Page) -> None:
    """Test WebSocket sends properly formatted messages."""
    # Arrange: Navigate to chat and wait for connection
    page.goto("http://localhost:3000/chat")
    connection_status = page.locator('[data-testid="ws-status"]')
    expect(connection_status).to_have_text("connected", timeout=5000)

    # Act: Type and send message
    page.fill('[data-testid="message-input"]', "Hello from test")
    page.click('[data-testid="send-button"]')

    # Assert: Message appears in chat history
    chat_history = page.locator('[data-testid="chat-history"]')
    expect(chat_history).to_contain_text("Hello from test", timeout=3000)
```

**Benefits:**
- Clear separation of test phases
- Easier to understand test flow at a glance
- Simplifies debugging (know which phase failed)
- Better maintainability
- Consistent with other test files in project

**Pattern to Apply:**
```python
# Arrange: [Description of setup]
# ... setup code ...

# Act: [Description of action]
# ... action code ...

# Assert: [Description of expectation]
# ... assertion code ...
```

**Impact:** VERY LOW - Pure readability improvement, no functional change.

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 43: WebSocket cleanup test doesn't verify no memory leaks

**Labels:** `testing`, `ui`, `enhancement`, `low-priority`, `phase-0`

**Title:** Add memory leak detection to useWebSocket cleanup test

**Description:**
The test `test_websocket_cleanup_on_unmount()` verifies reconnection after unmount but doesn't check for memory leaks from duplicate WebSocket connections. The comment says "prevents memory leaks" but test doesn't verify this claim.

**File:** `tests/ui/test_websocket_connection.py:183-202`

**Current Code:**
```python
def test_websocket_cleanup_on_unmount(self, page: Page) -> None:
    """Test WebSocket connection closes when component unmounts."""
    page.goto("http://localhost:3000/chat")

    # Wait for connection
    connection_status = page.locator('[data-testid="ws-status"]')
    expect(connection_status).to_have_text("connected", timeout=5000)

    # Navigate away (unmount component)
    page.goto("http://localhost:3000/")

    # Navigate back
    page.goto("http://localhost:3000/chat")

    # Should reconnect
    expect(connection_status).to_have_text("connected", timeout=5000)

    # Verify no duplicate connections (would show as multiple messages)
    # This is a behavioral test - proper cleanup prevents memory leaks
```

**What's Missing:**
- No verification that old WebSocket was actually closed
- No check for multiple active connections
- No verification of WebSocket count in browser
- Comment claims "prevents memory leaks" but test doesn't verify

**Recommended Enhancement:**
```python
def test_websocket_cleanup_on_unmount(self, page: Page) -> None:
    """Test WebSocket connection closes when component unmounts and doesn't leak."""
    # Arrange: Connect initially
    page.goto("http://localhost:3000/chat")
    connection_status = page.locator('[data-testid="ws-status"]')
    expect(connection_status).to_have_text("connected", timeout=5000)

    # Act: Navigate away (unmount) and back (remount)
    page.goto("http://localhost:3000/")
    page.wait_for_timeout(500)  # Ensure cleanup completes
    page.goto("http://localhost:3000/chat")

    # Assert: Reconnects successfully
    expect(connection_status).to_have_text("connected", timeout=5000)

    # Assert: No duplicate WebSocket connections
    # Check performance API for WebSocket connection count
    ws_connections = page.evaluate("""() => {
        // Count active WebSocket connections via performance API
        const entries = performance.getEntriesByType('resource');
        return entries.filter(e =>
            e.name.includes('/ws') &&
            e.initiatorType === 'websocket'
        ).length;
    }""")

    assert ws_connections == 1, f"Expected 1 WebSocket, found {ws_connections} (memory leak?)"

    # Assert: No console errors about failed WebSocket cleanup
    console_logs = []
    page.on("console", lambda msg: console_logs.append(msg.text()))

    # Do another mount/unmount cycle
    page.goto("http://localhost:3000/")
    page.goto("http://localhost:3000/chat")

    # Check for error messages
    error_logs = [log for log in console_logs if "error" in log.lower()]
    assert len(error_logs) == 0, f"Found console errors: {error_logs}"
```

**Alternative Approach (Simpler):**
```python
# Just verify console has no errors and connection works
# Assume React hooks cleanup properly (they do in React 18+)
# Memory leak testing is better suited for long-running E2E tests
```

**Impact:** VERY LOW - Memory leaks unlikely with React hooks' built-in cleanup, but good to verify.

**Benefits:**
- Catches potential useEffect cleanup bugs
- Verifies WebSocket.close() is called
- Demonstrates thorough testing
- Provides confidence in production behavior

**Trade-offs:**
- Browser WebSocket count APIs are limited
- May need platform-specific detection
- More complex test for marginal benefit

**Found in:** Playwright WebSocket Tests Review (2025-10-20)

---

## Issue 44: useWebSocket callback dependency causes infinite reconnection loops

**Labels:** `bug`, `high-priority`, `phase-0-layer-7`, `react`

**Title:** Fix callback dependency issue in useWebSocket hook to prevent infinite reconnection loops

**Description:**
The `connect` function includes `onEvent` and `onError` in its dependency array, but these callbacks can change on every render if passed inline by the parent component. This will trigger infinite reconnection loops when callbacks are recreated on every render.

**File:** `frontend/hooks/useWebSocket.ts:166`

**Current Code:**
```typescript
const connect = useCallback(() => {
  // ... implementation ...
}, [getWebSocketUrl, reconnect, getReconnectDelay, onEvent, onError]);
```

**Problem:**
If parent component passes callbacks like:
```tsx
<Component onEvent={(e) => console.log(e)} />
```
These get recreated every render → `connect` recreates every render → infinite reconnection loops.

**Fix (Option 1 - Recommended):**
```typescript
// Use refs for callbacks
const onEventRef = useRef(onEvent);
const onErrorRef = useRef(onError);

useEffect(() => {
  onEventRef.current = onEvent;
  onErrorRef.current = onError;
}, [onEvent, onError]);

const connect = useCallback(() => {
  // ... implementation ...
  if (onEventRef.current) {
    onEventRef.current(data);
  }
  // ... rest of implementation ...
}, [getWebSocketUrl, reconnect, getReconnectDelay]);
// Remove onEvent, onError from deps ^
```

**Fix (Option 2):**
Document that users MUST memoize callbacks:
```typescript
/**
 * @param onEvent - Callback for AG-UI events. MUST be memoized with useCallback.
 * @param onError - Callback for errors. MUST be memoized with useCallback.
 */
```

**Recommendation:** Use Option 1 (refs) - safer and doesn't rely on user discipline.

**Impact:** HIGH - Can cause infinite loops if callbacks not memoized by parent.

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 45: useWebSocket missing rate limiting for sendMessage

**Labels:** `enhancement`, `security`, `high-priority`, `phase-0-layer-7`

**Title:** Add rate limiting to useWebSocket sendMessage function

**Description:**
Users can spam messages, potentially overwhelming the backend or hitting rate limits. Per Phase 0 requirements, all expensive operations should have rate limiting protection.

**File:** `frontend/hooks/useWebSocket.ts:190-218`

**Recommended Implementation:**
```typescript
// Add rate limiting state
const sendTimestampsRef = useRef<number[]>([]);
const SEND_RATE_LIMIT = 10; // messages
const SEND_RATE_WINDOW = 60000; // 60 seconds

const sendMessage = useCallback(
  (message: string, thread_id: string, metadata?: Record<string, any>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('[useWebSocket] Cannot send message: not connected');
      return;
    }

    // Check rate limit
    const now = Date.now();
    sendTimestampsRef.current = sendTimestampsRef.current.filter(
      (ts) => now - ts < SEND_RATE_WINDOW
    );

    if (sendTimestampsRef.current.length >= SEND_RATE_LIMIT) {
      const rateLimitError = new Error(
        `Rate limit exceeded: ${SEND_RATE_LIMIT} messages per ${SEND_RATE_WINDOW / 1000}s`
      );
      console.error('[useWebSocket]', rateLimitError);
      setError(rateLimitError);

      if (onErrorRef.current) {
        onErrorRef.current(rateLimitError);
      }
      return;
    }

    sendTimestampsRef.current.push(now);

    // ... rest of implementation
  },
  []
);
```

**Impact:** HIGH - Users can spam backend, violates Phase 0 infrastructure requirements.

**Benefits:**
- Prevents backend overload from message spam
- Better user experience (clear rate limit errors)
- Aligns with Phase 0 requirements

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 46: useWebSocket missing max reconnection attempts (infinite retry risk)

**Labels:** `bug`, `reliability`, `high-priority`, `phase-0-layer-7`

**Title:** Implement max reconnection attempts in useWebSocket hook

**Description:**
Network failures or backend downtime could cause infinite reconnection attempts, draining battery on mobile devices and creating unnecessary load. No circuit breaker pattern implemented.

**File:** `frontend/hooks/useWebSocket.ts:142-153`

**Current Code:**
```typescript
// Auto-reconnect if enabled and not a normal closure
if (reconnect && event.code !== 1000) {
  setConnectionStatus('reconnecting');
  reconnectAttemptRef.current += 1;

  const delay = getReconnectDelay();
  console.log(`[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current})`);

  reconnectTimeoutRef.current = setTimeout(() => {
    connect();
  }, delay);
}
```

**Fix:**
```typescript
interface UseWebSocketOptions {
  // ... existing options ...
  maxReconnectAttempts?: number; // Max reconnect attempts (default: 10)
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    // ... existing destructuring ...
    maxReconnectAttempts = 10,
  } = options;

  // In ws.onclose handler:
  ws.onclose = (event) => {
    console.log('[useWebSocket] Disconnected:', event.code, event.reason);
    setConnectionStatus('disconnected');
    wsRef.current = null;

    if (reconnect && event.code !== 1000) {
      reconnectAttemptRef.current += 1;

      // Check max attempts
      if (reconnectAttemptRef.current > maxReconnectAttempts) {
        const maxAttemptsError = new Error(
          `Max reconnection attempts (${maxReconnectAttempts}) exceeded`
        );
        console.error('[useWebSocket]', maxAttemptsError);
        setError(maxAttemptsError);
        setConnectionStatus('error');

        if (onErrorRef.current) {
          onErrorRef.current(maxAttemptsError);
        }
        return; // Stop reconnecting
      }

      setConnectionStatus('reconnecting');
      const delay = getReconnectDelay();
      console.log(
        `[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current}/${maxReconnectAttempts})`
      );

      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    }
  };
}
```

**Impact:** HIGH - Network failures cause infinite retries, battery drain on mobile.

**Benefits:**
- Prevents infinite retry loops
- Better battery life on mobile
- Clear error state when max attempts reached
- User can manually retry if needed

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 47: useWebSocket missing input validation for sendMessage

**Labels:** `enhancement`, `security`, `medium-priority`, `phase-0-layer-7`

**Title:** Add input validation to useWebSocket sendMessage function

**Description:**
Malformed messages could be sent to backend, causing parsing errors or security issues. The `sendMessage` function doesn't validate parameters before sending.

**File:** `frontend/hooks/useWebSocket.ts:191-202`

**Recommended Implementation:**
```typescript
const sendMessage = useCallback(
  (message: string, thread_id: string, metadata?: Record<string, any>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('[useWebSocket] Cannot send message: not connected');
      return;
    }

    // Validate inputs
    if (!message || message.trim().length === 0) {
      const validationError = new Error('Message cannot be empty');
      console.warn('[useWebSocket]', validationError);
      setError(validationError);
      if (onErrorRef.current) {
        onErrorRef.current(validationError);
      }
      return;
    }

    if (!thread_id || thread_id.trim().length === 0) {
      const validationError = new Error('Thread ID is required');
      console.warn('[useWebSocket]', validationError);
      setError(validationError);
      if (onErrorRef.current) {
        onErrorRef.current(validationError);
      }
      return;
    }

    // Limit message length (prevent DoS)
    const MAX_MESSAGE_LENGTH = 10000; // 10KB
    if (message.length > MAX_MESSAGE_LENGTH) {
      const validationError = new Error(
        `Message too long (${message.length} chars, max ${MAX_MESSAGE_LENGTH})`
      );
      console.error('[useWebSocket]', validationError);
      setError(validationError);
      if (onErrorRef.current) {
        onErrorRef.current(validationError);
      }
      return;
    }

    // ... rest of implementation
  },
  [onError]
);
```

**Impact:** MEDIUM - Could send malformed messages to backend without validation.

**Benefits:**
- Prevents backend errors from malformed input
- Better error messages for users
- Prevents DoS via very large messages
- Security improvement

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 48: useWebSocket useEffect cleanup dependency issue

**Labels:** `bug`, `react`, `medium-priority`, `phase-0-layer-7`

**Title:** Fix useEffect cleanup to avoid stale closure issue

**Description:**
The cleanup function in useEffect captures `disconnect` from initial render. If `disconnect` changes, cleanup won't use the latest version. Could leave connections open.

**File:** `frontend/hooks/useWebSocket.ts:223-231`

**Current Code:**
```typescript
useEffect(() => {
  if (autoConnect) {
    connect();
  }

  return () => {
    disconnect();
  };
}, [autoConnect, connect, disconnect]);
```

**Problem:**
React useEffect runs cleanup BEFORE re-running effect. If `disconnect` reference changes, the cleanup from the PREVIOUS render runs with the OLD `disconnect`.

**Fix:**
```typescript
useEffect(() => {
  if (autoConnect) {
    connect();
  }

  // Use inline cleanup to always reference latest refs
  return () => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmount');
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
  };
}, [autoConnect, connect]); // Remove disconnect from deps
```

**Impact:** MEDIUM - Could leave connections open if disconnect reference changes.

**Benefits:**
- Always uses latest cleanup logic
- Prevents connection leaks
- Follows React hooks best practices

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 49: useWebSocket missing connection timeout protection

**Labels:** `enhancement`, `reliability`, `medium-priority`, `phase-0-layer-7`

**Title:** Add timeout for initial WebSocket connection attempt

**Description:**
If backend is unreachable, `new WebSocket(url)` can hang indefinitely. No timeout protection for initial connection.

**File:** `frontend/hooks/useWebSocket.ts:94-105`

**Recommended Implementation:**
```typescript
const connect = useCallback(() => {
  // ... existing cleanup ...

  try {
    setConnectionStatus('connecting');
    setError(null);

    const wsUrl = getWebSocketUrl();
    const ws = new WebSocket(wsUrl);

    // Add connection timeout
    const CONNECTION_TIMEOUT = 10000; // 10 seconds
    const connectionTimeoutId = setTimeout(() => {
      if (ws.readyState === WebSocket.CONNECTING) {
        const timeoutError = new Error('WebSocket connection timeout');
        console.error('[useWebSocket]', timeoutError);
        setError(timeoutError);
        setConnectionStatus('error');

        ws.close();

        if (onErrorRef.current) {
          onErrorRef.current(timeoutError);
        }
      }
    }, CONNECTION_TIMEOUT);

    ws.onopen = () => {
      clearTimeout(connectionTimeoutId); // Clear timeout on success
      console.log('[useWebSocket] Connected to', wsUrl);
      setConnectionStatus('connected');
      reconnectAttemptRef.current = 0;
    };

    // ... rest of handlers ...
  } catch (err) {
    // ... existing error handling ...
  }
}, [getWebSocketUrl, reconnect, getReconnectDelay]);
```

**Impact:** MEDIUM - Connection attempts can hang indefinitely without timeout.

**Benefits:**
- Prevents indefinite hangs
- Clear error after timeout
- Better user experience
- Allows retry after timeout

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 50: useWebSocket missing origin validation for WebSocket URL

**Labels:** `security`, `medium-priority`, `phase-0-layer-7`

**Title:** Add origin validation for WebSocket URL parameter

**Description:**
If `url` parameter is provided from user input or untrusted source, could connect to malicious WebSocket server (XSS/CSRF risk).

**File:** `frontend/hooks/useWebSocket.ts:58-65`

**Recommended Implementation:**
```typescript
const getWebSocketUrl = useCallback((): string => {
  if (url) {
    // Validate URL origin matches expected backend
    try {
      const wsUrl = new URL(url);
      const apiUrl = new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

      // Ensure same origin (or whitelisted origins)
      if (wsUrl.hostname !== apiUrl.hostname) {
        throw new Error(
          `WebSocket URL origin (${wsUrl.hostname}) doesn't match API URL (${apiUrl.hostname})`
        );
      }

      return url;
    } catch (err) {
      console.error('[useWebSocket] Invalid WebSocket URL:', err);
      throw new Error('Invalid WebSocket URL');
    }
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace(/^http/, 'ws');
  return `${wsUrl}/api/v1/ws`;
}, [url]);
```

**Impact:** MEDIUM - Security risk if URL can be controlled by attacker.

**Benefits:**
- Prevents connections to malicious servers
- Validates origin matches expected backend
- Security hardening

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 51: useWebSocket console.log statements should use conditional logging

**Labels:** `code-quality`, `enhancement`, `low-priority`, `phase-0-layer-7`

**Title:** Add debug flag for conditional console logging in useWebSocket

**Description:**
Multiple console.log statements throughout useWebSocket hook will spam production console. Should use conditional logging based on debug flag or environment.

**Files:** `frontend/hooks/useWebSocket.ts:102, 137, 147, 206`

**Recommended Implementation:**
```typescript
const DEBUG = process.env.NODE_ENV === 'development';

// In onopen handler
if (DEBUG) {
  console.log('[useWebSocket] Connected to', wsUrl);
}

// In reconnection logic
if (DEBUG) {
  console.log(`[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current})`);
}

// In sendMessage
if (DEBUG) {
  console.log('[useWebSocket] Sent message:', wsMessage);
}
```

**Impact:** LOW - Console spam in production, but doesn't affect functionality.

**Benefits:**
- Cleaner production console
- Easier debugging in development
- Standard practice for conditional logging

**Found in:** useWebSocket Hook Code Review (2025-10-20)

---

## Issue 37: Add thread_id validation in createThread action

**Labels:** `enhancement`, `frontend`, `validation`, `phase-0`

**Title:** Add input validation for empty/invalid thread_id in Zustand createThread action

**Description:**
The `createThread` action in `useAgentState` doesn't validate that the `thread_id` parameter is non-empty and valid. This could lead to creating threads with empty keys in the state object, causing lookup failures and UI bugs.

**File:** `frontend/hooks/useAgentState.ts:71-83`

**Current Code:**
```typescript
createThread: (thread_id: string) => {
  set(
    (state) => ({
      threads: {
        ...state.threads,
        [thread_id]: createEmptyThread(thread_id),
      },
      active_thread_id: thread_id,
    }),
    false,
    'createThread'
  );
},
```

**Expected:**
```typescript
createThread: (thread_id: string) => {
  // Validation
  if (!thread_id || typeof thread_id !== 'string' || thread_id.trim() === '') {
    console.error('[useAgentState] Invalid thread_id provided to createThread:', thread_id);
    return;
  }

  set(
    (state) => ({
      threads: {
        ...state.threads,
        [thread_id]: createEmptyThread(thread_id),
      },
      active_thread_id: thread_id,
    }),
    false,
    'createThread'
  );
},
```

**Impact:** MEDIUM - Empty thread IDs could cause state lookup failures, WebSocket routing errors, and UI displaying wrong thread data.

**Benefits:**
- Prevents creating invalid thread entries
- Clearer error messages for debugging
- Defensive programming against API/WebSocket errors

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 38: Refactor Zustand selectors to prevent unnecessary re-renders

**Labels:** `performance`, `frontend`, `refactor`, `phase-0`

**Title:** Move Zustand selectors from store methods to separate hooks for better performance

**Description:**
The current implementation defines selectors as methods on the store object (`getActiveThread`, `getPendingHITL`, `getMessagesByThread`). This anti-pattern causes components using these selectors to re-render on every state change, even when the selected data hasn't changed.

**File:** `frontend/hooks/useAgentState.ts:339-361`

**Current Code:**
```typescript
// Inside the store definition
getActiveThread: () => {
  const state = get();
  if (!state.active_thread_id) return null;
  return state.threads[state.active_thread_id] || null;
},

getPendingHITL: (thread_id: string) => {
  const state = get();
  const thread = state.threads[thread_id];
  return thread?.hitl_request;
},

getMessagesByThread: (thread_id: string) => {
  const state = get();
  const thread = state.threads[thread_id];
  return thread?.messages || [];
},
```

**Expected:**
```typescript
// REMOVE from store definition, create separate hooks:

/**
 * Hook to get the active conversation thread
 */
export const useActiveThread = () =>
  useAgentState((state) => {
    if (!state.active_thread_id) return null;
    return state.threads[state.active_thread_id] || null;
  });

/**
 * Hook to get pending HITL request for a thread
 */
export const usePendingHITL = (thread_id: string) =>
  useAgentState((state) => {
    const thread = state.threads[thread_id];
    return thread?.hitl_request;
  });

/**
 * Hook to get all messages for a thread
 */
export const useThreadMessages = (thread_id: string) =>
  useAgentState((state) => {
    const thread = state.threads[thread_id];
    return thread?.messages || [];
  });
```

**Impact:** MEDIUM - Poor performance with many messages/tool calls. Components re-render on every state change instead of only when selected data changes.

**Benefits:**
- Zustand's selector pattern provides automatic shallow equality checks
- Reduces unnecessary re-renders (better performance)
- Standard Zustand best practice
- Better React DevTools profiling

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 39: Add deleteThread action to prevent memory leaks

**Labels:** `enhancement`, `frontend`, `memory`, `phase-0`

**Title:** Implement deleteThread action for thread cleanup in Zustand store

**Description:**
The `useAgentState` store has a `clearThread` action that resets thread data but keeps the thread entry in memory. There's no way to completely remove old threads, leading to unbounded memory growth in long-running sessions.

**File:** `frontend/hooks/useAgentState.ts:316-332`

**Current Code:**
```typescript
clearThread: (thread_id: string) => {
  set(
    (state) => {
      const thread = state.threads[thread_id];
      if (!thread) return state;

      return {
        threads: {
          ...state.threads,
          [thread_id]: createEmptyThread(thread_id),
        },
      };
    },
    false,
    'clearThread'
  );
},
```

**Expected:**
```typescript
/**
 * Delete a conversation thread completely
 */
deleteThread: (thread_id: string) => {
  set(
    (state) => {
      const { [thread_id]: deleted, ...remaining } = state.threads;

      return {
        threads: remaining,
        // Clear active_thread_id if deleting active thread
        active_thread_id:
          state.active_thread_id === thread_id
            ? null
            : state.active_thread_id,
      };
    },
    false,
    'deleteThread'
  );
},
```

**Impact:** MEDIUM - Long-running sessions accumulate threads in memory with no cleanup mechanism. Memory usage grows unbounded.

**Benefits:**
- Prevents memory leaks in long sessions
- User control over conversation history
- Better memory management for production deployments

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 40: Add XSS sanitization for user message content in Zustand store

**Labels:** `security`, `frontend`, `enhancement`, `phase-0`

**Title:** Sanitize user message content with DOMPurify to prevent XSS attacks

**Description:**
User-provided message content is stored in the Zustand state without sanitization. While the UI components should also sanitize, defense-in-depth security practices recommend sanitizing at the state layer as well.

**File:** `frontend/hooks/useAgentState.ts:88-114`

**Current Code:**
```typescript
addMessage: (thread_id: string, message: Omit<AgentMessage, 'id' | 'timestamp'>) => {
  set(
    (state) => {
      const thread = state.threads[thread_id];
      if (!thread) return state;

      const newMessage: AgentMessage = {
        ...message,
        id: generateId(),
        timestamp: new Date().toISOString(),
      };

      return {
        threads: {
          ...state.threads,
          [thread_id]: {
            ...thread,
            messages: [...thread.messages, newMessage],
            updated_at: new Date().toISOString(),
          },
        },
      };
    },
    false,
    'addMessage'
  );
},
```

**Expected:**
```typescript
import DOMPurify from 'isomorphic-dompurify'; // npm install isomorphic-dompurify

addMessage: (thread_id: string, message: Omit<AgentMessage, 'id' | 'timestamp'>) => {
  set(
    (state) => {
      const thread = state.threads[thread_id];
      if (!thread) return state;

      // Sanitize content to prevent XSS
      const sanitizedContent =
        message.role === 'user'
          ? DOMPurify.sanitize(message.content, { ALLOWED_TAGS: [] }) // Strip all HTML from user input
          : message.content; // Trust assistant/system messages

      const newMessage: AgentMessage = {
        ...message,
        content: sanitizedContent,
        id: generateId(),
        timestamp: new Date().toISOString(),
      };

      return {
        threads: {
          ...state.threads,
          [thread_id]: {
            ...thread,
            messages: [...thread.messages, newMessage],
            updated_at: new Date().toISOString(),
          },
        },
      };
    },
    false,
    'addMessage'
  );
},
```

**Impact:** LOW - Risk depends on how UI components render messages. Defense-in-depth security principle.

**Benefits:**
- Prevents XSS if UI components don't sanitize
- Defense-in-depth security approach
- Industry best practice for user-generated content

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 41: Add error logging for missing entities in Zustand update actions

**Labels:** `enhancement`, `frontend`, `observability`, `phase-0`

**Title:** Add console warnings when update actions target non-existent messages/tool calls

**Description:**
Update actions like `updateMessage` and `updateToolCall` silently return unchanged state when the target entity doesn't exist. This makes debugging difficult when WebSocket events arrive out of order or reference incorrect IDs.

**File:** `frontend/hooks/useAgentState.ts:119-201`

**Current Code:**
```typescript
updateMessage: (
  thread_id: string,
  message_id: string,
  updates: Partial<AgentMessage>
) => {
  set(
    (state) => {
      const thread = state.threads[thread_id];
      if (!thread) return state;

      return {
        threads: {
          ...state.threads,
          [thread_id]: {
            ...thread,
            messages: thread.messages.map((msg) =>
              msg.id === message_id ? { ...msg, ...updates } : msg
            ),
            updated_at: new Date().toISOString(),
          },
        },
      };
    },
    false,
    'updateMessage'
  );
},
```

**Expected:**
```typescript
updateMessage: (
  thread_id: string,
  message_id: string,
  updates: Partial<AgentMessage>
) => {
  set(
    (state) => {
      const thread = state.threads[thread_id];
      if (!thread) {
        console.warn(`[useAgentState] Thread ${thread_id} not found in updateMessage`);
        return state;
      }

      // Validate that message exists
      const messageExists = thread.messages.some((msg) => msg.id === message_id);
      if (!messageExists) {
        console.warn(`[useAgentState] Message ${message_id} not found in thread ${thread_id}`);
        return state;
      }

      return {
        threads: {
          ...state.threads,
          [thread_id]: {
            ...thread,
            messages: thread.messages.map((msg) =>
              msg.id === message_id ? { ...msg, ...updates } : msg
            ),
            updated_at: new Date().toISOString(),
          },
        },
      };
    },
    false,
    'updateMessage'
  );
},
```

**Impact:** LOW - Makes debugging easier but doesn't affect functionality when everything works correctly.

**Benefits:**
- Easier debugging of WebSocket event ordering issues
- Clearer error messages for development
- Helps identify race conditions or ID mismatches

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 42: Add JSDoc examples for complex Zustand actions

**Labels:** `documentation`, `frontend`, `good-first-issue`, `phase-0`

**Title:** Add usage examples to JSDoc comments for complex state update actions

**Description:**
Complex actions like `updateMessage`, `updateToolCall`, and `updateStep` would benefit from JSDoc examples showing common usage patterns, especially for streaming message updates and tool call lifecycle management.

**File:** `frontend/hooks/useAgentState.ts:119-145, 175-201, 282-311`

**Current Code:**
```typescript
/**
 * Update an existing message in a thread
 */
updateMessage: (
  thread_id: string,
  message_id: string,
  updates: Partial<AgentMessage>
) => {
  // ... implementation
},
```

**Expected:**
```typescript
/**
 * Update an existing message in a thread
 *
 * @example
 * ```typescript
 * // Update message content during streaming
 * updateMessage('thread-123', 'msg-456', {
 *   content: existingContent + newChunk
 * });
 *
 * // Mark message as completed
 * updateMessage('thread-123', 'msg-456', {
 *   metadata: { streaming: false, completed: true }
 * });
 * ```
 */
updateMessage: (
  thread_id: string,
  message_id: string,
  updates: Partial<AgentMessage>
) => {
  // ... implementation
},
```

**Impact:** LOW - Documentation improvement, no functional change.

**Benefits:**
- Easier onboarding for new developers
- Clearer usage patterns
- Reduces misuse of partial updates
- Better IDE autocomplete hints

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 43: Make Zustand devtools configurable via environment variable

**Labels:** `enhancement`, `frontend`, `developer-experience`, `phase-0`

**Title:** Add environment variable to control Zustand devtools middleware

**Description:**
Zustand devtools are always enabled in development mode. It would be helpful to allow disabling them via environment variable for performance testing or when debugging other issues.

**File:** `frontend/hooks/useAgentState.ts:363-367`

**Current Code:**
```typescript
{
  name: 'agent-state',
  enabled: process.env.NODE_ENV === 'development',
}
```

**Expected:**
```typescript
{
  name: 'agent-state',
  enabled: process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_ZUSTAND_DEVTOOLS !== 'false',
}
```

**Impact:** LOW - Developer experience improvement, no functional change.

**Benefits:**
- Allows disabling devtools for performance testing in dev mode
- Reduces noise when debugging other issues
- More control over dev experience
- Standard practice for optional debugging tools

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

## Issue 44: Add TypeScript strict null checks in Zustand state updates

**Labels:** `type-safety`, `frontend`, `good-first-issue`, `phase-0`

**Title:** Improve TypeScript null safety in updateStep current_step logic

**Description:**
The `updateStep` action has a ternary that could be more explicit about null checking for TypeScript inference and code clarity.

**File:** `frontend/hooks/useAgentState.ts:299-302`

**Current Code:**
```typescript
current_step:
  thread.current_step?.id === step_id
    ? { ...thread.current_step, ...updates }
    : thread.current_step,
```

**Expected:**
```typescript
current_step:
  thread.current_step && thread.current_step.id === step_id
    ? { ...thread.current_step, ...updates }
    : thread.current_step,
```

**Impact:** LOW - Prevents potential runtime errors if current_step is undefined. More explicit intent.

**Benefits:**
- More explicit null checking
- Better TypeScript inference
- Prevents potential runtime errors
- Clearer code intent

**Found in:** useAgentState Zustand Store Code Review (2025-10-20)

---

---

## Issue 52: Conditional test logic in agent state UI tests reduces reliability

**Labels:** `testing`, `reliability`, `medium-priority`, `phase-0-layer-7`

**Title:** Replace conditional test logic with explicit assertions in agent state UI tests

**Description:**
Multiple Playwright tests use `if element.is_visible()` conditionals that allow tests to pass even when features are missing. Tests should explicitly assert element visibility or use skip markers for optional features.

**Files:** `tests/ui/test_agent_state.py:137-141, 160-167, 189-196`

**Current Code (Example from test_multiple_threads_isolation):**
```python
# Act: Create new thread (navigate to new chat page or click "New Chat")
new_chat_button = page.locator('[data-testid="new-chat-button"]')
if new_chat_button.is_visible():
    new_chat_button.click()
else:
    # Navigate to new instance
    page.goto("http://localhost:3000/chat?new=true")
```

**Recommended Fix:**
```python
# Option 1: Explicit assertion (if feature exists)
new_chat_button = page.locator('[data-testid="new-chat-button"]')
expect(new_chat_button).to_be_visible(timeout=3000)
new_chat_button.click()

# Option 2: Skip test if feature not ready (Phase 0)
@pytest.mark.skip(reason="New chat button not implemented in Phase 0")
def test_multiple_threads_isolation(self, page: Page) -> None:
    ...
```

**Impact:** MEDIUM - Tests may silently pass when features are missing, giving false confidence in test coverage.

**Benefits:**
- Tests fail explicitly when features missing
- Clear signal of incomplete implementation
- More reliable test suite
- Better test failure debugging

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 53: Incomplete test for state persistence across page refresh

**Labels:** `testing`, `incomplete`, `medium-priority`, `phase-0-layer-7`

**Title:** Complete or skip test_persist_state_across_page_refresh in agent state tests

**Description:**
Test `test_persist_state_across_page_refresh` has commented-out assertion and doesn't verify anything. Either implement the assertion if persistence exists, or mark as skipped for Phase 0.

**File:** `tests/ui/test_agent_state.py:198-219`

**Current Code:**
```python
def test_persist_state_across_page_refresh(self, page: Page) -> None:
    """Test agent state persists across page refresh (if implemented)."""
    # ... setup code ...
    
    # Assert: Message still visible (if persistence enabled)
    # Note: This test may fail if persistence not implemented in Phase 0
    # Consider marking as optional or skip if feature not ready
    chat_history = page.locator('[data-testid="chat-history"]')
    
    # For Phase 0, we might NOT persist state, so this test might be skipped
    # expect(chat_history).to_contain_text("Persistent message", timeout=5000)
```

**Recommended Fix:**
```python
# Option 1: If persistence IS implemented
def test_persist_state_across_page_refresh(self, page: Page) -> None:
    """Test agent state persists across page refresh."""
    # ... setup code ...
    expect(chat_history).to_contain_text("Persistent message", timeout=5000)

# Option 2: If persistence NOT in Phase 0
@pytest.mark.skip(reason="State persistence not implemented in Phase 0")
def test_persist_state_across_page_refresh(self, page: Page) -> None:
    """Test agent state persists across page refresh."""
    pass

# Option 3: Remove test entirely if not planned
```

**Impact:** MEDIUM - Test exists but doesn't test anything, reducing actual coverage.

**Benefits:**
- Clear test outcome (pass/fail/skip)
- Accurate coverage reporting
- No confusion about test purpose

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 54: Thread ID extraction in UI tests doesn't wait for rendering

**Labels:** `testing`, `race-condition`, `medium-priority`, `phase-0-layer-7`

**Title:** Add wait assertion before extracting thread ID text in test_switch_between_threads

**Description:**
Test extracts thread ID using `inner_text()` without waiting for element to be visible and populated. May get stale/empty value if UI hasn't rendered from WebSocket connection.

**File:** `tests/ui/test_agent_state.py:181`

**Current Code:**
```python
# Thread 1
page.fill('[data-testid="message-input"]', "Thread 1 content")
page.click('[data-testid="send-button"]')

thread_1_id = page.locator('[data-testid="thread-id"]').inner_text()
```

**Recommended Fix:**
```python
# Thread 1
page.fill('[data-testid="message-input"]', "Thread 1 content")
page.click('[data-testid="send-button"]')

# Wait for thread ID to be visible and populated
thread_id_element = page.locator('[data-testid="thread-id"]')
expect(thread_id_element).to_be_visible(timeout=5000)
expect(thread_id_element).not_to_be_empty()
thread_1_id = thread_id_element.inner_text()
```

**Impact:** MEDIUM - Test may fail intermittently due to race condition.

**Benefits:**
- Eliminates race condition
- More reliable test execution
- Clear assertion of prerequisite state

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 55: Hardcoded URLs in agent state UI tests prevent environment flexibility

**Labels:** `testing`, `configuration`, `medium-priority`, `phase-0-layer-7`

**Title:** Extract hardcoded URLs to environment variables in agent state UI tests

**Description:**
Tests hardcode `http://localhost:3000` throughout, preventing execution against different environments (staging, CI, Docker).

**Files:** `tests/ui/test_agent_state.py` (all test methods)

**Current Code:**
```python
def test_create_new_thread(self, page: Page) -> None:
    page.goto("http://localhost:3000/chat")
```

**Recommended Fix:**
```python
# In tests/ui/conftest.py
import os
import pytest

@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL for frontend from environment."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")

# In tests
def test_create_new_thread(self, page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/chat")
```

**Impact:** MEDIUM - Tests can't run against different environments without code changes.

**Benefits:**
- Tests work in CI/CD pipelines
- Can test against staging/production
- Docker-friendly testing
- Standard testing practice

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 56: Missing test coverage for message and tool call updates in agent state

**Labels:** `testing`, `enhancement`, `low-priority`, `phase-0-layer-7`

**Title:** Add tests for updateMessage and updateToolCall actions in agent state

**Description:**
Zustand store has `updateMessage` and `updateToolCall` actions, but no UI tests verify these updates work correctly. Missing coverage for partial updates to existing messages/tool calls.

**File:** `tests/ui/test_agent_state.py`

**Suggested Test:**
```python
def test_update_existing_message_content(self, page: Page) -> None:
    """Test updating an existing message's content."""
    # Send message
    page.fill('[data-testid="message-input"]', "Original message")
    page.click('[data-testid="send-button"]')
    
    # Wait for message to appear
    message = page.locator('[data-testid="message-user"]').first
    expect(message).to_contain_text("Original message")
    
    # Trigger message edit (if UI supports it)
    edit_button = page.locator('[data-testid="edit-message"]').first
    if edit_button.is_visible():
        edit_button.click()
        page.fill('[data-testid="edit-input"]', "Updated message")
        page.click('[data-testid="save-edit"]')
        
        # Verify update
        expect(message).to_contain_text("Updated message")
        expect(message).not_to_contain_text("Original message")

def test_update_tool_call_status(self, page: Page) -> None:
    """Test tool call status updates from pending -> running -> completed."""
    # Trigger tool call
    page.fill('[data-testid="message-input"]', "Search for Python")
    page.click('[data-testid="send-button"]')
    
    tool_call = page.locator('[data-testid="tool-call"]').first
    
    # Verify status transitions
    expect(tool_call).to_have_attribute("data-status", "pending", timeout=3000)
    expect(tool_call).to_have_attribute("data-status", "running", timeout=5000)
    expect(tool_call).to_have_attribute("data-status", "completed", timeout=10000)
```

**Impact:** LOW - Core functionality works, but edge cases for updates not tested.

**Benefits:**
- Complete test coverage of store actions
- Catches bugs in partial updates
- Verifies state immutability

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 57: Missing test coverage for step/subtask tracking in agent state

**Labels:** `testing`, `enhancement`, `low-priority`, `phase-0-layer-7`

**Title:** Add tests for addStep and updateStep actions in agent state

**Description:**
Zustand store has `addStep` and `updateStep` actions for tracking agent subtasks, but no UI tests verify this functionality. Missing coverage for progress tracking features.

**File:** `tests/ui/test_agent_state.py`

**Suggested Test:**
```python
def test_track_agent_steps_in_state(self, page: Page) -> None:
    """Test agent steps/subtasks are tracked and displayed."""
    page.goto(f"{base_url}/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected")
    
    # Send complex query that triggers multiple steps
    page.fill('[data-testid="message-input"]', "Research and summarize Python best practices")
    page.click('[data-testid="send-button"]')
    
    # Verify steps appear
    steps_list = page.locator('[data-testid="agent-steps"]')
    expect(steps_list).to_be_visible(timeout=5000)
    
    # Verify at least one step exists
    first_step = page.locator('[data-testid="agent-step"]').first
    expect(first_step).to_be_visible()
    expect(first_step).to_have_attribute("data-status", /pending|running|completed/)

def test_update_step_status_progression(self, page: Page) -> None:
    """Test step status updates from pending -> running -> completed."""
    # ... similar to tool call status test ...
```

**Impact:** LOW - Subtask tracking is supplementary feature, not core functionality.

**Benefits:**
- Verifies progress indicator UI works
- Tests complete AG-UI event handling
- Better user experience validation

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 58: Missing test coverage for error scenarios in agent state

**Labels:** `testing`, `enhancement`, `low-priority`, `phase-0-layer-7`

**Title:** Add error handling tests for agent state management

**Description:**
No tests verify agent state handles errors correctly (failed tool calls, agent errors, network failures). Missing coverage for error recovery and error state transitions.

**File:** `tests/ui/test_agent_state.py`

**Suggested Tests:**
```python
def test_agent_error_state_handling(self, page: Page) -> None:
    """Test agent state transitions to error and displays error message."""
    page.goto(f"{base_url}/chat")
    
    # Trigger error (e.g., invalid query, backend timeout)
    page.fill('[data-testid="message-input"]', "TRIGGER_ERROR_MODE")
    page.click('[data-testid="send-button"]')
    
    # Verify error state
    agent_status = page.locator('[data-testid="agent-status"]')
    expect(agent_status).to_have_text(/error|failed/, timeout=10000)
    
    # Verify error message displayed
    error_message = page.locator('[data-testid="error-message"]')
    expect(error_message).to_be_visible()
    expect(error_message).not_to_be_empty()

def test_tool_call_error_state(self, page: Page) -> None:
    """Test tool call transitions to error state on failure."""
    page.fill('[data-testid="message-input"]', "Search for INVALID_QUERY_123")
    page.click('[data-testid="send-button"]')
    
    tool_call = page.locator('[data-testid="tool-call"]').first
    expect(tool_call).to_have_attribute("data-status", "error", timeout=10000)
    
    # Verify error details available
    error_details = tool_call.locator('[data-testid="tool-error"]')
    expect(error_details).to_be_visible()

def test_recover_from_error_state(self, page: Page) -> None:
    """Test agent can recover from error state with new message."""
    # Trigger error
    page.fill('[data-testid="message-input"]', "TRIGGER_ERROR")
    page.click('[data-testid="send-button"]')
    
    agent_status = page.locator('[data-testid="agent-status"]')
    expect(agent_status).to_have_text(/error/, timeout=10000)
    
    # Send new valid message
    page.fill('[data-testid="message-input"]', "Hello")
    page.click('[data-testid="send-button"]')
    
    # Verify recovery
    expect(agent_status).to_have_text(/running|idle/, timeout=10000)
```

**Impact:** LOW - Error handling is important but tests can be added later.

**Benefits:**
- Verifies error states work correctly
- Tests error recovery paths
- Better reliability validation
- Prevents error state bugs

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 59: Missing test coverage for concurrent state modifications in agent state

**Labels:** `testing`, `enhancement`, `low-priority`, `phase-0-layer-7`

**Title:** Add tests for concurrent tool calls and message updates in agent state

**Description:**
No tests verify agent state handles concurrent operations correctly (multiple tool calls running simultaneously, rapid message updates). Missing coverage for race conditions and concurrent state modifications.

**File:** `tests/ui/test_agent_state.py`

**Suggested Test:**
```python
def test_track_multiple_concurrent_tool_calls(self, page: Page) -> None:
    """Test state correctly tracks multiple tool calls running simultaneously."""
    page.goto(f"{base_url}/chat")
    
    # Trigger query that uses multiple tools concurrently
    page.fill('[data-testid="message-input"]', "Search web AND read file AND analyze data")
    page.click('[data-testid="send-button"]')
    
    # Verify multiple tool calls appear
    tool_calls = page.locator('[data-testid="tool-call"]')
    expect(tool_calls).to_have_count(3, timeout=10000)  # Or at least 2+
    
    # Verify each has correct status
    for i in range(3):
        tool_call = tool_calls.nth(i)
        expect(tool_call).to_have_attribute("data-status", /pending|running|completed/)
        expect(tool_call).to_have_attribute("data-tool-name")  # Has name

def test_rapid_message_updates(self, page: Page) -> None:
    """Test state handles rapid streaming message updates."""
    page.fill('[data-testid="message-input"]', "Generate long response")
    page.click('[data-testid="send-button"]')
    
    assistant_message = page.locator('[data-testid="message-assistant"]').first
    expect(assistant_message).to_be_visible(timeout=10000)
    
    # Verify message content updates rapidly (streaming)
    # Wait for partial content, then full content
    expect(assistant_message).to_contain_text(/.+/, timeout=2000)  # Some text
    
    # Wait for completion
    agent_status = page.locator('[data-testid="agent-status"]')
    expect(agent_status).to_have_text(/completed|idle/, timeout=15000)
    
    # Verify final message is complete
    final_text = assistant_message.inner_text()
    assert len(final_text) > 50  # Long response
```

**Impact:** LOW - Concurrent operations are edge cases, core functionality works sequentially.

**Benefits:**
- Catches race conditions
- Verifies state immutability under concurrency
- Better reliability for complex workflows

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 60: Missing accessibility tests for agent state UI components

**Labels:** `testing`, `accessibility`, `low-priority`, `phase-0-layer-7`

**Title:** Add accessibility tests for agent state UI (ARIA labels, keyboard nav)

**Description:**
No tests verify agent state UI components are accessible (ARIA labels, keyboard navigation, screen reader compatibility). Missing WCAG compliance testing.

**File:** `tests/ui/test_agent_state.py`

**Suggested Test:**
```python
def test_agent_state_accessibility(self, page: Page) -> None:
    """Test agent state UI has proper accessibility attributes."""
    page.goto(f"{base_url}/chat")
    
    # Check ARIA labels
    message_input = page.locator('[data-testid="message-input"]')
    expect(message_input).to_have_attribute("aria-label", /message|input/)
    
    send_button = page.locator('[data-testid="send-button"]')
    expect(send_button).to_have_attribute("aria-label", /send|submit/)
    
    agent_status = page.locator('[data-testid="agent-status"]')
    expect(agent_status).to_have_attribute("role", "status")
    expect(agent_status).to_have_attribute("aria-live", "polite")
    
    # Check keyboard navigation
    message_input.focus()
    page.keyboard.press("Tab")
    # Verify focus moved to send button
    expect(send_button).to_be_focused()

def test_screen_reader_announcements(self, page: Page) -> None:
    """Test important state changes have screen reader announcements."""
    page.goto(f"{base_url}/chat")
    
    # Check for aria-live regions
    status_region = page.locator('[aria-live="polite"]')
    expect(status_region).to_be_attached()
    
    # Trigger state change
    page.fill('[data-testid="message-input"]', "Hello")
    page.click('[data-testid="send-button"]')
    
    # Verify status region updates
    expect(status_region).to_contain_text(/running|processing/, timeout=5000)
```

**Impact:** LOW - Accessibility is important but can be added incrementally.

**Benefits:**
- WCAG compliance
- Better user experience for assistive tech users
- Legal compliance (ADA, Section 508)
- Standard best practice

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 61: Inconsistent timeout values in agent state UI tests

**Labels:** `testing`, `code-quality`, `low-priority`, `phase-0-layer-7`

**Title:** Standardize timeout values in agent state UI tests

**Description:**
Tests use inconsistent timeout values (3s, 5s, 10s, 15s) with no clear rationale. Should standardize based on operation type for consistency and clarity.

**File:** `tests/ui/test_agent_state.py` (all test methods)

**Current State:**
- WebSocket connection: 5s (line 35)
- Message display: 3s (lines 43, 90, 120)
- Assistant response: 10s (line 62)
- Agent completion: 15s (line 100)
- Tool calls: 10s (lines 78, 116)

**Recommended Standard:**
```python
# In conftest.py or test constants
TIMEOUT_WS_CONNECTION = 5000  # WebSocket connection
TIMEOUT_UI_UPDATE = 3000      # UI element display
TIMEOUT_AGENT_RESPONSE = 10000  # Agent response generation
TIMEOUT_TOOL_EXECUTION = 10000  # Tool call completion
TIMEOUT_AGENT_COMPLETION = 15000  # Full agent run completion

# In tests
expect(page.locator('[data-testid="ws-status"]')).to_have_text(
    "connected", 
    timeout=TIMEOUT_WS_CONNECTION
)
```

**Impact:** LOW - Tests work, but inconsistent timeouts reduce clarity.

**Benefits:**
- Clear timeout rationale
- Easier to adjust timeouts globally
- Better test readability
- Standard testing practice

**Found in:** Agent State UI Tests Review (2025-10-20)

---

## Issue 62: Missing test for thread deletion from store

**Labels:** `testing`, `enhancement`, `low-priority`, `phase-0-layer-7`

**Title:** Add test for thread deletion (not just clearing) from agent state

**Description:**
Tests verify `clearThread` action (removes messages but keeps thread), but no test verifies complete thread deletion from store (removing thread entirely from `threads` dictionary).

**File:** `tests/ui/test_agent_state.py`

**Suggested Test:**
```python
def test_delete_thread_removes_from_store(self, page: Page) -> None:
    """Test deleting a thread removes it from the store entirely."""
    page.goto(f"{base_url}/chat")
    
    # Create thread and add content
    page.fill('[data-testid="message-input"]', "Test message")
    page.click('[data-testid="send-button"]')
    
    thread_id_element = page.locator('[data-testid="thread-id"]')
    expect(thread_id_element).to_be_visible()
    thread_id = thread_id_element.inner_text()
    
    # Delete thread (if UI supports it)
    delete_button = page.locator('[data-testid="delete-thread-button"]')
    if delete_button.is_visible():
        delete_button.click()
        
        # Confirm deletion
        confirm_button = page.locator('[data-testid="confirm-delete"]')
        if confirm_button.is_visible():
            confirm_button.click()
        
        # Verify thread ID changed (new thread created)
        new_thread_id_element = page.locator('[data-testid="thread-id"]')
        expect(new_thread_id_element).to_be_visible(timeout=3000)
        new_thread_id = new_thread_id_element.inner_text()
        
        assert new_thread_id != thread_id  # Different thread
        
        # Verify old thread content not visible
        chat_history = page.locator('[data-testid="chat-history"]')
        expect(chat_history).not_to_contain_text("Test message")
```

**Impact:** LOW - Thread deletion is administrative feature, not core workflow.

**Benefits:**
- Complete coverage of store actions
- Verifies thread lifecycle management
- Tests thread isolation

**Found in:** Agent State UI Tests Review (2025-10-20)

---
