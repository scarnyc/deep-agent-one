# Deep Agent AGI - Development Guide for Claude Code

## Project Overview

**Goal:** Build a general-purpose deep agent framework that helps users reduce AI tool costs while providing comprehensive everyday task assistance.

**Core Capabilities:** Gmail analysis, code generation in secure sandboxes, GitHub integration, calendar management, web search, shopping, budgeting, retirement planning, research, OCR, content creation, and image generation.

**Development Philosophy:** Phased, measurable, test-driven approach with continuous evaluation, observability, and constant commits. Commit early, commit often - every logical unit of work should be committed with meaningful messages.

---

## 🔴 NON-NEGOTIABLE Development Principles

### 1. Environment Setup (ALWAYS FIRST)

```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip

# Initialize repository
git init deep-agent-agi
cd deep-agent-agi

# Install Poetry for dependency management
curl -sSL https://install.python-poetry.org | python3 -
poetry install

# Initialize git
git add .
git commit -m "Initial commit: Deep Agent AGI"
git checkout -b phase-0-mvp
```

**CRITICAL: Install Node.js/npm and Playwright MCP**
```bash
# Verify Node.js installation (required for Playwright MCP)
node --version  # Must be 18+
npm --version

# If not installed, install Node.js 18+ from https://nodejs.org/

# Install Playwright MCP server (for UI testing)
npm install -g @modelcontextprotocol/server-playwright

# Install Playwright browsers and system dependencies
npx playwright install
npx playwright install-deps

# Verify Playwright installation
npx playwright --version
```

### 2. Environment Separation

**Dependency Management:** Poetry with pyproject.toml
**Node.js Dependencies:** npm with package.json (for Playwright MCP)

**Environment Variables:**
- Use `python-dotenv` for environment-specific `.env` files
- Use `pydantic-settings` for configuration management
- **NEVER commit secrets** - keep `.env.*` files in `.gitignore`
- Maintain `.env.example` as a template
- Use separate API keys for each environment

**Execution:**
```bash
ENV=prod poetry run python -m deep_agent
```

### 3. Security Auditing Setup (TheAuditor)

**Install TheAuditor for AI-assisted security analysis:**

```bash
# Clone and install TheAuditor
git clone github.com/TheAuditorTool/Auditor
cd TheAuditor && pip install -e .

# Return to your project
cd ~/deep-agent-agi

# Initialize and run first audit
aud init && aud full
```

**Why TheAuditor Matters:**
- Works with ANY AI assistant (Claude, Cursor, Copilot)
- AI assistants are blind to security - they optimize for "make it work"
- TheAuditor gives them eyes to see security issues
- Results in `.pf/readthis/` that any LLM can read
- Free, open source (AGPL-3.0)

**Usage:**
- Run `aud full` before every major commit
- Run `aud full` after AI-generated code changes
- Review reports in `.pf/readthis/` directory
- Have Claude/your AI assistant read and fix issues

**Integration with Development:**
- Add `.pf/` to `.gitignore` (reports are generated, not committed)
- Create CI/CD hook to run `aud full` automatically
- Block merges if critical security issues found

### 4. MCP Server Configuration

**Install and configure Model Context Protocol servers:**

#### Playwright MCP (UI Testing - REQUIRED for Phase 0)

```bash
# Install Playwright MCP server globally
npm install -g @modelcontextprotocol/server-playwright

# Install Playwright browsers
npx playwright install
npx playwright install-deps
```

**MCP Configuration Directory:**
Create `.mcp/` directory with configuration files for each MCP server (see README.md for details).

### 5. Evaluation-Driven Development (EDD)

- Implement traces and observability during module development
- Every feature MUST have measurable success criteria
- Use LangSmith for tracing from day one

### 6. Test-Driven Development (TDD)

- Write tests FIRST for every function, tool, and agent
- Minimum 80% test coverage requirement
- Use pytest for unit, integration, and E2E tests
- Mock external API calls during testing
- Use Playwright MCP server for UI testing

### 7. Continuous Integration & Constant Commits

- **Commit constantly:** Every logical unit of work (single function, test, config change) gets committed
- Commit early and often with meaningful messages
- **Never wait to commit:** Small, frequent commits > large, infrequent ones
- Run tests on every commit
- Automated testing pipeline via GitHub Actions
- **Code reviews:** Use CodeRabbit CLI for automated code reviews when available
- Use Playwright MCP server for UI regression testing

---

## 🏗️ Architectural Decisions

All 33 architectural decisions have been documented. Key decisions include:

**Technology Stack:**
- Backend: FastAPI + Python 3.10+
- Frontend: Next.js + AG-UI Protocol
- Database: PostgreSQL + pgvector (Replit)
- LLM: OpenAI GPT-5 with variable reasoning
- Agent Framework: LangGraph DeepAgents

**Development Standards:**
- Testing: pytest with 80%+ coverage requirement
- Code Quality: Ruff (linting/formatting) + mypy (type checking)
- CI/CD: GitHub Actions with parallel jobs
- Security: TheAuditor + pre-commit hooks
- Monitoring: LangSmith for agent tracing

**See:** `README.md` for complete folder structure and detailed architectural decision records.

---

## 📐 Architecture Overview

**Backend:** FastAPI (Python 3.10+)
**Frontend:** Next.js (React) with AG-UI Protocol
**Database:** PostgreSQL with pgvector (Replit)
**LLM:** OpenAI GPT-5 with variable reasoning effort
**Agent Framework:** LangGraph DeepAgents
**Monitoring:** LangSmith
**Search:** Perplexity MCP
**UI Testing:** Playwright MCP

**Key Patterns:**
- Reasoning Router (GPT-5 effort optimization)
- Event Streaming (AG-UI Protocol)
- HITL Workflow (Human-in-the-loop approvals)
- Checkpointer Strategy (State persistence)

**See README.md for complete folder structure and detailed architecture.**

---

## Phase 0: Build & Test MVP

### Objective
Create a functional deep agent framework with core capabilities, basic UI, and monitoring.

### Core Components

#### 1. Deep Agent Framework (LangGraph DeepAgents)
**Repository:** https://github.com/langchain-ai/deepagents

**Default Components:**
- Built-in System Prompt
- Planning Tool (TodoWrite-based)
- File System Tools (ls, read_file, write_file, edit_file)
- Sub-Agents (general-purpose)
- Human-in-the-Loop (HITL) with checkpointer

#### 2. LLM Integration (GPT-5)
**Documentation:**
- API: https://platform.openai.com/docs/guides/latest-model
- Prompting: https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide

**User Flow:** Fast chat Q&A with streaming responses

#### 3. UI Implementation (AG-UI Protocol)
**Documentation:** https://docs.ag-ui.com/sdk/python/core/overview

**Required AG-UI Events:**
- **Lifecycle:** RunStarted, RunFinished, RunError, StepStarted, StepFinished
- **Messages:** TextMessageStart, TextMessageContent, TextMessageEnd
- **Tools:** ToolCallStart, ToolCallArgs, ToolCallEnd, ToolCallResult
- **HITL:** Custom events for approval workflows

**UI Components:**
1. Chat interface with streaming
2. Subtask progress list
3. Tool execution transparency panel
4. HITL approval interface
5. Progress indicators

#### 4. Monitoring & Observability
**LangSmith Integration:**
- Documentation: https://docs.smith.langchain.com/reference/python/reference
- Trace all agent operations from day one

#### 5. Web Search (Perplexity MCP)
**Repository:** https://github.com/perplexityai/modelcontextprotocol

#### 6. Backend Infrastructure
- FastAPI with WebSocket support
- Rate limiting (slowapi)
- Retry logic with exponential backoff
- Structured error handling

#### 7. Prompt Optimization (Opik)
- Auto-prompt optimization
- A/B testing infrastructure

### Success Criteria - Phase 0

**Must Pass All:**

1. **Framework Integration** ✓
   - [ ] DeepAgents installed and running
   - [ ] All 4 file system tools functional
   - [ ] Planning tool creates and tracks plans
   - [ ] Sub-agent delegation works
   - [ ] HITL approval workflow functional

2. **LLM Integration** ✓
   - [ ] GPT-5 API connected
   - [ ] Streaming responses work
   - [ ] Token usage tracking implemented
   - [ ] Rate limiting active

3. **UI Functionality** ✓
   - [ ] Chat interface displays streaming text
   - [ ] Subtask list updates in real-time
   - [ ] Tool calls visible with "inspect source" toggle
   - [ ] HITL approval UI works (accept/respond/edit)
   - [ ] Progress indicators show agent state

4. **Monitoring** ✓
   - [ ] LangSmith traces all agent runs
   - [ ] Tool calls tracked with arguments and results
   - [ ] Error states logged and visible

5. **Web Search** ✓
   - [ ] Perplexity MCP server connected
   - [ ] Search results returned and displayed

6. **Testing & Reporting** ✓
   - [ ] 80%+ test coverage
   - [ ] Unit, integration, E2E, UI tests passing
   - [ ] Test reports generated automatically
   - [ ] CodeRabbit reviews pass (when available)

7. **Infrastructure** ✓
   - [ ] FastAPI backend running
   - [ ] Separate dev/staging/prod environments
   - [ ] Rate limiting active
   - [ ] Error messages user-friendly

8. **Code Quality & Commits** ✓
   - [ ] Constant commits (every logical change)
   - [ ] Meaningful commit messages (semantic format)
   - [ ] No secrets in version control
   - [ ] Type hints throughout

**Quantitative Metrics:**
- Response latency: <2s for simple queries
- Test coverage: ≥80%
- HITL approval time: <30s
- API error rate: <1%

---

## Phase 1: Enhance MVP (Productionization)

**Objective:** Production-grade features - advanced reasoning, memory, authentication, enhanced UI.

**Core Enhancements:**
1. Variable Reasoning Effort (trigger phrases, complexity analysis, cost optimization)
2. Memory System (PostgreSQL pgvector, semantic search, context retrieval)
3. Authentication & IAM (OAuth 2.0, rotating credentials, least-privilege)
4. Provenance Store (source tracking, citations, confidence scores)
5. Enhanced AG-UI (reasoning indicators, state events, provenance display)

**Key Metrics:** Memory retrieval >90%, auth token refresh >99%, deep reasoning >5% queries, provenance 100% sources

---

## Phase 2: Implement Deep Research

**Objective:** Comprehensive research capabilities via LangChain's Open Deep Research framework.

**Core Components:**
1. Deep Research Framework (multi-step planning, source gathering, synthesis, reporting)
2. Custom MCP Servers (fastmcp for research tools, data aggregation, multi-source querying)
3. Infrastructure Hardening (Cloudflare WAF, load balancing, database scaling)
4. Security Testing (TheAuditor penetration testing, prompt injection defenses)

**Key Metrics:** Research <10min, ≥10 sources/task, uptime >99.5%, zero critical vulnerabilities, 100 concurrent users

---

## Technical Stack

### Core Technologies
- **Framework:** LangGraph DeepAgents
- **LLM:** OpenAI GPT-5
- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Next.js (React) + shadcn/ui + Tailwind CSS
- **Database:** PostgreSQL (Replit) with pgvector
- **Monitoring:** LangSmith
- **Search:** Perplexity MCP
- **UI Protocol:** AG-UI (Python SDK)
- **Runtime:** Python 3.10+, Node.js 18+
- **Package Management:** Poetry (Python), npm (Node.js)

### Development Tools
- **Testing:** pytest, Playwright MCP, pytest-html, pytest-cov
- **Security:** TheAuditor
- **Code Quality:** Ruff (linting + formatting), mypy (type checking)
- **Code Review:** CodeRabbit CLI (when available)
- **Version Control:** Git with semantic commits
- **CI/CD:** GitHub Actions

### MCP Servers
- **Playwright MCP:** UI testing automation
- **Perplexity MCP:** Web search integration
- **Custom MCP Servers:** Built with fastmcp (Phase 2)

### Production Infrastructure
- **WAF:** Cloudflare
- **Load Balancing:** Nginx or cloud-native
- **Caching:** Redis (Phase 2)

---

## Technical Debt & Known Issues

**Last Updated:** 2025-10-06

All code quality issues and technical debt items are tracked in `GITHUB_ISSUES.md`.

**Current Issues:** 8 total
- Issues 1-4: Initial code review (cleanup, type safety, logging improvements)
- Issues 5-8: Layer 2 code review (config mismatch, enhancements, tooling)

**Priority Breakdown:**
- HIGH: 1 issue (.env.example verbosity mismatch)
- MEDIUM: 1 issue (ReasoningRouter configuration - Phase 1)
- LOW: 6 issues (cleanup, enhancements, tooling)

**See:** `GITHUB_ISSUES.md` for detailed descriptions, code examples, fixes, and impact assessments.

---

## Testing Strategy

### Unit Tests
- All functions and methods
- Tool implementations
- 80% minimum coverage

### Integration Tests
- Agent workflows
- Tool chains
- Database operations
- API integrations

### E2E Tests
- Complete user journeys
- HITL approval flows
- Research workflows

### UI Tests (Playwright MCP)
- Automated browser testing
- Visual regression testing
- Cross-browser compatibility
- Accessibility testing (WCAG)

### Load Testing
- Concurrent user simulations (k6)
- API rate limiting validation
- Database performance under load

### Security Testing (TheAuditor)
- Prompt injection attacks
- Authorization bypass testing
- Input sanitization validation
- API abuse prevention
- Data exfiltration attempts
- Automated security scans on every major release
- Pen Test

### Test Reporting
**Automated reports generated after every test run:**
- Test pass/fail summary
- Coverage report (HTML + terminal)
- Performance metrics
- Security scan results (TheAuditor)
- Code review status (CodeRabbit)

**CI/CD Integration:**
- Run on every commit
- Block merge if <80% coverage
- Block merge if security FAIL
- Generate and archive reports

---

## Development Workflow

### Phase 0 Workflow
1. Set up environment → **Commit**
2. Install Node.js + Playwright MCP → **Commit**
3. Install Playwright browsers → **Commit**
4. Create .mcp/ config files → **Commit**
5. Implement DeepAgents core → **Commit after each tool**
6. Add GPT-5 integration → **Commit**
7. Build basic AG-UI → **Commit after each event type**
8. Integrate LangSmith → **Commit**
9. Add Perplexity MCP → **Commit**
10. Implement FastAPI backend → **Commit**
11. Add HITL approval → **Commit**
12. Write comprehensive tests → **Commit after each category**
13. Generate test reports → **Commit**
14. CodeRabbit review → **Commit**
15. Deploy to dev → **Commit**

**Throughout Phase 0:** Commit every logical unit of work immediately.

### Commit Message Convention

Use semantic commit messages:
- `feat:` New features
- `fix:` Bug fixes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `docs:` Documentation updates
- `chore:` Dependency updates, configs
- `perf:` Performance improvements
- `security:` Security enhancements

**Example:** `feat(phase-0): implement DeepAgents file system tools with HITL`

### Pre-Commit Review Workflow (MANDATORY)

**IMPORTANT:** Before EVERY commit, run both code-review-expert and testing-expert agents to verify code quality. Do NOT commit code until agents approve.

**Why This Matters:**
- Prevents committing broken or problematic code
- Ensures git history contains ONLY reviewed, high-quality code
- No fixup commits needed (cleaner history)
- Standard code quality gate pattern
- All issues (critical AND non-critical) tracked before merge

**Workflow:**

1. **Write code/tests** following TDD principles
2. **Run testing-expert** (if tests were written):
   ```bash
   # Before committing tests, verify:
   # - AAA pattern followed
   # - Coverage ≥80%
   # - Edge cases covered
   # - Proper mocking
   # Agent will identify issues and suggest improvements
   ```
3. **Run code-review-expert** (for all code):
   ```bash
   # Before committing implementation, verify:
   # - Type hints present
   # - Security best practices
   # - Error handling comprehensive
   # - Integration patterns correct
   # Agent will identify issues and suggest improvements
   ```
4. **Review agent findings and track ALL issues:**
   - **CRITICAL/HIGH issues:** MUST fix before commit (blocking)
   - **MEDIUM issues:** Fix before commit OR document in GITHUB_ISSUES.md if deferring
   - **LOW/non-critical issues:** Log ALL to GITHUB_ISSUES.md for future work
   - **Agent MUST log non-critical issues** to GITHUB_ISSUES.md per line 930

5. **Fix issues or document deferral:**
   - **If APPROVED:** Proceed to step 6 (commit)
   - **If CHANGES REQUESTED:** Fix issues, go back to step 2 (re-review)
   - **If REJECTED:** Major rework needed, go back to step 1

6. **Only after approval: Make commit** following semantic commit convention

**Example Pre-Commit Review Session:**

```bash
# 1. Write tests for new feature (Web Search Tool)
# [Implement tests/integration/test_tools/test_web_search.py]

# 2. Run testing-expert BEFORE committing tests
# [Use Task tool with testing-expert subagent]
# Result: CHANGES REQUESTED - Missing edge case tests for empty query
# Action: Add missing tests, re-run testing-expert
# Result: APPROVED (9/10) - Optional: Add performance test (logged to GITHUB_ISSUES.md)

# 3. Write implementation (Web Search Tool)
# [Implement backend/deep_agent/tools/web_search.py]

# 4. Run code-review-expert BEFORE committing implementation
# [Use Task tool with code-review-expert subagent]
# Result: APPROVED WITH MINOR RECOMMENDATIONS (8.5/10)
# - HIGH: None
# - MEDIUM: None
# - LOW: Could add more detailed docstring examples (logged to GITHUB_ISSUES.md)

# 5. Track all non-critical issues
git add GITHUB_ISSUES.md
# (Document LOW priority items from both reviews)

# 6. NOW commit (only after approval)
git add tests/integration/test_tools/test_web_search.py
git commit -m "test(phase-0): add Web Search Tool tests (12 tests, TDD)"

git add backend/deep_agent/tools/web_search.py
git commit -m "feat(phase-0): implement Web Search Tool using Perplexity MCP client"

# 7. Continue with next task
```

**Key Differences from Post-Commit:**
- ❌ NO fixup commits needed (code already reviewed)
- ✅ Git history contains ONLY approved code
- ✅ Faster progression (no going back after commit)
- ⚠️ Slightly slower initial workflow (10-15 min wait before commit)

**Time Investment:** 10-15 minutes per feature for review + issue tracking
**Return:** Clean git history, zero unreviewed code in main branch, comprehensive issue tracking

---

## Success Validation Checklist

After each phase, validate:
- [ ] All success criteria met
- [ ] Tests pass with 80%+ coverage
- [ ] **Test reports generated** (HTML, coverage, JSON)
- [ ] **Playwright MCP UI tests** pass
- [ ] **TheAuditor security scan** completed (`aud full`)
- [ ] **Security report shows PASS** (no critical vulnerabilities)
- [ ] **CodeRabbit review approved** (if available)
- [ ] No secrets in version control
- [ ] Environment separation working
- [ ] Monitoring/tracing operational
- [ ] Documentation updated
- [ ] Performance metrics within targets
- [ ] **Constant commits maintained** throughout development

---

## Key References

### Framework & Core
- DeepAgents: https://github.com/langchain-ai/deepagents
- Open Deep Research: https://github.com/langchain-ai/open_deep_research
- Product Research Agent Example: https://github.com/scarnyc/product-research-agent

### Anthropic Resources
- Effective Context Engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Writing Tools for Agents: https://www.anthropic.com/engineering/writing-tools-for-agents
- Tool Use Implementation: https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use

### MCP & Servers
- Model Context Protocol: https://modelcontextprotocol.io/
- Official MCP Servers: https://github.com/modelcontextprotocol/servers
- Perplexity MCP: https://github.com/perplexityai/modelcontextprotocol
- Playwright MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/playwright

### UI & Monitoring
- AG-UI Documentation: https://docs.ag-ui.com/sdk/python/core/overview
- LangSmith Python SDK: https://docs.smith.langchain.com/reference/python/reference

### OpenAI
- GPT-5 Latest Model: https://platform.openai.com/docs/guides/latest-model
- GPT-5 Prompting Guide: https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide

### Security Tools
- **TheAuditor:** https://github.com/TheAuditorTool/Auditor

### Testing Tools
- **Playwright MCP:** https://github.com/modelcontextprotocol/servers/tree/main/src/playwright
- **pytest documentation:** https://docs.pytest.org/

---

## Quick Reference: Essential Commands

### Environment Setup
```bash
# Python virtual environment with Poetry
poetry install
poetry shell

# Verify Node.js
node --version  # Must be 18+

# Install Playwright MCP
npm install -g @modelcontextprotocol/server-playwright
npx playwright install
```

### TheAuditor Security Scanning
```bash
# Initialize
aud init

# Run full security audit
aud full

# Review results
cat .pf/readthis/*
```

### Testing & Reporting
```bash
# All tests with coverage
pytest --cov

# Generate HTML report
pytest --html=reports/test_report.html

# UI tests only
pytest tests/ui/ -v
```

### Code Quality
```bash
# Lint and format
ruff check .
ruff format .

# Type checking
mypy backend/deep_agent/

# Run all quality checks
./scripts/quality_check.sh
```

### Git Workflow
```bash
# After implementing a feature
git add <files>
git commit -m "feat(phase-X): <description>"

# After security scan
git commit -m "security(phase-X): address TheAuditor findings"
```

---

## Next Steps for Claude Code

1. **Review this guide thoroughly**
2. **Set up Phase 0 environment** (venv, git, Poetry, Node.js)
3. **Install Playwright MCP** and browsers
4. **Install TheAuditor** for security scanning
5. **Create project structure** (see README.md)
6. **Start with TDD:** Write tests first
7. **Implement incrementally:** One component at a time
8. **Commit constantly:** After every logical unit of work
9. **Run TheAuditor** after AI-generated code (`aud full`)
10. **Validate against success criteria** before moving to next phase

Remember: **Evaluation-driven, test-driven, phase-driven, commit-driven, security-first.**

Build incrementally, commit constantly, test thoroughly, scan for security issues, measure continuously, deploy confidently.

**Before writing any code:** Add todos to this file. Update todos accordingly, checking them off as you complete tasks. Only use one subagent when instructed. Plan subagent delegation for optimal task distribution.

---

## 📋 Phase 0 Implementation TODO List

### **Layer 1: Foundation (Configuration & Core Infrastructure)**

#### Configuration System
- [x] Create `backend/deep_agent/config/__init__.py`
- [x] Write test: `tests/unit/test_config.py` - test settings load from .env
- [x] Implement `backend/deep_agent/config/settings.py` - Pydantic Settings class
- [x] Verify tests pass - settings validation works
- [x] Commit: `feat(phase-0): implement pydantic settings configuration`

#### Structured Logging
- [x] Create `backend/deep_agent/core/__init__.py`
- [x] Write test: `tests/unit/test_logging.py` - test log format and levels
- [x] Implement `backend/deep_agent/core/logging.py` - structlog setup with JSON
- [x] Verify tests pass - logging outputs correctly
- [x] Commit: `feat(phase-0): add structlog for structured logging`

#### Error Handling
- [x] Write test: `tests/unit/test_errors.py` - test custom exceptions
- [x] Implement `backend/deep_agent/core/errors.py` - custom exception classes
- [x] Verify tests pass - exceptions raised properly
- [x] Commit: `feat(phase-0): implement custom error handling`

### **Layer 2: GPT-5 Integration**

**⚠️ Refactoring Note:** This layer was refactored to use LangChain's `ChatOpenAI` instead of raw OpenAI API for DeepAgents compatibility. See commits: `6c1c28f`, `6525029`, `361dcd2`

#### GPT-5 Pydantic Models
- [x] Create `backend/deep_agent/models/__init__.py`
- [x] Write test: `tests/unit/test_models/test_gpt5.py` - test model serialization
- [x] Implement `backend/deep_agent/models/gpt5.py` - GPT5Config, ReasoningEffort, Verbosity
- [x] Verify tests pass - models validate correctly (13 tests)
- [x] Commit: `refactor(phase-0): simplify GPT-5 models for LangChain compatibility`

#### LLM Factory (LangChain ChatOpenAI)
- [x] Create `backend/deep_agent/services/__init__.py`
- [x] Write test: `tests/unit/test_services/test_llm_factory.py` - test ChatOpenAI creation
- [x] Implement `backend/deep_agent/services/llm_factory.py` - create_gpt5_llm() factory
- [x] Verify tests pass - ChatOpenAI instances created correctly (12 tests)
- [x] Commit: `feat(phase-0): implement LLM factory for LangChain ChatOpenAI`

#### Basic Reasoning Router
- [x] Create `backend/deep_agent/agents/__init__.py`
- [x] Write test: `tests/unit/test_agents/test_reasoning_router.py` - test basic routing
- [x] Implement `backend/deep_agent/agents/reasoning_router.py` - return "medium" for all queries
- [x] Verify tests pass - router returns expected effort (11 tests)
- [x] Commit: `feat(phase-0): implement basic reasoning router`
- [x] **Bug Fix:** Issue #5 - Fixed .env.example verbosity mismatch (commit `82ae04a`)

### **Layer 3: LangGraph DeepAgents Setup**

#### Checkpointer Configuration
- [ ] Write test: `tests/unit/test_agents/test_checkpointer.py` - test persistence
- [ ] Implement `backend/deep_agent/agents/checkpointer.py` - SqliteSaver setup
- [ ] Verify tests pass - state persists correctly
- [ ] Commit: `feat(phase-0): configure sqlite checkpointer for agent state`

#### DeepAgents Initialization
- [ ] Write test: `tests/unit/test_agents/test_deep_agent.py` - test agent init, tools loaded
- [ ] Implement `backend/deep_agent/agents/deep_agent.py` - initialize DeepAgents with file tools, HITL
- [ ] Verify tests pass - agent starts, tools available
- [ ] Commit: `feat(phase-0): initialize DeepAgents with file tools and HITL`

#### Agent Service
- [ ] Write test: `tests/integration/test_agent_workflows/test_basic_workflow.py` - full agent run
- [ ] Implement `backend/deep_agent/services/agent_service.py` - orchestration layer
- [ ] Verify tests pass - agent executes workflow end-to-end
- [ ] Commit: `feat(phase-0): add agent service for orchestration`

### **Layer 4: MCP Integration (Web Search)**

#### Perplexity MCP Client
- [ ] Create `backend/deep_agent/integrations/__init__.py`
- [ ] Create `backend/deep_agent/integrations/mcp_clients/__init__.py`
- [ ] Write test: `tests/integration/test_mcp_integration/test_perplexity.py` - mock MCP responses
- [ ] Implement `backend/deep_agent/integrations/mcp_clients/perplexity.py` - MCP client
- [ ] Verify tests pass - MCP calls work
- [ ] Commit: `feat(phase-0): integrate perplexity MCP for web search`

#### Web Search Tool
- [ ] Create `backend/deep_agent/tools/__init__.py`
- [ ] Write test: `tests/unit/test_tools/test_web_search.py` - test tool signature, errors
- [ ] Implement `backend/deep_agent/tools/web_search.py` - agent tool using Perplexity
- [ ] Verify tests pass - tool callable by agent
- [ ] Commit: `feat(phase-0): add web search tool using perplexity MCP`

### **Layer 5: LangSmith Integration (Observability)**

#### LangSmith Tracing
- [ ] Write test: `tests/unit/test_integrations/test_langsmith.py` - verify trace metadata
- [ ] Implement `backend/deep_agent/integrations/langsmith.py` - configure tracing
- [ ] Verify tests pass - traces created
- [ ] Commit: `feat(phase-0): integrate LangSmith for agent tracing`

### **Layer 6: FastAPI Backend (API Layer)**

#### API Models
- [ ] Write test: `tests/unit/test_models/test_chat.py` - validate schemas
- [ ] Implement `backend/deep_agent/models/chat.py` - chat request/response models
- [ ] Implement `backend/deep_agent/models/agents.py` - agent management models
- [ ] Implement `backend/deep_agent/models/common.py` - shared models
- [ ] Verify tests pass - schemas validate
- [ ] Commit: `feat(phase-0): add API pydantic models`

#### FastAPI App Setup
- [ ] Create `backend/deep_agent/api/__init__.py`
- [ ] Create `backend/deep_agent/api/v1/__init__.py`
- [ ] Write test: `tests/integration/test_api_endpoints/test_main.py` - verify app starts
- [ ] Implement `backend/deep_agent/main.py` - FastAPI app with CORS, rate limiting, logging
- [ ] Verify tests pass - app serves requests
- [ ] Commit: `feat(phase-0): initialize FastAPI app with middleware`

#### Chat Endpoints
- [ ] Write test: `tests/integration/test_api_endpoints/test_chat.py` - test REST + SSE
- [ ] Implement `backend/deep_agent/api/v1/chat.py` - POST /chat, POST /chat/stream
- [ ] Verify tests pass - endpoints return responses, streaming works
- [ ] Commit: `feat(phase-0): add chat endpoints with SSE streaming`

#### WebSocket for AG-UI
- [ ] Write test: `tests/integration/test_api_endpoints/test_websocket.py` - test WS connection
- [ ] Implement `backend/deep_agent/api/v1/websocket.py` - WebSocket endpoint for events
- [ ] Verify tests pass - WS connects, events stream
- [ ] Commit: `feat(phase-0): add websocket endpoint for AG-UI event streaming`

#### Agent Management Endpoints
- [ ] Write test: `tests/integration/test_api_endpoints/test_agents.py` - test HITL workflows
- [ ] Implement `backend/deep_agent/api/v1/agents.py` - GET /agents/{run_id}, POST /approve, /respond
- [ ] Verify tests pass - HITL approval works
- [ ] Commit: `feat(phase-0): add agent management endpoints with HITL support`

### **Layer 7: Frontend (AG-UI Protocol)**

#### Next.js Setup
- [ ] Create `frontend/next.config.js` - Next.js configuration
- [ ] Create `frontend/tailwind.config.js` - Tailwind CSS config
- [ ] Create `frontend/postcss.config.js` - PostCSS config
- [ ] Create `frontend/tsconfig.json` - TypeScript config
- [ ] Create `frontend/app/layout.tsx` - root layout
- [ ] Create `frontend/app/page.tsx` - home page
- [ ] Verify: `npm run dev` starts successfully
- [ ] Commit: `feat(phase-0): configure Next.js with Tailwind and TypeScript`

#### AG-UI SDK Setup
- [ ] Create `frontend/lib/ag-ui.ts` - AG-UI SDK configuration
- [ ] Verify: AG-UI types available
- [ ] Commit: `feat(phase-0): integrate AG-UI SDK`

#### WebSocket Hook
- [ ] Write test: `tests/ui/test_websocket_connection.py` - Playwright test WS connection
- [ ] Create `frontend/hooks/useWebSocket.ts` - React hook for backend WS
- [ ] Verify tests pass - connection establishes
- [ ] Commit: `feat(phase-0): add useWebSocket hook for backend connection`

#### Agent State Management
- [ ] Write test: `tests/ui/test_agent_state.py` - verify state updates
- [ ] Create `frontend/hooks/useAgentState.ts` - Zustand store for agent state
- [ ] Create `frontend/types/agent.ts` - TypeScript types
- [ ] Create `frontend/types/ag-ui.ts` - AG-UI event types
- [ ] Verify tests pass - state updates on events
- [ ] Commit: `feat(phase-0): add zustand store for agent state management`

#### Chat Interface
- [ ] Write test: `tests/ui/test_chat_interface.py` - type message, send, verify display
- [ ] Create `frontend/app/chat/page.tsx` - chat page
- [ ] Create `frontend/app/chat/components/ChatInterface.tsx` - main chat component
- [ ] Create `frontend/components/ui/` - shadcn/ui base components (Button, Input, Card, etc.)
- [ ] Verify tests pass - can send messages
- [ ] Commit: `feat(phase-0): implement chat interface`

#### Streaming Message Component
- [ ] Write test: `tests/ui/test_streaming_message.py` - verify token-by-token rendering
- [ ] Create `frontend/app/chat/components/StreamingMessage.tsx` - streaming text display
- [ ] Verify tests pass - text streams in real-time
- [ ] Commit: `feat(phase-0): add streaming message component`

#### Tool Call Display
- [ ] Write test: `tests/ui/test_tool_display.py` - toggle expand/collapse
- [ ] Create `frontend/components/ag-ui/ToolCallDisplay.tsx` - tool transparency panel
- [ ] Verify tests pass - can inspect tool args/results
- [ ] Commit: `feat(phase-0): add tool call transparency display`

#### HITL Approval UI
- [ ] Write test: `tests/ui/test_hitl_approval.py` - click approve, verify backend call
- [ ] Create `frontend/app/chat/components/HITLApproval.tsx` - approval interface
- [ ] Verify tests pass - approval sends to backend
- [ ] Commit: `feat(phase-0): implement HITL approval interface`

#### Progress Indicators
- [ ] Write test: `tests/ui/test_progress_tracker.py` - verify updates on StepStarted
- [ ] Create `frontend/components/ag-ui/ProgressTracker.tsx` - subtask list display
- [ ] Create `frontend/components/ag-ui/AgentStatus.tsx` - agent state indicator
- [ ] Verify tests pass - progress updates in real-time
- [ ] Commit: `feat(phase-0): add progress tracking UI`

### **Layer 8: Testing & Quality**

#### E2E Test Suite
- [ ] Create `tests/e2e/test_complete_workflows/test_basic_chat.py` - user sends query, gets response
- [ ] Create `tests/e2e/test_complete_workflows/test_hitl_workflow.py` - full HITL approval flow
- [ ] Create `tests/e2e/test_complete_workflows/test_tool_usage.py` - agent uses file tools
- [ ] Verify all E2E tests pass
- [ ] Commit: `test(phase-0): add E2E tests for complete workflows`

#### Test Reporting
- [ ] Update `scripts/test.sh` - ensure all report generation works
- [ ] Run full test suite: `./scripts/test.sh`
- [ ] Verify reports generated: HTML, coverage, JSON, Playwright
- [ ] Verify coverage ≥80%
- [ ] Commit: `test(phase-0): configure comprehensive test reporting`

#### Security Scanning
- [ ] Run TheAuditor: `./scripts/security_scan.sh`
- [ ] Review findings in `.pf/readthis/`
- [ ] Fix any critical/high vulnerabilities found
- [ ] Re-run scan to verify fixes
- [ ] Commit: `security(phase-0): run TheAuditor scan and address findings`

### **Final Phase 0 Steps**

#### Documentation
- [ ] Create `docs/development/setup.md` - local setup guide
- [ ] Create `docs/api/endpoints.md` - API endpoint documentation
- [ ] Create `docs/development/testing.md` - testing guide
- [ ] Commit: `docs(phase-0): add setup and API documentation`

#### Success Criteria Validation
- [ ] Review all Phase 0 success criteria in this file
- [ ] Verify all checkboxes can be checked
- [ ] Run full test suite one final time
- [ ] Verify all metrics met (latency <2s, coverage ≥80%, etc.)
- [ ] Commit: `chore(phase-0): validate all success criteria met`

#### Phase 0 Completion
- [ ] Tag release: `git tag v0.1.0-phase0`
- [ ] Push to remote: `git push origin phase-0-mvp --tags`
- [ ] Create summary report of Phase 0 accomplishments
- [ ] Commit: `chore(phase-0): complete Phase 0 MVP`

---
- if CodeRabbit extension is not triggered. Review PRs and identify issues in the comments
- periodically review claude.md by removing stale context. make sure it's < 40k chars to prevent performance impacts
- run the code-review-expert and testing-expert agents before every commit. Make sure we ask both agents to log non-critical issues into the github_issues.md for tracking