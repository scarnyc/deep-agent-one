# Deep Agent One - Replit Project

## Overview
Deep Agent One is a Phase 0 prototype deep agent framework built on LangGraph DeepAgents with GPT-5 reasoning optimization and Google Gemini 3 Pro. This project demonstrates core framework capabilities with basic features including cost reduction through intelligent reasoning routing, human-in-the-loop workflows, real-time transparency, web search, and file operations.

## Project Structure
```
.
├── backend/              # Python FastAPI backend
│   └── deep_agent/       # Main application package
│       ├── agents/       # Agent implementations
│       ├── api/          # REST API endpoints
│       ├── config/       # Configuration management
│       ├── core/         # Core utilities
│       ├── integrations/ # External service integrations
│       ├── models/       # Data models
│       ├── services/     # Business logic
│       └── tools/        # Agent tools
├── frontend/             # Next.js 14+ frontend
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── contexts/         # React contexts
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utility libraries
│   └── types/            # TypeScript type definitions
├── db/                   # Database files
│   ├── data/             # SQLite checkpoints
│   └── migrations/       # Database migrations
├── scripts/              # Startup and utility scripts
│   ├── start-replit.sh   # Development startup (Run button)
│   └── start-replit-prod.sh  # Production deployment
└── tests/                # Test suites
```

## Running the Application

### Quick Start (Development)
1. **Add API keys** to Replit Secrets (Tools > Secrets):
   - `OPENAI_API_KEY` - OpenAI GPT-5.1 (fallback)
   - `GOOGLE_API_KEY` - Google Gemini 3 Pro (primary)
   - `PERPLEXITY_API_KEY` - Web search (optional)
   - `LANGSMITH_API_KEY` - Tracing (optional)

2. **Click the Run button** - Both services start automatically:
   - **Backend:** FastAPI on port 8000 (internal)
   - **Frontend:** Next.js on port 5000 (visible in webview)

3. **Use the webview** to interact with the chat interface

### Services
| Service | Port | Access |
|---------|------|--------|
| Frontend | 5000 | Replit webview (external port 80) |
| Backend | 8000 | Internal API (external port 8000) |

### Deployment
The app is configured for Replit Deployments with autoscale:
- Build: `poetry install --only main && pnpm install && pnpm build`
- Run: `./scripts/start-replit-prod.sh`

## Configuration

### Secrets (Sensitive - Store in Replit Secrets)
**Required:**
- `OPENAI_API_KEY` - OpenAI API key for GPT-5.1 fallback model
- `GOOGLE_API_KEY` - Google API key for Gemini 3 Pro primary model

**Optional:**
- `PERPLEXITY_API_KEY` - Web search functionality
- `LANGSMITH_API_KEY` - Agent tracing and monitoring
- `OPIK_API_KEY` - Prompt optimization
- `SECRET_KEY` - App security (generate: `openssl rand -hex 32`)
- `JWT_SECRET` - Token signing (generate: `openssl rand -hex 32`)

### Environment Variables (Non-Sensitive - in `.env`)
The `.env` file contains non-sensitive configuration like model names, timeouts, and feature flags. See `.env.example` for all options.

## Technology Stack

### Backend
- **Framework:** FastAPI (async Python 3.11+)
- **AI Framework:** LangGraph DeepAgents
- **LLMs:**
  - Primary: Google Gemini 3 Pro
  - Fallback: OpenAI GPT-5.1
- **State Management:** SQLite checkpointer
- **Monitoring:** LangSmith (optional)

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **UI Library:** shadcn/ui + Tailwind CSS
- **State Management:** Zustand
- **Protocol:** AG-UI for event streaming
- **Communication:** WebSocket for real-time updates

### External Integrations
- Perplexity MCP: Web search functionality
- LangSmith: Agent tracing and observability
- Opik: Prompt optimization (optional)

## Project Goals

### Phase 0 (Current)
- ✅ Core framework with basic agent capabilities
- ✅ GPT-5 and Gemini 3 reasoning optimization
- ✅ Human-in-the-loop workflows
- ✅ Real-time streaming responses
- ✅ Web search via Perplexity MCP
- ✅ File operation tools
- ✅ Replit deployment configuration

### Future Phases
- **Phase 1:** Production-grade features (memory systems, advanced auth)
- **Phase 2:** Deep research capabilities

## Architecture Notes

### Frontend-Backend Communication
- WebSocket endpoint: `ws://localhost:8000/api/v1/ws`
- AG-UI Protocol for streaming events
- Real-time tool call transparency
- Token-by-token response streaming

### State Management
- SQLite checkpointer for conversation history
- No persistent user database in Phase 0
- LangSmith for trace persistence (optional)

## Replit-Specific Configuration

### Port Bindings
- Frontend binds to `0.0.0.0:5000` for webview access
- Backend binds to `0.0.0.0:8000` for API access
- CORS automatically includes Replit preview domains

### Workflows
The `.replit` file configures parallel workflows:
- **Project** - Runs both Backend and Frontend in parallel
- **Backend** - Starts FastAPI with uvicorn (auto-reload)
- **Frontend** - Starts Next.js dev server

### Startup Scripts
- `scripts/start-replit.sh` - Development (used by Run button)
- `scripts/start-replit-prod.sh` - Production deployment

## Security Considerations
- API keys stored in Replit Secrets (never committed)
- No authentication system in Phase 0 (single-user testing)
- Rate limiting enabled (100 requests/hour per IP)
- CORS automatically configured for Replit domains

## Troubleshooting

### Backend not starting
1. Check Replit Secrets are configured correctly
2. Verify Poetry dependencies: `poetry install`
3. Check logs in console output

### Frontend not loading
1. Verify pnpm dependencies: `cd frontend && pnpm install`
2. Check if backend is running (port 8000)
3. Look for errors in webview console

### CORS errors
The backend automatically includes Replit domains in CORS. If issues persist:
1. Check `REPLIT_DEV_DOMAIN` environment variable is set
2. Verify backend logs show Replit CORS origins loaded

### WebSocket disconnects
1. Check backend is running on port 8000
2. Verify no firewall blocking WebSocket connections
3. Try refreshing the webview
