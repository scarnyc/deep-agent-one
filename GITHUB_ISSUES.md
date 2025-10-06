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
