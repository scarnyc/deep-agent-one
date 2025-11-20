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

### 2. Configuration Management

**Single Source of Truth:** Root `.env` file

#### File Structure

```
deep-agent-agi/
├── .env                      # Active configuration (gitignored, NOT committed)
├── .env.example              # Template with comprehensive documentation (committed)
├── docs/
│   └── templates/
│       ├── env.local.template   # Local development defaults (committed)
│       ├── env.test.template    # Test environment defaults (committed)
│       └── env.prod.template    # Production template (committed)
├── frontend/
│   ├── .env.test             # Frontend test fixtures (committed)
│   └── .env.local.example    # Documentation only (frontend reads from root .env)
└── backend/deep_agent/config/
    └── settings.py           # Pydantic Settings loader
```

#### How It Works

**Backend (Python/FastAPI):**
- **Reads:** Root `.env` file
- **Loader:** `backend/deep_agent/config/settings.py` (Pydantic BaseSettings)
- **Cache:** `@lru_cache` singleton pattern (loaded once on startup)
- **Consumers:** 11 backend modules import `get_settings()`

**Frontend (Next.js/React):**
- **Reads:** Root `.env` file (Next.js default behavior)
- **Exposed:** Only `NEXT_PUBLIC_*` variables (embedded in browser bundle at build time)
- **Consumers:** 18 TypeScript files access `process.env.NEXT_PUBLIC_*`

**Key Points:**
- **ONE active config file** - Root `.env` serves both backend and frontend
- **NO separate frontend/.env.local** - Consolidated to root for simplicity
- **Frontend reads from root** - Next.js automatically finds root `.env`
- **NEXT_PUBLIC_* variables** - Only these are exposed to the browser

#### Setup for New Developers

```bash
# 1. Copy template to active config
cp .env.example .env

# 2. Fill in your API keys
nano .env  # Edit: OPENAI_API_KEY, PERPLEXITY_API_KEY, LANGSMITH_API_KEY

# 3. Validate configuration
python scripts/validate_config.py

# 4. Start services (validation runs automatically)
./scripts/start-all.sh
```

#### Environment-Specific Configuration

Configure environment-specific settings directly in `.env`:

```bash
# Local Development
# Edit .env and set:
ENV=local
DEBUG=true
API_RELOAD=true
STREAM_TIMEOUT_SECONDS=300  # 5 min for debugging
GPT_MODEL_NAME=gpt-5.1-thinking

# Testing (CI/CD)
# Edit .env and set:
ENV=test
MOCK_EXTERNAL_APIS=true
STREAM_TIMEOUT_SECONDS=60  # 1 min for speed
GPT_MODEL_NAME=gpt-5.1-thinking

# Production
# Edit .env and set:
ENV=prod
DEBUG=false  # NEVER true in production
# Fill in ALL secrets (no placeholders)
GPT_MODEL_NAME=gpt-5.1-thinking
# Run: python scripts/validate_config.py
```

**Single Source of Truth:** All configuration is managed through the root `.env` file. No separate template files are used.

#### Configuration Validation

**Automatic validation on startup:**
```bash
./scripts/start-backend.sh  # Runs validation before starting server
```

**Manual validation:**
```bash
python scripts/validate_config.py
```

**Validation checks:**
- ✓ ENV consistency (prod must not have DEBUG=true)
- ✓ Timeout relationships (tool < stream timeout)
- ✓ Required API keys (unless MOCK_EXTERNAL_APIS=true)
- ✓ Security settings (strong secrets in production)
- ✓ Dangerous defaults (no debug tools in production)
- ✓ Type and range validation

#### Best Practices

- **Use pydantic-settings** for type-safe configuration
- **NEVER commit `.env`** - keep it gitignored
- **Maintain `.env.example`** - comprehensive documentation for all settings
- **Use separate API keys per environment**
- **Run validation** before deploying (`python scripts/validate_config.py`)
- **Review templates** when adding new settings

#### Dependency Management

**Python:** Poetry with pyproject.toml
**Node.js:** npm with package.json (for Playwright MCP)

**Execution:**
```bash
# Backend with specific environment
ENV=prod poetry run python -m deep_agent

# Or set in .env file (recommended)
echo "ENV=prod" >> .env
./scripts/start-backend.sh
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

#### context7 MCP (Documentation Retrieval - Built-in)

context7 is a built-in MCP server in Claude Code that provides up-to-date library documentation and code examples.

**Features:**
- Resolve library names to Context7-compatible IDs
- Fetch documentation with code snippets and API references
- Support for versioned documentation
- Trust scores and snippet coverage metrics

**Usage:**
```python
# Automatically used when you need library documentation
# Example: "Show me how to create a FastAPI route with async"
# Tools: mcp__context7__resolve-library-id, mcp__context7__get-library-docs
```

**No installation required** - context7 is pre-configured in Claude Code and ready to use immediately.

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
- **MANDATORY: Run testing-expert and code-review-expert agents before EVERY commit**
- Run tests on every commit
- Automated testing pipeline via GitHub Actions
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
   - [ ] testing-expert and code-review-expert agents run before every commit

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
6. **Custom TypeScript Components** - Explore UI redesign with custom AG-UI components on top of SDK:
   - Custom chat components using `@ag-ui/react` hooks for full UI control
   - Advanced HITL workflows (multi-step approval, conditional branching)
   - Custom event visualizers (tool call timeline, reasoning display)
   - Company-specific branding, animations, and UX enhancements
   - Use `@ag-ui/core` types and `@ag-ui/react` hooks as building blocks
   - Replace CopilotKit components incrementally as needed
   - Create ErrorDisplay.tsx component & update WebSocketProvider.tsx to use ErrorDisplay.
7. Prompt Optimization (Opik) - Auto-prompt optimization, A/B testing infrastructure, prompt versioning
8. **WebSocket Reliability Improvements** - Deferred from Phase 0:
   - Proactive client disconnect monitoring (parallel task using `websocket.wait_closed()`)
   - Progress events for long-running tools (emit status every 5-10 seconds)
   - Reconnection logic for network hiccups (automatic retry with backoff)
   - Tool execution progress tracking (show "Tool X of Y executing..." in UI)
   - Note: Phase 0 implemented graceful cancellation (✅ complete) and reactive disconnect detection (✅ sufficient for MVP)

**Key Metrics:** Memory retrieval >90%, auth token refresh >99%, deep reasoning >5% queries, provenance 100% sources, prompt A/B improvement >10%

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
- **Code Review:** testing-expert and code-review-expert agents (run before every commit)
- **Version Control:** Git with semantic commits
- **CI/CD:** GitHub Actions
- **Debugging:** debugging-expert when prompt identifies there's an issue, crash, bug or defect that needs triaging

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

All code quality issues and technical debt items are tracked in `GITHUB_ISSUES.md` with detailed descriptions, code examples, fixes, and impact assessments.

**Find resolved issues:** `git log --grep="Issue [0-9]"` or search commit messages for specific issue numbers.

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
14. Deploy to dev → **Commit**

**Throughout Phase 0:**
- Commit every logical unit of work immediately
- Use the debugging-expert when a bug or issue is identified
- **MANDATORY: Run testing-expert and code-review-expert agents before EVERY commit**

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
- **Automated security scanning catches vulnerabilities before commit**

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
   # The agent will AUTOMATICALLY:
   # 1. Run TheAuditor security scan (./scripts/security_scan.sh)
   # 2. Read reports from .pf/readthis/ directory
   # 3. Include security findings in review report
   # 4. Perform manual security analysis
   # 5. Verify type hints, error handling, logging
   # 6. Check architecture adherence
   # 7. Validate testing coverage

   # You will receive a comprehensive report with:
   # - TheAuditor scan results (CRITICAL/HIGH/MEDIUM issues)
   # - Manual security review findings
   # - Code quality issues
   # - Testing gaps
   # - Commit quality feedback
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
# [Agent automatically runs: ./scripts/security_scan.sh]
# [Agent reads reports from .pf/readthis/]
# Result: APPROVED WITH MINOR RECOMMENDATIONS (8.5/10)
# TheAuditor Scan: PASS (0 critical issues)
# - ✓ No hardcoded secrets
# - ✓ No SQL injection vulnerabilities
# - ✓ Dependencies up to date
# Manual Security Review:
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
- ✅ Automated security scanning on every commit
- ✅ No security vulnerabilities slip through
- ⚠️ Slightly slower initial workflow (10-15 min wait before commit)

**Time Investment:** 10-15 minutes per feature for review + issue tracking + security scanning
**Return:**
- Clean git history with zero unreviewed code
- Comprehensive issue tracking (functional + security)
- No vulnerabilities in committed code
- Automated + manual security analysis

---

## Prompt Optimization Workflow (context-engineering-expert)

**IMPORTANT:** When you identify opportunities to optimize prompts (agent instructions, system prompts, user-facing messages), use the **context-engineering-expert** agent.

### Triggering Conditions

Use this agent when:
- User explicitly requests prompt optimization or improvement
- User mentions issues with agent behavior, inconsistent responses, or poor output quality
- User wants to implement A/B testing for different prompt versions
- User needs to reduce token usage while maintaining quality
- Creating new agents and wants optimal system prompts from the start
- User mentions Opik, prompt engineering, or context optimization
- After receiving feedback that an agent's responses are unclear or off-target

### Proactive Usage Examples

<example>
Context: User has just created a new agent and completed its initial implementation.
user: "I've finished implementing the code-reviewer agent. Here's the system prompt I wrote: [prompt content]"
assistant: "Let me use the context-engineering-expert agent to optimize this system prompt before you deploy it."
<commentary>
Since the user has created a new agent, proactively use the context-engineering-expert to optimize the prompt following GPT-5 best practices and Opik recommendations, even though the user didn't explicitly request optimization.
</commentary>
</example>

<example>
Context: User reports inconsistent agent behavior.
user: "The research-assistant agent sometimes gives great summaries but other times it's too verbose or misses key points."
assistant: "I'm going to use the context-engineering-expert agent to analyze and optimize the research-assistant's system prompt. This should help ensure more consistent, high-quality outputs."
<commentary>
Inconsistent behavior is a clear signal for prompt optimization. Use the context-engineering-expert to diagnose issues and improve the prompt structure.
</commentary>
</example>

<example>
Context: User is experiencing high token costs.
user: "Our API costs are higher than expected. The agents seem to be using a lot of tokens."
assistant: "Let me use the context-engineering-expert agent to analyze your agents' prompts and optimize them for token efficiency while maintaining output quality."
<commentary>
High token usage often indicates verbose or inefficient prompts. Proactively use the context-engineering-expert to optimize for cost without sacrificing quality.
</commentary>
</example>

### Workflow

1. **Identify optimization opportunity:**
   ```bash
   # Examples:
   # - Agent responses too verbose
   # - Missing citations in web search results
   # - Unclear instructions causing confusion
   # - High token costs
   # - New agent prompt needs review
   ```

2. **Invoke context-engineering-expert:**
   ```bash
   # The agent will:
   # 1. Analyze current prompt against GPT-5 best practices
   # 2. Create evaluation dataset
   # 3. Run Opik optimizer (MetaPrompt, Evolutionary, etc.)
   # 4. Validate improvements with A/B testing
   # 5. Present quantitative results (accuracy, latency, cost)
   ```

3. **Review and apply recommendations:**
   - Review before/after prompt comparison
   - Verify performance metrics show improvement
   - Check statistical significance (p-values)
   - Apply optimized prompt to codebase

### Tools Available

- **analyze_prompt** - GPT-5 best practices analysis
- **optimize_prompt** - Opik-powered optimization
- **evaluate_prompt** - Metrics (accuracy, latency, cost)
- **create_evaluation_dataset** - Generate test cases
- **ab_test_prompts** - Statistical A/B testing

### Example Use Cases

- Optimize `prompts.py` system prompt for better accuracy/verbosity balance
- Improve web search result formatting with citation requirements
- Reduce token usage while maintaining response quality
- Create task-specific prompt variations (code gen vs. chat vs. research)
- Add parallel tool call limits to prevent timeouts

---

## Success Validation Checklist

After each phase, validate:
- [ ] All success criteria met
- [ ] Tests pass with 80%+ coverage
- [ ] **Test reports generated** (HTML, coverage, JSON)
- [ ] **Playwright MCP UI tests** pass
- [ ] **TheAuditor security scan** completed (`aud full`)
- [ ] **Security report shows PASS** (no critical vulnerabilities)
- [ ] **testing-expert and code-review-expert agents run before every commit**
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

### Prompt Optimization
```bash
# Analyze prompt against GPT-5 best practices
# (via context-engineering-expert agent)
analyze_prompt(prompt, task_type="general")

# Optimize prompt with Opik
optimize_prompt(prompt, dataset, optimizer_type="meta")

# Evaluate prompt performance
evaluate_prompt(prompt, dataset, metrics=["accuracy", "latency", "cost"])

# A/B test two prompts
ab_test_prompts(prompt_a, prompt_b, dataset)

# Create evaluation dataset
create_evaluation_dataset(task_description, num_examples=20)
```

### Startup Scripts

**ALWAYS: Use `start-all.sh` for development**

```bash
# Start both backend and frontend with automatic logging
./scripts/start-all.sh

# Servers will start on:
# - Backend:  http://127.0.0.1:8000
# - Frontend: http://localhost:3000
#
# Ctrl+C stops both servers cleanly
```

**Features:**
- **Synchronized startup** - Backend starts first, frontend waits 3 seconds
- **Automatic logging** - Console output + timestamped log files
- **Clean shutdown** - Ctrl+C stops both servers gracefully
- **Environment loading** - Automatically sources `.env` file
- **Virtual environment** - Activates venv for Python dependencies

**Logging Configuration:**

All scripts use `2>&1 | tee` to simultaneously:
- Display output to console (interactive development)
- Save output to timestamped log files (debugging, auditing)

Log files are organized by component:
```
logs/
├── backend/
│   ├── 2025-11-16-10-30-45.log
│   └── 2025-11-16-14-22-18.log
└── frontend/
    ├── 2025-11-16-10-30-48.log
    └── 2025-11-16-14-22-21.log
```

**Viewing Logs:**

```bash
# Watch live logs
tail -f logs/backend/2025-11-16-*.log
tail -f logs/frontend/2025-11-16-*.log

# Search logs for errors
grep -i error logs/backend/*.log
grep -i "websocket" logs/backend/*.log

# View most recent backend log
tail -100 $(ls -t logs/backend/*.log | head -1)

# Follow both logs simultaneously
tail -f logs/backend/2025-11-16-*.log logs/frontend/2025-11-16-*.log
```

**Individual Scripts:**

Use these when you need to start services separately:

```bash
# Backend only (when testing API directly)
./scripts/start-backend.sh

# Frontend only (when backend already running)
./scripts/start-frontend.sh
```

**Common Scenarios:**

```bash
# Full development with logging
./scripts/start-all.sh

# Debug backend issues (backend only + follow logs)
./scripts/start-backend.sh &
tail -f logs/backend/$(ls -t logs/backend/*.log | head -1)

# Test frontend changes (backend running separately)
# Terminal 1:
./scripts/start-backend.sh

# Terminal 2:
./scripts/start-frontend.sh

# Review historical logs after crash
ls -lt logs/backend/*.log | head -5  # Find recent logs
cat logs/backend/2025-11-16-10-30-45.log | grep -i error
```

**Why `2>&1 | tee`?**

This pattern redirects stderr to stdout (`2>&1`) then duplicates output to both console and file (`tee`):
- **Console output** - See real-time feedback during development
- **Log file** - Permanent record for debugging, auditing, security analysis
- **No lost output** - Both streams (stdout/stderr) captured

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

### ✅ **Layers 1-7: COMPLETED**

**Layer 1: Foundation** - Configuration, logging, error handling ✓
**Layer 2: GPT-5 Integration** - Models, LLM factory, reasoning router ✓
**Layer 3: LangGraph DeepAgents** - Checkpointer, agent initialization, service layer ✓
**Layer 4: MCP Integration** - Perplexity client, web search tool ✓
**Layer 5: LangSmith** - Tracing and observability ✓
**Layer 6: FastAPI Backend** - API models, chat/WS/agents endpoints ✓
**Layer 7: Frontend** - Next.js, AG-UI Protocol, custom components (migrated from CopilotKit) ✓

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

## 📝 Important Reminders

- **Periodic maintenance:** Review CLAUDE.md regularly to remove stale context (keep < 40k chars)
- **Pre-commit workflow:** Run code-review-expert and testing-expert agents before EVERY commit
- **Issue tracking:** Both agents must log non-critical issues to GITHUB_ISSUES.md for future work
- **Code Doc Context:** Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.
- **Debugging workflow:** Run debugging-expert agent when a bug or issue is identified
- **Fix validation:** After making code changes, ALWAYS validate the fix comprehensively before asking the user to manually test in browser. Validation steps:
  1. Analyze the fix to understand what it does and why it solves the issue
  2. Run TypeScript compilation (`npx tsc --noEmit`) to verify no new type errors
  3. Run relevant tests (`pytest` for backend, `npm test` for frontend) to verify no regressions
  4. Explain the fix to the user with evidence (test results, compilation success)
  5. Only THEN ask the user to manually test if automated validation passes