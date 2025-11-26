# Scripts

## Purpose

Development, testing, deployment, and utility scripts for Deep Agent AGI.

All scripts in this directory support the Phase 0 MVP development workflow with automated setup, testing, security scanning, and server management.

---

## Available Scripts

### Development Scripts
- `dev.sh` - One-time development environment setup
- `setup_env.py` - Environment validation and .env file creation
- `start-all.sh` - Start both backend and frontend servers
- `start-backend.sh` - Start backend server only
- `start-frontend.sh` - Start frontend server only

### Testing Scripts
- `test.sh` - Run complete test suite with coverage reporting
- `run_all_tests.sh` - Legacy test runner (unit + integration only)
- `test_websocket_streaming.py` - Manual WebSocket streaming test
- `test_multiturn_websocket.py` - Multi-turn conversation regression test

### Security Scripts
- `security_scan.sh` - Run TheAuditor security audit

### Utility Scripts
- `cleanup-logs.sh` - Clean up old log files
- `reorganize_issues.py` - Reorganize GITHUB_ISSUES.md by migration strategy

---

## Quick Start

### First-Time Setup

```bash
# 1. Install Python 3.10+ and Node.js 18+
python --version  # Should be 3.10+
node --version    # Should be 18+

# 2. Run development setup script
./scripts/dev.sh

# 3. Edit .env file with your API keys
vim .env

# 4. Start both servers
./scripts/start-all.sh
```

### Daily Development Workflow

```bash
# Start development servers
./scripts/start-all.sh

# In another terminal: Run tests
./scripts/test.sh

# Run security scan before commit
./scripts/security_scan.sh
```

---

## Script Documentation

### Development Scripts

#### `dev.sh`
**Purpose:** One-time development environment setup

**Usage:**
```bash
./scripts/dev.sh
```

**What It Does:**
- Creates virtual environment (venv/)
- Installs Python dependencies via Poetry
- Installs Node.js dependencies
- Installs Playwright browsers
- Creates .env from .env.example
- Sets up pre-commit hooks

**Requirements:**
- Python 3.10+
- Node.js 18+
- Poetry installed

**Output:**
- Virtual environment: `venv/`
- .env file created
- All dependencies installed

---

#### `setup_env.py`
**Purpose:** Validate environment and create .env file

**Usage:**
```bash
python scripts/setup_env.py
```

**What It Does:**
- Validates Python 3.10+ installed
- Validates Node.js 18+ installed
- Creates necessary directories (data/, reports/, logs/)
- Creates .env from .env.example

**Requirements:**
- Python 3.10+
- Node.js 18+

**Exit Codes:**
- `0` - Setup completed successfully
- `1` - Python/Node.js version too old or .env.example missing

---

#### `start-all.sh`
**Purpose:** Start both backend and frontend servers concurrently

**Usage:**
```bash
./scripts/start-all.sh
```

**Requirements:**
- .env file with API keys (OPENAI_API_KEY, etc.)
- Virtual environment at venv/bin/activate
- Dependencies installed (poetry install, pnpm install)

**Output:**
- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:3000
- Backend logs: `logs/backend/YYYY-MM-DD-HH-MM-SS.log`
- Frontend logs: `logs/frontend/YYYY-MM-DD-HH-MM-SS.log`

**Control:**
- Press `Ctrl+C` to stop both servers

**Examples:**
```bash
# Start both servers
./scripts/start-all.sh

# Watch backend logs
tail -f logs/backend/2025-11-12-*.log

# Watch frontend logs
tail -f logs/frontend/2025-11-12-*.log
```

---

#### `start-backend.sh`
**Purpose:** Start FastAPI backend server only

**Usage:**
```bash
./scripts/start-backend.sh
```

**Requirements:**
- .env file with API keys
- Virtual environment at venv/bin/activate
- Python dependencies installed

**Output:**
- Server: http://127.0.0.1:8000
- Logs: `logs/backend/YYYY-MM-DD-HH-MM-SS.log`

**Examples:**
```bash
# Start backend
./scripts/start-backend.sh

# Watch logs
tail -f logs/backend/2025-11-12-*.log
```

---

#### `start-frontend.sh`
**Purpose:** Start Next.js frontend server only

**Usage:**
```bash
./scripts/start-frontend.sh
```

**Requirements:**
- Node.js 18+ installed
- Node.js dependencies installed (pnpm install in frontend/)
- Backend server running (or NEXT_PUBLIC_BACKEND_URL configured)

**Output:**
- Server: http://localhost:3000
- Logs: `logs/frontend/YYYY-MM-DD-HH-MM-SS.log`

**Examples:**
```bash
# Start frontend
./scripts/start-frontend.sh

# Watch logs
tail -f logs/frontend/2025-11-12-*.log
```

---

### Testing Scripts

#### `test.sh`
**Purpose:** Run complete test suite with coverage reporting

**Usage:**
```bash
./scripts/test.sh
```

**Requirements:**
- Virtual environment activated
- All dependencies installed (poetry install)
- Playwright browsers installed (npx playwright install)

**Output:**
- HTML Report: `reports/test_report.html`
- Coverage Report: `reports/coverage/index.html`
- JSON Report: `reports/report.json`
- Playwright Report: `playwright-report/index.html`
- Terminal: Coverage summary

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

**Examples:**
```bash
# Run all tests
./scripts/test.sh

# View HTML report
open reports/test_report.html

# View coverage report
open reports/coverage/index.html
```

---

#### `run_all_tests.sh`
**Purpose:** Legacy test runner (unit + integration tests only)

**Status:** Being phased out in favor of `test.sh`

**Usage:**
```bash
./scripts/run_all_tests.sh
```

**Requirements:**
- Python 3.11+ (uses hardcoded Python path)
- All dependencies installed

**Output:**
- Coverage Report (HTML): `htmlcov/index.html`
- Coverage Report (JSON): `coverage.json`
- Test Report (HTML): `reports/test_report.html`

**Note:** Use `test.sh` instead for full test suite including UI tests.

---

#### `test_websocket_streaming.py`
**Purpose:** Manual WebSocket streaming test with performance metrics

**Usage:**
```bash
python scripts/test_websocket_streaming.py [optional message]
```

**Requirements:**
- Backend server running on ws://localhost:8000/api/v1/ws
- websockets library installed

**What It Validates:**
- Token streaming works (on_chat_model_stream events)
- Response content received
- Time to first token (TTFT) < 5s
- Total duration < 30s

**Output:**
- Real-time streaming tokens (color-coded)
- Performance metrics (TTFT, tokens/second, duration)
- Event statistics breakdown
- Validation checks summary

**Exit Codes:**
- `0` - All validation checks passed
- `1` - Connection error or test interrupted

**Examples:**
```bash
# Default message
python scripts/test_websocket_streaming.py

# Custom message
python scripts/test_websocket_streaming.py "Tell me a joke"
```

---

#### `test_multiturn_websocket.py`
**Purpose:** Multi-turn conversation regression test (Issue #37)

**Usage:**
```bash
python scripts/test_multiturn_websocket.py
```

**Requirements:**
- Backend server running on ws://localhost:8000/api/v1/ws
- websockets library installed
- Web search tool enabled with Perplexity MCP

**What It Tests:**
1. Multi-turn conversation (same thread_id)
2. Tool execution (web_search)
3. No CancelledError during tool execution
4. Correct AG-UI event format

**Output:**
- Turn-by-turn conversation progress
- Tool execution details
- Validation results summary
- Pass/fail status

**Exit Codes:**
- `0` - Test passed (no CancelledError)
- `1` - Test failed (timeout, error, or exception)

**Examples:**
```bash
# Run test
python scripts/test_multiturn_websocket.py

# Check backend logs after test
tail -f logs/backend/*.log
```

---

### Security Scripts

#### `security_scan.sh`
**Purpose:** Run TheAuditor security audit

**Usage:**
```bash
./scripts/security_scan.sh
```

**Requirements:**
- TheAuditor installed in `.auditor_venv/`
- Install: `.auditor_venv/bin/pip install -e /path/to/Auditor`

**What It Does:**
1. Checks if TheAuditor is installed
2. Initializes `.pf/` directory (if first run)
3. Runs full security audit
4. Checks for CRITICAL vulnerabilities
5. Exits with error if critical issues found

**Output:**
- Security reports: `.pf/readthis/` directory
- Terminal: Summary of findings

**Exit Codes:**
- `0` - No critical vulnerabilities detected
- `1` - Critical vulnerabilities found OR TheAuditor not installed

**Examples:**
```bash
# Run security scan
./scripts/security_scan.sh

# View detailed findings
cat .pf/readthis/*
```

**Integration:**
- Run before EVERY commit (code-review-expert workflow)
- Blocks commit if CRITICAL issues found
- Part of pre-commit hook (future)

---

### Utility Scripts

#### `cleanup-logs.sh`
**Purpose:** Clean up old log files while preserving recent ones

**Usage:**
```bash
./scripts/cleanup-logs.sh
```

**Configuration:**
- `DAYS_TO_KEEP=7` - Delete logs older than 7 days
- `MIN_FILES_TO_KEEP=10` - Always keep at least 10 most recent logs

**Behavior:**
- Interactive: Asks for confirmation before deleting
- Shows files to be deleted with size and modification date
- Calculates total space to be freed
- Preserves minimum number of recent files regardless of age

**Safety:**
- Never deletes ALL logs (keeps MIN_FILES_TO_KEEP)
- Shows detailed preview before deletion
- Requires explicit confirmation

**Output:**
- Lists files to be deleted
- Shows total space to be freed
- Summary of remaining logs

**Examples:**
```bash
# Interactive cleanup
./scripts/cleanup-logs.sh
```

**Advanced:**
Edit script to change `DAYS_TO_KEEP` or `MIN_FILES_TO_KEEP` constants.

---

#### `reorganize_issues.py`
**Purpose:** Reorganize GITHUB_ISSUES.md by migration strategy

**Usage:**
```bash
python scripts/reorganize_issues.py
```

**Requirements:**
- GITHUB_ISSUES.md file exists in project root

**What It Does:**
1. Reads original GITHUB_ISSUES.md
2. Categorizes all issues by migration strategy:
   - **DEFERRED:** Backend issues (fix during microservices split)
   - **OBSOLETE:** Frontend issues (removed - replaced by UI redesign)
   - **TRACKED:** Low-priority issues (fix when time permits)
3. Adds migration strategy notes to each issue
4. Removes OBSOLETE issues from file
5. Generates new file with organized sections

**Output:**
- Updated GITHUB_ISSUES.md with:
  - Migration strategy header
  - DEFERRED issues (7 backend issues)
  - TRACKED issues (10 low-priority issues)
  - OBSOLETE issues removed (47 frontend issues)
- Summary statistics in terminal

**Benefits:**
- Saves ~35-42 hours (87% reduction) by avoiding throwaway work
- Clear roadmap for when to fix each issue
- Removes obsolete work from active tracking

**Examples:**
```bash
# Reorganize issues
python scripts/reorganize_issues.py

# View obsolete issues in git history
git log -p GITHUB_ISSUES.md
```

**Exit Codes:**
- `0` - Successfully reorganized
- `1` - File not found or error during processing

---

## Adding New Scripts

### Shell Script Template

```bash
#!/bin/bash
# Script name and description
#
# Description:
#   Detailed description of what this script does
#
# Usage:
#   ./scripts/script_name.sh [options]
#
# Options:
#   -h, --help    Show help
#   -v, --verbose Verbose output
#
# Requirements:
#   - List dependencies
#   - Environment variables
#
# Output:
#   - What the script produces
#
# Exit Codes:
#   0 - Success
#   1 - Error
#
# Examples:
#   ./scripts/script_name.sh --option

set -e

# Script implementation
```

### Python Script Template

```python
#!/usr/bin/env python3
"""Script description.

Detailed description of what this script does and why it exists.

Usage:
    python scripts/script_name.py [args]

Requirements:
    - Python 3.10+
    - Required libraries

What It Does:
    1. Step one
    2. Step two
    3. Step three

Output:
    - What the script produces

Exit Codes:
    0 - Success
    1 - Error

Examples:
    # Example usage
    python scripts/script_name.py --flag value
"""

import sys

def main():
    """Main entry point."""
    pass

if __name__ == "__main__":
    main()
```

---

## Dependencies

### Shell Scripts
- **bash** - All shell scripts use bash
- **set -e** - Exit on error (all scripts)

### Python Scripts
- **Python 3.10+** - Minimum version requirement
- **websockets** - For WebSocket test scripts
- **pathlib** - For path operations

### System Requirements
- **Node.js 18+** - For frontend development
- **Poetry** - For Python dependency management
- **npm** - For Node.js dependency management
- **TheAuditor** - For security scanning (optional in .auditor_venv/)

---

## Related Documentation

- [Development Guide](../docs/development/) - Development workflow
- [Testing](../tests/README.md) - Testing strategy and conventions
- [CLAUDE.md](../CLAUDE.md) - Project development guide
- [README.md](../README.md) - Project overview and architecture

---

## Security Notes

### Best Practices
- Scripts should NOT contain hardcoded secrets
- Use environment variables for sensitive data (.env file)
- Validate all inputs before processing
- Use `set -e` in shell scripts to exit on error
- Add confirmation prompts for destructive operations

### API Keys
- Never commit API keys to version control
- Store keys in .env file (gitignored)
- Use .env.example as template
- Validate keys are present before running

### TheAuditor Integration
- Run `./scripts/security_scan.sh` before every commit
- Review findings in `.pf/readthis/` directory
- Block commits if CRITICAL vulnerabilities found
- Part of code-review-expert pre-commit workflow

---

## Troubleshooting

### Common Issues

#### Script Permission Denied
```bash
# Fix: Make script executable
chmod +x scripts/script_name.sh
```

#### Virtual Environment Not Found
```bash
# Fix: Run dev setup first
./scripts/dev.sh
```

#### TheAuditor Not Installed
```bash
# Fix: Install TheAuditor
python -m venv .auditor_venv
.auditor_venv/bin/pip install -e /path/to/Auditor
```

#### Playwright Browsers Missing
```bash
# Fix: Install Playwright browsers
npx playwright install
npx playwright install-deps
```

#### Port Already in Use
```bash
# Fix: Kill process using port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

---

## Maintenance

### Log Cleanup
- Run `./scripts/cleanup-logs.sh` periodically
- Default: Keeps logs from last 7 days + 10 most recent
- Adjust DAYS_TO_KEEP and MIN_FILES_TO_KEEP as needed

### Security Scans
- Run before every commit
- Review findings regularly
- Update TheAuditor periodically

### Dependency Updates
- Update Poetry dependencies: `poetry update`
- Update Node.js dependencies: `npm update`
- Update Playwright: `npx playwright install`

---

## Contributing

### Adding a New Script

1. **Create script file** in `scripts/` directory
2. **Add header documentation** (see templates above)
3. **Make executable** (if shell script): `chmod +x scripts/script_name.sh`
4. **Test thoroughly** in clean environment
5. **Update this README** with script documentation
6. **Commit with semantic message:** `chore(scripts): add script_name.sh for X`

### Script Naming Conventions
- Use kebab-case for shell scripts: `start-all.sh`, `cleanup-logs.sh`
- Use snake_case for Python scripts: `setup_env.py`, `test_websocket_streaming.py`
- Use descriptive names that indicate purpose

### Documentation Requirements
- All scripts MUST have header documentation
- Include usage, requirements, output, examples
- Document exit codes
- Add security notes if handling sensitive data

---

**Last Updated:** 2025-11-12
