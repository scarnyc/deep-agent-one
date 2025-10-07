# Deep Agent AGI

> **General-purpose deep agent framework that reduces AI tool costs through intelligent reasoning optimization**

[![Phase](https://img.shields.io/badge/Phase-0--MVP-blue)]()
[![Python](https://img.shields.io/badge/Python-3.10+-green)]()
[![Node](https://img.shields.io/badge/Node.js-18+-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

---

## 🎯 Project Overview

Deep Agent AGI is a production-ready deep agent framework built on LangGraph DeepAgents with GPT-5 reasoning optimization. The framework provides:

- **Cost Reduction:** Intelligent GPT-5 reasoning effort routing (minimal/low/medium/high)
- **Human-in-the-Loop:** Built-in approval workflows for critical decisions
- **Multi-Agent System:** Sub-agent delegation for specialized tasks
- **Real-time UI:** AG-UI protocol for streaming events and transparency
- **Production-Ready:** Full observability, testing, security scanning

**Core Capabilities:**
- Gmail analysis
- Code generation in secure sandboxes
- GitHub integration
- Calendar management
- Web search (Perplexity MCP)
- Shopping & budgeting
- Retirement planning
- Research & analysis
- OCR & content creation
- Image generation

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Chat UI      │  │ HITL         │  │ Reasoning         │   │
│  │ (AG-UI)      │  │ Approval     │  │ Dashboard         │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬─────────┘   │
│         │                  │                     │              │
│         └─────────WebSocket────────┴─────────────┘              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            API Layer (/api/v1/)                          │  │
│  │  • Agents  • Chat  • Reasoning  • WebSocket Streaming   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│  ┌────────────────────────┴─────────────────────────────────┐  │
│  │           Services Layer                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ Agent        │  │ GPT-5        │  │ Reasoning    │  │  │
│  │  │ Service      │  │ Service      │  │ Router       │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │  │
│  └─────────┼──────────────────┼──────────────────┼──────────┘  │
│            │                  │                  │              │
│  ┌─────────┴──────────────────┴──────────────────┴──────────┐  │
│  │              LangGraph DeepAgents                         │  │
│  │  • Planning Tool  • File Tools  • Sub-Agents  • HITL    │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                            │                                     │
│  ┌────────────────────────┴─────────────────────────────────┐  │
│  │              External Integrations                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│  │
│  │  │ OpenAI   │  │Perplexity│  │LangSmith │  │  Opik   ││  │
│  │  │ GPT-5    │  │   MCP    │  │  Traces  │  │ Prompts ││  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘│  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    DATA LAYER                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ PostgreSQL       │  │ Checkpointer     │  │ Redis        │ │
│  │ (Replit)         │  │ (SQLite/Postgres)│  │ (Phase 2)    │ │
│  │ + pgvector       │  │                  │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ Architectural Decisions (High-Level)

All 33 architectural decisions have been made. See README.md for folder structure details.

### Phase 0 Critical Decisions

**1. Folder Structure & Organization**
- **✅ Decision:** Backend (FastAPI/Python) + Frontend (Next.js/React) separation with feature-based organization
- **Rationale:** Clear separation of concerns, production-ready structure
- **See:** README.md for complete folder structure

**2. Checkpointer Configuration**
- **✅ Decision:** SqliteSaver for Phase 0, PostgresSaver for Phase 1+
- **Rationale:** Simple for MVP, scalable for production
- **Implementation:** `CheckpointerManager` class handles environment-specific checkpointers

**3. Database Schema & Setup**
- **✅ Decision:** Alembic + SQLAlchemy 2.0 with async support
- **Rationale:** Industry standard, excellent pgvector integration, Replit compatible
- **Implementation:** Schema includes Users, Conversations, Memories (vector embeddings), Messages, Provenance, Sessions

**4. Environment Variables**
- **✅ Decision:** Comprehensive .env.example with GPT-5 reasoning configuration
- **Rationale:** Clear documentation of all required settings per environment
- **Implementation:** See `.env.example` in repository

**5. Dependency Management**
- **✅ Decision:** Poetry for Python, npm for Node.js
- **Rationale:** Best lock files, native Replit support, modern pyproject.toml standard
- **Implementation:** `pyproject.toml` + `package.json`

**6. Error Handling & Logging**
- **✅ Decision:** structlog with JSON formatting, custom exception classes, FastAPI global handlers
- **Rationale:** Production-ready structured logging, machine-parseable, excellent for debugging
- **Implementation:** `ErrorCode` enum, `DeepAgentError` base class, environment-specific log formats

**7. API Design & WebSocket Strategy**
- **✅ Decision:** WebSocket for AG-UI events, `/api/v1/` versioning, feature-based routers
- **Rationale:** AG-UI requires WebSocket, clear API versioning, organized by domain
- **Implementation:** FastAPI routers for agents, chat, reasoning, WebSocket streaming

**8. Test Organization & Patterns**
- **✅ Decision:** `test_*.py` naming, hierarchical conftest.py, factory pattern mocks
- **Rationale:** Pytest standard, shared fixtures at appropriate scope, reusable mocks
- **Implementation:** Unit/Integration/E2E/UI test directories with dedicated fixtures

**9. Git Hooks & Pre-commit**
- **✅ Decision:** pre-commit framework with ruff, mypy, detect-secrets
- **Rationale:** Automated quality checks, prevent common issues before commit
- **Implementation:** `.pre-commit-config.yaml` with comprehensive hooks

**10. CI/CD Pipeline**
- **✅ Decision:** GitHub Actions with parallel jobs (lint, test, security, deploy)
- **Rationale:** Native GitHub integration, parallel execution, Replit deployment support
- **Implementation:** `.github/workflows/` with test, security, deploy workflows

**11. Frontend Architecture**
- **✅ Decision:** Next.js App Router + shadcn/ui + Tailwind CSS + Zustand
- **Rationale:** Modern React patterns, AG-UI compatibility, excellent DX
- **Implementation:** App router for SSR, shadcn/ui for components, Zustand for state

**12. Monitoring & Observability**
- **✅ Decision:** LangSmith for traces, built-in logging for Phase 0, add Sentry Phase 1
- **Rationale:** LangSmith essential for agent debugging, structured logs sufficient for MVP
- **Implementation:** LangSmith integration in all agent operations

**13. Opik Setup**
- **✅ Decision:** Opik SDK integrated with agent prompts from day one
- **Rationale:** Auto-prompt optimization critical for cost reduction goal
- **Implementation:** Opik decorators on agent system prompts and tool prompts

**14. Secrets Management**
- **✅ Decision:** Local (.env files) + Replit Secrets + GitHub Secrets
- **Rationale:** Environment-specific secret storage with proper isolation
- **Implementation:** `get_secret()` abstraction layer in `core/secrets.py`

**15. Rate Limiting**
- **✅ Decision:** slowapi library, per-IP + per-user, in-memory Phase 0, Redis Phase 2
- **Rationale:** FastAPI-native, flexible strategy, simple for MVP
- **Implementation:** `@limiter.limit()` decorators on routes

**16. CORS & Security Headers**
- **✅ Decision:** Environment-specific CORS whitelist + comprehensive security headers
- **Rationale:** Secure by default, defense-in-depth approach
- **Implementation:** CORS middleware + `SecurityHeadersMiddleware`

**17. Docker & Replit Compatibility**
- **✅ Decision:** Replit Nix for deployment, optional Docker for local dev
- **Rationale:** Replit-native approach preferred, Docker available if needed
- **Implementation:** `.replit` + `replit.nix` configuration

**18. Linting, Formatting & Code Quality**
- **✅ Decision:** Ruff (linting + formatting) + mypy (type checking)
- **Rationale:** 10-100x faster than alternatives, single tool, excellent VSCode integration
- **Implementation:** `pyproject.toml` configuration, pre-commit hooks

**19. IDE Configuration**
- **✅ Decision:** VSCode/Cursor settings + recommended extensions
- **Rationale:** Consistent development experience across team
- **Implementation:** `.vscode/settings.json`, `.vscode/extensions.json`

**20. Local Development Workflow**
- **✅ Decision:** Scripts in `scripts/` directory, single command startup
- **Rationale:** Simple developer experience, consistent across environments
- **Implementation:** `scripts/dev.sh` for starting all services

**21. Debugging Strategies**
- **✅ Decision:** LangSmith visual debugging + VSCode launch configurations
- **Rationale:** LangGraph-specific debugging crucial for agent development
- **Implementation:** `.vscode/launch.json` with agent debug configs

**22. LLM Output Testing**
- **✅ Decision:** LangSmith evals + custom assertion patterns
- **Rationale:** Handle non-deterministic outputs, track quality regressions
- **Implementation:** Eval suite in `tests/evals/` with LangSmith integration

**23. Load Testing**
- **✅ Decision:** k6 for load testing, scenarios aligned with Replit tier limits
- **Rationale:** Modern, scriptable, excellent reporting
- **Implementation:** Load test scenarios in `tests/load/`

**24. Playwright Test Organization**
- **✅ Decision:** Page Object Model + data-testid selectors
- **Rationale:** Maintainable UI tests, resilient to UI changes
- **Implementation:** `tests/ui/` with page objects

**25. Cost Tracking & Optimization**
- **✅ Decision:** Per-request token tracking + custom cost dashboard
- **Rationale:** Core project goal is cost reduction, need visibility
- **Implementation:** `CostTracker` service, dashboard in frontend

**26. Caching Strategy**
- **✅ Decision:** Redis for Phase 2 (LLM responses, DB queries, API responses)
- **Rationale:** Distributed cache essential for multi-instance production
- **Implementation:** Cache layer with TTL configuration

**27. Performance Budgets**
- **✅ Decision:** <2s simple query latency, <500ms DB queries, 80% test coverage
- **Rationale:** User experience requirements drive technical constraints
- **Implementation:** Performance monitoring + alerts

**28. Architecture Decision Records (ADRs)**
- **✅ Decision:** ADR template in `docs/adr/` for major decisions
- **Rationale:** Document architectural choices with context and rationale
- **Implementation:** ADR template + numbering system

**29. API Documentation**
- **✅ Decision:** Google-style docstrings + enhanced OpenAPI with examples
- **Rationale:** FastAPI auto-generates docs, enhance with rich examples
- **Implementation:** Docstring standards + OpenAPI customization

**30. Operations Manual (Runbook)**
- **✅ Decision:** Runbook in `docs/operations/` with deployment, rollback, troubleshooting
- **Rationale:** Production readiness requires operational documentation
- **Implementation:** Step-by-step procedures for common operations

**31. Custom Tool Development**
- **✅ Decision:** Tool template + error handling patterns + testing template
- **Rationale:** Consistent tool interface, reliable error handling
- **Implementation:** Tool base class + development guide

**32. Sub-Agent Communication**
- **✅ Decision:** Context-passing patterns + error handling + async calls
- **Rationale:** DeepAgents supports sub-agents, need clear communication patterns
- **Implementation:** Sub-agent usage guidelines + examples

**33. Agent State Management**
- **✅ Decision:** State persistence via checkpointer + cleanup strategies + size limits
- **Rationale:** Manage agent state across interactions and sessions
- **Implementation:** `StateManager` with pruning and migration support

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

### Key Architectural Patterns

#### 1. **Reasoning Router Pattern**
Dynamically routes queries to appropriate GPT-5 reasoning effort levels:
- **Minimal:** Simple factual queries (`2+2`, `weather today`)
- **Low:** Basic explanations (`what is Python?`)
- **Medium:** Moderate complexity (`explain OOP concepts`)
- **High:** Complex analysis, triggered phrases (`think harder about quantum computing`)

#### 2. **Event Streaming (AG-UI Protocol)**
Real-time streaming of agent events to frontend:
- Lifecycle events (RunStarted, StepStarted, etc.)
- Text message streaming (token-by-token)
- Tool call transparency (args, results)
- HITL approval workflows

#### 3. **HITL Workflow**
Human-in-the-loop approvals with three options:
- **Accept:** Approve without changes
- **Respond:** Reject with feedback
- **Edit:** Approve with modifications

#### 4. **Checkpointer Strategy**
State persistence across agent interactions:
- Phase 0: SQLite for local/dev
- Phase 1+: PostgreSQL for production
- Enables conversation continuity and HITL

---

## 📁 Project Structure

```
deep-agent-agi/
├── backend/                           # FastAPI backend
│   └── deep_agent/                    # Main application package
│       ├── __init__.py
│       ├── main.py                    # FastAPI app entry point
│       │
│       ├── config/                    # Configuration management
│       │   ├── __init__.py
│       │   ├── settings.py            # Pydantic settings
│       │   ├── gpt5_config.py         # GPT-5 configuration
│       │   └── environments.py        # Environment configs
│       │
│       ├── agents/                    # LangGraph DeepAgents
│       │   ├── __init__.py
│       │   ├── deep_agent.py          # Main agent implementation
│       │   ├── reasoning_router.py    # GPT-5 effort routing
│       │   ├── checkpointer.py        # State persistence
│       │   └── sub_agents/            # Specialized sub-agents
│       │       ├── __init__.py
│       │       ├── research_agent.py
│       │       └── analysis_agent.py
│       │
│       ├── tools/                     # Agent tools
│       │   ├── __init__.py
│       │   ├── file_system.py         # File tools (ls, read, write, edit)
│       │   ├── planning.py            # Planning tool
│       │   ├── web_search.py          # Perplexity MCP integration
│       │   └── custom_tools.py        # Project-specific tools
│       │
│       ├── api/                       # FastAPI routes
│       │   ├── __init__.py
│       │   ├── v1/                    # API version 1
│       │   │   ├── __init__.py
│       │   │   ├── agents.py          # Agent endpoints
│       │   │   ├── chat.py            # Chat/streaming
│       │   │   ├── reasoning.py       # Reasoning analysis
│       │   │   └── websocket.py       # AG-UI WebSocket
│       │   ├── middleware.py          # CORS, rate limiting, auth
│       │   └── dependencies.py        # FastAPI dependencies
│       │
│       ├── models/                    # Pydantic data models
│       │   ├── __init__.py
│       │   ├── gpt5.py                # GPT-5 models
│       │   ├── agents.py              # Agent models
│       │   ├── chat.py                # Chat models
│       │   ├── reasoning.py           # Reasoning models
│       │   ├── database.py            # SQLAlchemy models
│       │   └── common.py              # Shared models
│       │
│       ├── services/                  # Business logic layer
│       │   ├── __init__.py
│       │   ├── gpt5_service.py        # GPT-5 API integration
│       │   ├── reasoning_service.py   # Reasoning analysis
│       │   ├── agent_service.py       # Agent orchestration
│       │   ├── memory_service.py      # Memory/vector DB (Phase 1)
│       │   └── auth_service.py        # Authentication (Phase 1)
│       │
│       ├── core/                      # Core utilities
│       │   ├── __init__.py
│       │   ├── logging.py             # Structured logging (structlog)
│       │   ├── errors.py              # Custom exceptions
│       │   ├── monitoring.py          # LangSmith integration
│       │   ├── security.py            # Security utilities
│       │   ├── database.py            # Database connection manager
│       │   └── secrets.py             # Secrets abstraction
│       │
│       └── integrations/              # External service integrations
│           ├── __init__.py
│           ├── langsmith.py           # LangSmith tracing
│           ├── opik.py                # Prompt optimization
│           ├── mcp_clients/           # MCP server clients
│           │   ├── __init__.py
│           │   ├── playwright.py      # Playwright MCP client
│           │   └── perplexity.py      # Perplexity MCP client
│           └── ag_ui.py               # AG-UI event streaming
│
├── frontend/                          # Next.js frontend (AG-UI)
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Home page
│   │   ├── chat/                      # Chat interface
│   │   │   ├── page.tsx
│   │   │   └── components/
│   │   │       ├── ChatInterface.tsx
│   │   │       ├── ReasoningIndicator.tsx
│   │   │       ├── StreamingMessage.tsx
│   │   │       └── HITLApproval.tsx
│   │   └── reasoning/                 # Reasoning dashboard
│   │       ├── page.tsx
│   │       └── components/
│   │           ├── ReasoningDashboard.tsx
│   │           ├── EffortSelector.tsx
│   │           └── TokenUsageChart.tsx
│   │
│   ├── components/                    # Shared components
│   │   ├── ui/                        # shadcn/ui components
│   │   ├── ag-ui/                     # AG-UI specific
│   │   │   ├── AgentStatus.tsx
│   │   │   ├── ToolCallDisplay.tsx
│   │   │   ├── ReasoningVisualizer.tsx
│   │   │   └── ProgressTracker.tsx
│   │   └── common/                    # Common UI components
│   │
│   ├── lib/                           # Utility libraries
│   │   ├── ag-ui.ts                   # AG-UI client setup
│   │   ├── websocket.ts               # WebSocket client
│   │   ├── reasoning.ts               # Reasoning utilities
│   │   └── utils.ts                   # General utilities
│   │
│   ├── hooks/                         # React hooks
│   │   ├── useAgentState.ts
│   │   ├── useReasoningMode.ts
│   │   └── useWebSocket.ts
│   │
│   ├── types/                         # TypeScript types
│   │   ├── agent.ts
│   │   ├── gpt5.ts
│   │   ├── reasoning.ts
│   │   └── ag-ui.ts
│   │
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── tests/                             # Comprehensive test suite
│   ├── unit/                          # Unit tests (pytest)
│   │   ├── test_agents/
│   │   │   ├── test_reasoning_router.py
│   │   │   ├── test_deep_agent.py
│   │   │   └── test_checkpointer.py
│   │   ├── test_services/
│   │   ├── test_tools/
│   │   ├── test_api/
│   │   └── test_models/
│   │
│   ├── integration/                   # Integration tests
│   │   ├── test_agent_workflows/
│   │   ├── test_api_endpoints/
│   │   ├── test_mcp_integration/
│   │   └── test_database/
│   │
│   ├── e2e/                           # End-to-end tests
│   │   ├── test_complete_workflows/
│   │   ├── test_reasoning_scenarios/
│   │   └── test_user_journeys/
│   │
│   ├── ui/                            # Playwright UI tests
│   │   ├── test_chat_interface.py
│   │   ├── test_reasoning_ui.py
│   │   ├── test_hitl_approval.py
│   │   └── test_agent_dashboard.py
│   │
│   ├── fixtures/                      # Test data
│   │   ├── reasoning_scenarios.json
│   │   ├── agent_configs.py
│   │   └── mock_responses/
│   │
│   ├── mocks/                         # Mock implementations
│   │   ├── mock_gpt5.py
│   │   ├── mock_langsmith.py
│   │   └── mock_mcp_servers.py
│   │
│   └── conftest.py                    # Pytest configuration
│
├── .mcp/                              # MCP server configurations
│   ├── playwright.json
│   ├── perplexity.json
│   └── README.md
│
├── docs/                              # Documentation
│   ├── architecture/
│   │   ├── gpt5_integration.md
│   │   ├── reasoning_system.md
│   │   ├── overview.md
│   │   └── decisions/                 # Architecture Decision Records
│   ├── development/
│   │   ├── setup.md
│   │   ├── testing.md
│   │   └── deployment.md
│   ├── api/                           # API documentation
│   ├── operations/                    # Runbooks
│   │   ├── deployment.md
│   │   ├── rollback.md
│   │   └── troubleshooting.md
│   └── user_guides/
│
├── scripts/                           # Development scripts
│   ├── dev.sh                         # Start development environment
│   ├── test.sh                        # Run test suite
│   ├── security_scan.sh               # TheAuditor security scan
│   ├── quality_check.sh               # Lint, format, type check
│   ├── deploy.sh                      # Deployment script
│   └── setup_env.py                   # Environment setup
│
├── alembic/                           # Database migrations
│   ├── env.py
│   ├── versions/
│   └── alembic.ini
│
├── .github/                           # GitHub Actions CI/CD
│   └── workflows/
│       ├── test.yml                   # Test workflow
│       ├── security.yml               # TheAuditor integration
│       └── deploy.yml                 # Deployment workflow
│
├── .vscode/                           # VSCode/Cursor settings
│   ├── settings.json
│   ├── extensions.json
│   └── launch.json
│
├── pyproject.toml                     # Poetry configuration
├── poetry.lock                        # Poetry lock file
├── package.json                       # Node.js dependencies (Playwright MCP)
├── package-lock.json
│
├── .env.example                       # Environment template
├── .gitignore
├── .pre-commit-config.yaml            # Pre-commit hooks
│
├── .replit                            # Replit configuration
├── replit.nix                         # Replit Nix configuration
│
├── CLAUDE.md                          # Development guide (this file)
└── README.md                          # Architecture overview (you are here)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** (for Phase 1+, Replit provides this)
- **Git**

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/deep-agent-agi.git
cd deep-agent-agi

# 2. Install Poetry (Python dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Install Python dependencies
poetry install

# 4. Install Node.js dependencies
npm install

# 5. Install Playwright browsers
npx playwright install
npx playwright install-deps

# 6. Install TheAuditor (security scanning)
git clone https://github.com/TheAuditorTool/Auditor
cd TheAuditor && pip install -e .
cd ..

# 7. Set up environment variables
cp .env.example .env
# Edit .env with your API keys (OpenAI, Perplexity, LangSmith, etc.)

# 8. Initialize database (Phase 1+)
alembic upgrade head
```

### Run Development Server

```bash
# Start backend (FastAPI)
poetry run uvicorn backend.deep_agent.main:app --reload --port 8000

# Start frontend (Next.js) - in separate terminal
cd frontend
npm run dev
```

### Run Tests

```bash
# All tests with coverage
pytest --cov

# Unit tests only
pytest tests/unit/

# UI tests (Playwright)
pytest tests/ui/

# Security scan (TheAuditor)
aud init && aud full
```

---

## 💻 Technology Stack

### Backend
- **Framework:** LangGraph DeepAgents
- **LLM:** OpenAI GPT-5 with variable reasoning
- **API:** FastAPI (async Python)
- **Database:** PostgreSQL + pgvector (Replit)
- **Checkpointer:** SQLite (Phase 0) → PostgreSQL (Phase 1+)
- **Monitoring:** LangSmith
- **Prompt Optimization:** Opik

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **UI Library:** shadcn/ui + Tailwind CSS
- **State Management:** Zustand
- **Protocol:** AG-UI for agent event streaming
- **Real-time:** WebSocket for bidirectional communication

### Testing
- **Unit/Integration/E2E:** pytest + pytest-cov
- **UI Testing:** Playwright MCP
- **Load Testing:** k6
- **Security:** TheAuditor

### Development Tools
- **Linting/Formatting:** Ruff (10-100x faster than alternatives)
- **Type Checking:** mypy
- **Pre-commit Hooks:** pre-commit framework
- **CI/CD:** GitHub Actions
- **Code Review:** CodeRabbit CLI (when available)

### MCP Servers
- **Playwright MCP:** UI testing automation
- **Perplexity MCP:** Web search integration
- **Custom MCP:** Built with fastmcp (Phase 2)

### Infrastructure
- **Deployment:** Replit (dev/staging/prod)
- **WAF:** Cloudflare (Phase 2)
- **Caching:** Redis (Phase 2)
- **Load Balancing:** Nginx/cloud-native (Phase 2)

---

## 🔐 Security

### Built-in Security Features

1. **TheAuditor Integration**
   - AI-assisted security scanning
   - Automatic vulnerability detection
   - Reports in `.pf/readthis/` directory
   - Run: `aud init && aud full`

2. **Security Headers**
   - CORS whitelist (environment-specific)
   - CSP (Content Security Policy)
   - HSTS (Strict-Transport-Security)
   - X-Frame-Options, X-Content-Type-Options

3. **Rate Limiting**
   - Per-IP + per-user limits
   - Special limits for expensive operations (high reasoning)
   - In-memory (Phase 0) → Redis (Phase 2)

4. **Authentication & IAM (Phase 1)**
   - OAuth 2.0 authentication
   - Least-privilege access
   - Rotating credentials (24-48h)
   - Ephemeral tokens

5. **Secrets Management**
   - Local: `.env` files (gitignored)
   - Replit: Replit Secrets
   - CI/CD: GitHub Secrets
   - No hardcoded secrets anywhere

### Security Testing

- **Prompt injection** attack prevention
- **Authorization bypass** testing
- **Data exfiltration** prevention
- **Rate limit** validation
- **Input sanitization** verification

**Run Security Scan:**
```bash
aud full
cat .pf/readthis/*  # Review findings
```

---

## 📊 Monitoring & Observability

### LangSmith Integration

All agent operations are traced in LangSmith:
- Agent runs (start, steps, finish)
- Tool calls (args, results, duration)
- Sub-agent invocations
- Error states and exceptions
- Performance metrics

**View Traces:** https://smith.langchain.com

### Structured Logging (structlog)

JSON-formatted logs for production:
- Environment-specific formats (human-readable local, JSON prod)
- Request/response logging with duration
- Error tracking with stack traces
- Reasoning decision logging

### Cost Tracking

Per-request token usage tracking:
- GPT-5 token counts by reasoning effort
- Cost calculation per model
- Budget alerts
- Custom cost dashboard (frontend)

---

## 🧪 Testing Strategy

### Test Coverage Requirements

- **Minimum:** 80% code coverage
- **Block merge** if coverage drops below threshold
- **Automated reports** generated on every test run

### Test Categories

| Category | Tool | Coverage |
|----------|------|----------|
| Unit Tests | pytest | Functions, methods, tools |
| Integration Tests | pytest | Workflows, tool chains, API |
| E2E Tests | pytest | Complete user journeys |
| UI Tests | Playwright MCP | Browser automation, visual regression |
| Load Tests | k6 | Concurrent users, rate limiting |
| Security Tests | TheAuditor | Vulnerabilities, prompt injection |

### Running Tests

```bash
# All tests with coverage report
pytest --cov --html=reports/test_report.html

# Specific test categories
pytest tests/unit/                      # Unit tests
pytest tests/integration/               # Integration tests
pytest tests/e2e/                       # E2E tests
pytest tests/ui/                        # Playwright UI tests

# Parallel execution (faster)
pytest -n auto

# Watch mode (re-run on file changes)
pytest --watch

# Generate detailed report
pytest --cov --cov-report=html --html=reports/test_report.html
```

---

## 📈 Development Workflow

### Phase-Based Development

**Phase 0 (MVP):** Core agent + basic UI + monitoring
**Phase 1 (Production):** Memory + auth + reasoning optimization
**Phase 2 (Research):** Deep research + infrastructure hardening

### Commit Discipline

**Commit constantly:** Every logical unit of work gets committed immediately.

**Semantic Commit Messages:**
```bash
feat(phase-0): implement DeepAgents file system tools
fix(agents): resolve HITL approval timeout
test(ui): add Playwright tests for chat interface
security(phase-1): address TheAuditor findings
docs(readme): update architecture diagram
chore(deps): upgrade langchain to 0.3.x
```

### Pre-commit Checks

Automated on every commit:
- Ruff linting & formatting
- mypy type checking
- detect-secrets scan
- Trailing whitespace removal
- YAML/JSON/TOML validation

### CI/CD Pipeline

GitHub Actions workflow runs on every push:
1. **Lint:** Ruff check + format check
2. **Type Check:** mypy
3. **Unit Tests:** pytest with coverage
4. **Integration Tests:** pytest
5. **UI Tests:** Playwright MCP
6. **Security Scan:** TheAuditor
7. **E2E Tests:** Full workflows
8. **Deploy:** Replit (if all pass)

---

## 🎯 Phase 0 Success Criteria

- [x] All 33 architectural decisions made
- [ ] DeepAgents framework integrated
- [ ] GPT-5 streaming responses working
- [ ] AG-UI event streaming functional
- [ ] HITL approval workflow complete
- [ ] Perplexity MCP web search integrated
- [ ] LangSmith tracing operational
- [ ] 80%+ test coverage achieved
- [ ] TheAuditor security scan passing
- [ ] FastAPI backend deployed

**See CLAUDE.md for complete success criteria and development guide.**

---

## 📚 Key Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Complete development guide for Claude Code
- **[.env.example](./.env.example)** - Environment variable template
- **[docs/architecture/](./docs/architecture/)** - Architecture decisions and diagrams
- **[docs/development/](./docs/development/)** - Setup, testing, deployment guides
- **[docs/operations/](./docs/operations/)** - Runbooks for deployment, rollback, troubleshooting

---

## 🔗 Key Resources

### Framework & Core
- [LangGraph DeepAgents](https://github.com/langchain-ai/deepagents)
- [Open Deep Research](https://github.com/langchain-ai/open_deep_research)
- [AG-UI Protocol](https://docs.ag-ui.com/sdk/python/core/overview)

### LLM & Optimization
- [GPT-5 Documentation](https://platform.openai.com/docs/guides/latest-model)
- [GPT-5 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)
- [Opik Prompt Optimization](https://opik.ai/docs)

### MCP Servers
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Perplexity MCP](https://github.com/perplexityai/modelcontextprotocol)
- [Playwright MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/playwright)

### Monitoring & Tools
- [LangSmith](https://docs.smith.langchain.com/reference/python/reference)
- [TheAuditor Security](https://github.com/TheAuditorTool/Auditor)
- [Playwright Testing](https://playwright.dev/)

---

## 🤝 Contributing

1. **Follow CLAUDE.md development principles**
2. **Write tests first** (TDD approach)
3. **Commit constantly** (semantic messages)
4. **Run security scan** after changes (`aud full`)
5. **Maintain 80%+ test coverage**
6. **Request CodeRabbit review** (when available)

---

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details

---

## 👥 Team

Built with ❤️ using Claude Code

**Contact:** [your-email@example.com]

---

## ⚡ Quick Commands Reference

```bash
# Development
poetry run uvicorn backend.deep_agent.main:app --reload
cd frontend && npm run dev

# Testing
pytest --cov                                    # All tests
pytest tests/ui/ -v                             # UI tests only
./scripts/test.sh                               # Full test suite

# Code Quality
ruff check . && ruff format .                   # Lint & format
mypy backend/deep_agent/                        # Type checking
./scripts/quality_check.sh                      # All checks

# Security
aud init && aud full                            # Security scan
cat .pf/readthis/*                              # Review findings

# Git Workflow
git add <files>
git commit -m "feat(phase-X): description"      # Semantic commit
git push origin feat/your-feature               # Push feature branch
```

---

**Remember:** Evaluation-driven, test-driven, phase-driven, commit-driven, security-first.

Build incrementally, commit constantly, test thoroughly, scan for security issues, measure continuously, deploy confidently.
