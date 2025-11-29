# Deep Agent One

> **Phase 0 Prototype: Core framework demonstrating intelligent reasoning optimization and cost reduction**

[![Phase](https://img.shields.io/badge/Phase-0--Prototype-orange)]()
[![Python](https://img.shields.io/badge/Python-3.10+-green)]()
[![Node](https://img.shields.io/badge/Node.js-18+-green)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)]()

---

## 🎯 Overview

Deep Agent One is a **Phase 0 prototype** deep agent framework built on LangGraph DeepAgents with **Gemini 3 Pro** as the primary model and **GPT-5.1** as automatic fallback. This prototype demonstrates the core framework capabilities with basic features.

**What This Prototype Provides:**

- **Dual-Model Stack:** Gemini 3 Pro (primary) with GPT-5.1 automatic fallback on errors
- **Prompt Optimization:** Opik integration with 6 optimization algorithms (Hierarchical, Bayesian, Evolutionary, MetaPrompt, GEPA, Parameter)
- **Human-in-the-Loop:** Built-in approval workflows for critical decisions
- **Real-time Transparency:** AG-UI protocol for streaming events and tool call visibility
- **Web Search:** Perplexity MCP integration for web queries
- **File Operations:** Read, write, edit, and list files
- **Observability:** LangSmith tracing for debugging and monitoring

**Phase 0 Status:**

This is a working prototype demonstrating core framework capabilities. Future phases will add production-grade features like memory systems, advanced authentication, and deep research capabilities.

---

## ✨ Features

### Currently Implemented (Phase 0)

**Chat Interface**
- Real-time streaming responses with token-by-token display
- Conversation history and context tracking
- WebSocket-based bidirectional communication

**Dual-Model Architecture**
- **Primary:** Google Gemini 3 Pro with configurable thinking depth (low/medium/high)
- **Fallback:** OpenAI GPT-5.1 with automatic failover on rate limits, timeouts, or errors
- Intelligent model routing with seamless switching
- Per-request cost tracking and model attribution

**Opik Prompt Optimization** (Available)
- 6 optimization algorithms: Hierarchical, Bayesian, Evolutionary, MetaPrompt, GEPA, Parameter
- Prompt analysis against GPT best practices
- A/B testing infrastructure for prompt comparison
- Automatic evaluation dataset generation

**Reasoning Effort Routing** (Phase 0 Stub)
- Infrastructure for 4 effort levels: minimal, low, medium, high
- Phase 0: Fixed at MEDIUM effort (dynamic routing coming in Phase 1)
- Configurable timeouts per effort level
- Trigger phrase detection (Phase 1)

**Web Search**
- Perplexity MCP integration for web queries
- Search results with source citations
- Seamless integration into agent responses

**Human-in-the-Loop (HITL)**
- Built-in approval workflow for critical operations
- Three response options: Accept, Respond (with feedback), Edit
- Real-time approval requests in UI
- Conversation continuity after approval/rejection

**File System Tools**
- `ls`: List directory contents
- `read_file`: Read file contents
- `write_file`: Create or overwrite files
- `edit_file`: Modify existing files

**Planning & Task Tracking**
- TodoWrite-based planning tool
- Real-time task list updates in UI
- Subtask progress visualization

**Agent Transparency**
- Real-time tool call display (args and results)
- Agent state visualization
- Step-by-step execution tracking
- "Inspect source" toggle for detailed tool information

**Monitoring & Observability**
- LangSmith tracing for all agent operations
- Structured logging (JSON in production, human-readable locally)
- Error tracking with trace IDs
- Cost tracking per request

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐      │
│  │ Chat UI      │  │ HITL         │  │ Reasoning         │      │
│  │ (AG-UI)      │  │ Approval     │  │ Dashboard         │      │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬─────────┘      │
│         │                 │                    │                │
│         └─────────WebSocket────────┴───────────┘                │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            API Layer (/api/v1/)                          │   │
│  │  • Agents  • Chat  • Reasoning  • WebSocket Streaming    │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────┴─────────────────────────────────┐   │
│  │           Services Layer                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │ Agent        │  │ LLM          │  │ Reasoning    │    │   │
│  │  │ Service      │  │ Factory      │  │ Router       │    │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │   │
│  └─────────┼─────────────────┼─────────────────┼──────────┘     │
│            │                 │                 │                │
│  ┌─────────┴─────────────────┴─────────────────┴──────────┐     │
│  │              LangGraph DeepAgents                        │   │
│  │  • Planning Tool  • File Tools  • Sub-Agents  • HITL     │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────┴─────────────────────────────────┐   │
│  │              External Integrations                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Google   │  │ OpenAI   │  │Perplexity│  │LangSmith │ │   │
│  │  │ Gemini   │  │ GPT-5.1  │  │   MCP    │  │  Traces  │ │   │
│  │  │(Primary) │  │(Fallback)│  │          │  │          │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                    DATA LAYER (Phase 0)                         │
│  ┌──────────────────┐                                            │
│  │ SQLite           │  Checkpointer for agent state             │
│  │ Checkpointer     │  (conversation history, HITL state)       │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Patterns

#### 1. **Model Fallback Pattern**
Primary model (Gemini 3 Pro) with automatic failover to GPT-5.1:
- **Rate limit handling:** Seamless switch on 429 errors
- **Timeout recovery:** Fallback on slow responses
- **Connection resilience:** Retry with alternate model
- **Transparent switching:** User sees consistent experience

#### 2. **Reasoning Router Pattern** (Phase 0 Stub)
Infrastructure for dynamic routing (full implementation in Phase 1):
- **Minimal/Low/Medium/High** effort levels defined
- **Phase 0:** Fixed at MEDIUM (stub implementation)
- **Phase 1:** Trigger phrase detection + complexity analysis

#### 3. **Event Streaming (AG-UI Protocol)**
Real-time streaming of agent events to frontend:
- Lifecycle events (RunStarted, StepStarted, etc.)
- Text message streaming (token-by-token)
- Tool call transparency (args, results)
- HITL approval workflows

#### 4. **HITL Workflow**
Human-in-the-loop approvals with three options:
- **Accept:** Approve without changes
- **Respond:** Reject with feedback
- **Edit:** Approve with modifications

#### 5. **Checkpointer Strategy**
State persistence across agent interactions:
- Phase 0: SQLite for local development
- Enables conversation continuity and HITL workflows

### Technology Stack

**Backend:**
- Framework: LangGraph DeepAgents
- LLM: Google Gemini 3 Pro (primary) + OpenAI GPT-5.1 (fallback)
- Prompt Optimization: Opik (6 algorithms)
- API: FastAPI (async Python 3.10+)
- State Management: SQLite checkpointer
- Monitoring: LangSmith

**Frontend:**
- Framework: Next.js 14+ (App Router)
- UI: shadcn/ui + Tailwind CSS
- State: Zustand
- Protocol: AG-UI for event streaming
- WebSocket: Real-time bidirectional communication

**External Integrations:**
- Google Gemini: Primary LLM (Gemini 3 Pro)
- OpenAI: Fallback LLM (GPT-5.1)
- Opik: Prompt optimization and A/B testing
- Perplexity MCP: Web search
- LangSmith: Agent tracing and observability

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Git**
- **API Keys:** Google (Gemini), OpenAI (fallback), Perplexity, LangSmith (optional)

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/deep-agent-one.git
cd deep-agent-one

# 2. Install Poetry (Python dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Install Python dependencies
poetry install

# 4. Install Node.js dependencies
npm install

# 5. Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
#   - GOOGLE_API_KEY (required - Gemini 3 Pro, primary model)
#   - OPENAI_API_KEY (required - GPT-5.1 fallback)
#   - PERPLEXITY_API_KEY (required for web search)
#   - LANGSMITH_API_KEY (optional, for tracing)

# 6. Start the servers
./scripts/start-all.sh
```

**Access Points:**
- Backend API: http://127.0.0.1:8000
- Frontend UI: http://localhost:3000
- API Docs: http://127.0.0.1:8000/docs

### Replit Deployment

This prototype is optimized for deployment on Replit:

**One-Click Deploy:**
1. Fork this repository on Replit
2. Configure Secrets in Replit dashboard:
   - `GOOGLE_API_KEY` (Gemini 3 Pro - primary)
   - `OPENAI_API_KEY` (GPT-5.1 - fallback)
   - `PERPLEXITY_API_KEY`
   - `LANGSMITH_API_KEY` (optional)
3. Click "Run" - Replit automatically:
   - Installs Python/Node dependencies
   - Starts backend (FastAPI) on port 8000
   - Starts frontend (Next.js) on port 3000

**Environment Configuration:**
```bash
# Replit automatically loads secrets from the Secrets tab
# No .env file needed on Replit

# Verify deployment:
curl https://your-repl-name.replit.app/health
```

### Environment Variables

**Required:**
```bash
GOOGLE_API_KEY=...                       # Google API key for Gemini 3 Pro (primary)
OPENAI_API_KEY=sk-...                    # OpenAI API key for GPT-5.1 (fallback)
PERPLEXITY_API_KEY=pplx-...             # Perplexity API key for web search
```

**Optional:**
```bash
LANGSMITH_API_KEY=ls__...               # LangSmith tracing (recommended)
LANGSMITH_PROJECT=deep-agent-one        # Project name in LangSmith

# Reasoning configuration (defaults shown)
GPT5_REASONING_MINIMAL=minimal          # Effort level for simple queries
GPT5_REASONING_LOW=low                  # Effort level for basic queries
GPT5_REASONING_MEDIUM=medium            # Effort level for moderate queries
GPT5_REASONING_HIGH=high                # Effort level for complex queries

# Rate limiting (Phase 0 defaults)
RATE_LIMIT_PER_MINUTE=60                # Requests per minute per IP
```

See `.env.example` for complete configuration template.

---

## 📖 User Guide

### Using the Chat Interface

**Starting a Conversation:**
1. Navigate to http://localhost:3000 (or your Replit URL)
2. Type your message in the chat input
3. Press Enter or click Send
4. Watch the agent respond in real-time (token-by-token streaming)

**Understanding the Model Stack:**

Deep Agent One uses a dual-model architecture:

- **Primary:** Google Gemini 3 Pro with configurable thinking depth
- **Fallback:** OpenAI GPT-5.1 (automatic on errors/rate limits)

The model automatically switches if the primary model fails, ensuring reliable responses.

**Reasoning Effort (Phase 0):**

> Note: In Phase 0, reasoning effort is fixed at MEDIUM. Dynamic routing based on query complexity will be added in Phase 1.

Infrastructure exists for 4 effort levels:
- **Minimal** (⚡): Fast, simple queries (Phase 1)
- **Low** (💡): Basic explanations (Phase 1)
- **Medium** (🧠): Current default for all queries
- **High** (🚀): Complex analysis with trigger phrases (Phase 1)

**Coming in Phase 1:**
- Trigger phrase detection ("think harder about...")
- Query complexity analysis
- Dynamic effort routing

### HITL Approval Workflow

**When the agent needs approval:**

1. **Approval Request Appears:** Agent pauses and displays the action requiring approval
2. **Three Options:**
   - **Accept:** Proceed with the action as-is
   - **Respond:** Reject and provide feedback (agent will adjust)
   - **Edit:** Modify the action then approve

3. **Response:** Agent continues based on your decision

**Example HITL Scenario:**
```
Agent: "I need approval to delete file: important-data.txt"

Options:
[ Accept ]  [ Respond ]  [ Edit ]

You: [Respond] "Please back it up first"

Agent: "I'll create a backup at important-data.txt.bak first"
```

### Viewing Agent Activity

**Tool Call Transparency:**

Click "Inspect" next to any agent response to see:
- Tool name and invocation time
- Input arguments (JSON format)
- Output results
- Execution duration

**Example Tool Call Display:**
```
Tool: web_search
Args: { "query": "latest Python news" }
Result: [5 search results with titles and URLs]
Duration: 1.2s
```

**Task Progress:**

Watch the subtask list (left sidebar) for:
- Current task being executed
- Completed tasks (checked off)
- Pending tasks (queued)

### Cost Tracking

**Per-Request Costs:**

Each response shows:
- Tokens used (input + output)
- Reasoning effort level
- Estimated cost in USD

**Cost Optimization Tips:**
- Use simple queries when possible (triggers minimal reasoning)
- Avoid trigger phrases unless needed
- Break complex queries into simpler sub-queries

---

## 🔌 API Reference

### WebSocket Endpoint

**Endpoint:** `ws://localhost:8000/ws/chat`

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  console.log('Connected to agent');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

**Message Format (Client → Server):**
```json
{
  "type": "user_message",
  "content": "Your message here",
  "thread_id": "optional-thread-id",
  "reasoning_effort": "auto"  // or "minimal", "low", "medium", "high"
}
```

**Event Types (Server → Client):**

**Text Streaming:**
```json
{
  "type": "text_message_start",
  "message_id": "msg_123"
}
{
  "type": "text_message_content",
  "message_id": "msg_123",
  "content": "Hello"
}
{
  "type": "text_message_end",
  "message_id": "msg_123"
}
```

**Tool Calls:**
```json
{
  "type": "tool_call_start",
  "tool_name": "web_search",
  "tool_call_id": "call_456"
}
{
  "type": "tool_call_args",
  "tool_call_id": "call_456",
  "args": {"query": "Python news"}
}
{
  "type": "tool_call_result",
  "tool_call_id": "call_456",
  "result": ["Result 1", "Result 2"]
}
```

**HITL Approval:**
```json
{
  "type": "hitl_approval_required",
  "approval_id": "hitl_789",
  "action": "delete_file",
  "details": {"file_path": "/data/file.txt"}
}

// Client responds with:
{
  "type": "hitl_response",
  "approval_id": "hitl_789",
  "action": "accept"  // or "respond", "edit"
}
```

**Errors:**
```json
{
  "type": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

### REST Endpoints

**Health Check:**
```bash
GET /health

Response:
{
  "status": "healthy",
  "version": "0.1.0-phase0"
}
```

**API Documentation:**
```bash
GET /docs  # Interactive Swagger UI
GET /redoc # ReDoc documentation
```

### Rate Limits

**Phase 0 Limits:**
- **Per IP:** 60 requests/minute
- **WebSocket connections:** 5 concurrent per IP
- **Message size:** 100KB max

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1634567890
```

**Rate Limit Exceeded Response:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## ⚡ Performance & Limits

### Expected Response Times (Phase 0 Prototype)

| Query Type | Reasoning Effort | Expected Latency | Example |
|------------|------------------|------------------|---------|
| Simple | Minimal | TBDs | "What is 2+2?" |
| Basic | Low | TBDs | "What is Python?" |
| Moderate | Medium | TBDs | "Explain OOP" |
| Complex | High | TBDs | "Analyze quantum computing" |

**Note:** Response times include network latency, LLM inference, and streaming overhead.

### Current Limitations

**Prototype Constraints:**
- **No memory system:** Each conversation is independent (no long-term memory)
- **No authentication:** Open access (secure your deployment)
- **No rate limiting per user:** Only per-IP limits
- **SQLite checkpointer:** Not suitable for high concurrency
- **No multi-user:** Designed for single-user testing
- **Reasoning fixed at MEDIUM:** Dynamic effort routing coming in Phase 1
- **Opik not integrated:** Prompt optimization tools available but not in agent runtime

**Known Issues:**
- WebSocket connections may timeout after 60 seconds of inactivity
- Large file operations (>1MB) may be slow
- Complex reasoning (high effort) can take 15+ seconds

### Cost Estimates

**Model costs vary:**
- **Gemini 3 Pro (Primary):** Generally lower cost per token
- **GPT-5.1 (Fallback):** Used only on primary model failures

**Cost factors:**
- Query complexity
- Response length
- Tool usage (web search adds $0.01-0.05)
- Model used (Gemini vs GPT-5.1)

**Cost Optimization:**
- Gemini 3 Pro is preferred for cost efficiency
- Cache common queries (not implemented in Phase 0)
- Use specific, targeted questions

---

## 🔐 Security

### Built-in Protections

**Rate Limiting:**
- Per-IP request limits (60/minute)
- Concurrent WebSocket connection limits (5/IP)
- Protection against DoS attacks

**Input Validation:**
- Message size limits (100KB max)
- JSON schema validation
- SQL injection prevention (parameterized queries)

**Security Headers:**
- CORS whitelist (environment-specific)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY

### Data Privacy

**Phase 0 Prototype:**
- No persistent user data storage
- Conversation state in SQLite (local only)
- LangSmith traces (optional, can be disabled)

**Data Handling:**
- API keys stored in environment variables only
- No hardcoded secrets in codebase
- Logs do not contain API keys or sensitive data

### Recommended Deployment Security

**For Public Deployments:**
1. **Add authentication:** Implement API key or OAuth before public deployment
2. **Use HTTPS:** Always deploy with SSL/TLS certificates
3. **Firewall rules:** Restrict access to known IPs if possible
4. **Monitor logs:** Watch for suspicious activity patterns
5. **Rotate API keys:** Change OpenAI/Perplexity keys regularly

**Environment Variables:**
```bash
# Never commit these to version control
OPENAI_API_KEY=...
PERPLEXITY_API_KEY=...
LANGSMITH_API_KEY=...
```

---

## 🔧 Troubleshooting

### Common Issues

**Issue: "WebSocket connection failed"**
```
Symptoms: Chat interface shows "Disconnected" status
Cause: Backend not running or CORS misconfiguration

Solution:
1. Verify backend is running: curl http://localhost:8000/health
2. Check backend logs: tail -f logs/backend/*.log
3. Verify CORS settings in .env
```

**Issue: "API key not found"**
```
Symptoms: Error message "OpenAI API key not configured"
Cause: Missing or invalid OPENAI_API_KEY

Solution:
1. Check .env file exists
2. Verify OPENAI_API_KEY is set: echo $OPENAI_API_KEY
3. Restart backend after setting: ./scripts/start-backend.sh
```

**Issue: "Rate limit exceeded"**
```
Symptoms: HTTP 429 error, message "Rate limit exceeded"
Cause: Too many requests from same IP

Solution:
1. Wait 60 seconds before retrying
2. Check for infinite loops or automated scripts
3. Increase limit in .env: RATE_LIMIT_PER_MINUTE=120
```

**Issue: "Slow responses (>30 seconds)"**
```
Symptoms: Agent takes very long to respond
Cause: High reasoning effort or network issues

Solution:
1. Check reasoning effort level (visible in UI)
2. Use simpler queries or avoid trigger phrases
3. Verify network connection to OpenAI
4. Check LangSmith traces for bottlenecks
```

**Issue: "HITL approval hangs"**
```
Symptoms: Approval request never completes
Cause: WebSocket connection lost during approval

Solution:
1. Refresh the page
2. Check WebSocket connection status
3. Review backend logs for errors
```

### Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry |
| `INVALID_API_KEY` | OpenAI key invalid | Check environment variables |
| `WEBSOCKET_CLOSED` | Connection lost | Refresh page |
| `TOOL_EXECUTION_FAILED` | Tool error | Check tool arguments |
| `INTERNAL_SERVER_ERROR` | Backend crash | Check logs, restart |

### Getting Help

**Debugging Steps:**
1. Check backend logs: `tail -f logs/backend/*.log`
2. Check frontend logs: Browser console (F12)
3. View LangSmith traces: https://smith.langchain.com (if configured)
4. Review error messages in UI

**Log Locations:**
```bash
# Backend logs (timestamped)
logs/backend/2025-11-17-*.log

# Frontend logs (timestamped)
logs/frontend/2025-11-17-*.log
```

**Reporting Issues:**
- Include error messages from logs
- Include steps to reproduce
- Include environment details (OS, Python/Node versions)
- Open an issue on GitHub

---

## 🤝 Contributing

This is a **Phase 0 prototype**. Contributions are welcome for:
- Bug fixes
- Documentation improvements
- Test coverage
- Performance optimizations

**Development Setup:**

See [CLAUDE.md](./CLAUDE.md) for complete development guide, including:
- TDD workflow (write tests first)
- Commit discipline (semantic commits)
- Pre-commit checks (linting, type checking)
- Security scanning (TheAuditor)

**Quick Start for Contributors:**
```bash
# Fork and clone
git clone https://github.com/yourusername/deep-agent-one.git

# Install development dependencies
poetry install
npm install

# Run tests
pytest --cov

# Make changes, write tests, commit
git commit -m "feat(phase-0): add feature X"
```

---

## 📚 Documentation

### Key Documents

- **[CLAUDE.md](./CLAUDE.md)** - Complete development guide
- **[.env.example](./.env.example)** - Environment variable template
- **[docs/architecture/](./docs/architecture/)** - Architecture details
- **[docs/operations/](./docs/operations/)** - Deployment guides

### Technical References

**Framework & Core:**
- [LangGraph DeepAgents](https://github.com/langchain-ai/deepagents)
- [AG-UI Protocol](https://docs.ag-ui.com/sdk/python/core/overview)

**LLM & APIs:**
- [Gemini API Documentation](https://ai.google.dev/docs)
- [GPT-5 Documentation](https://platform.openai.com/docs/guides/latest-model)
- [Opik Prompt Optimization](https://www.comet.com/docs/opik/)
- [Perplexity MCP](https://github.com/perplexityai/modelcontextprotocol)

**Monitoring:**
- [LangSmith](https://docs.smith.langchain.com/reference/python/reference)

---

## 📄 License

Apache 2.0 License - see [LICENSE](./LICENSE) for details

---

## 👥 About

**Phase 0 Prototype** - Demonstrating core framework capabilities with dual-model architecture and prompt optimization.

Built with Claude Code using LangGraph DeepAgents, Gemini 3 Pro, GPT-5.1, and Opik.

**Roadmap:**
- **Phase 1:** Production features (memory, auth, dynamic reasoning, Opik integration)
- **Phase 2:** Deep research capabilities and infrastructure hardening

**Contact:** [your-email@example.com]

---

**Phase 0 Prototype** | Gemini 3 Pro + GPT-5.1 + Opik | [View on GitHub](https://github.com/yourusername/deep-agent-one)
