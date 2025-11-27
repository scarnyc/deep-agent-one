# Deep Agent AGI - Replit Project

## Overview
Deep Agent AGI is a Phase 0 prototype deep agent framework built on LangGraph DeepAgents with GPT-5 reasoning optimization and Google Gemini 3 Pro. This project demonstrates core framework capabilities with basic features including cost reduction through intelligent reasoning routing, human-in-the-loop workflows, real-time transparency, web search, and file operations.

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
└── tests/                # Test suites
```

## Recent Changes (Nov 27, 2025)

### Replit Environment Setup
- **Modules Installed:** Python 3.11, Node.js 20
- **Dependencies Installed:** 
  - Backend: Poetry managed Python packages (FastAPI, LangChain, etc.)
  - Frontend: pnpm managed Node.js packages (Next.js, React, AG-UI, etc.)
- **Configuration Updates:**
  - Created `.env` file with basic configuration
  - Created `frontend/.env.local` with Next.js port configuration
  - Updated `next.config.js` to support Replit's proxy/iframe preview with `allowedDevOrigins: ['*']`
- **Workflows Configured:**
  - Frontend workflow: Runs on port 5000 with hostname 0.0.0.0 for Replit webview

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

## Configuration

### Required Environment Variables
The application requires the following API keys to function:
- `OPENAI_API_KEY` - OpenAI API key for GPT-5 (fallback model)
- `GOOGLE_API_KEY` - Google API key for Gemini 3 Pro (primary model)

### Optional Environment Variables
- `PERPLEXITY_API_KEY` - For web search functionality
- `LANGSMITH_API_KEY` - For agent tracing and monitoring
- `OPIK_API_KEY` - For prompt optimization

See `.env.example` for complete configuration template.

## Running the Application

### Development Mode
The frontend is configured to run automatically via Replit workflow:
- **Frontend:** Accessible via Replit webview (port 5000)
- **Backend:** Not yet configured (requires API keys)

### Backend Setup (To Do)
1. Set up API keys in Replit Secrets or .env file:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
2. Backend will run on port 8000 (localhost)
3. Frontend proxies API requests to backend

## User Preferences

### Development Setup
- Using Python 3.11 and Node.js 20
- Poetry for Python dependency management
- pnpm for Node.js dependency management
- Frontend runs on port 5000 for Replit compatibility

## Project Goals

### Phase 0 (Current)
- ✅ Core framework with basic agent capabilities
- ✅ GPT-5 and Gemini 3 reasoning optimization
- ✅ Human-in-the-loop workflows
- ✅ Real-time streaming responses
- ✅ Web search via Perplexity MCP
- ✅ File operation tools

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

## Important Notes

### Replit-Specific Configuration
- Frontend must bind to `0.0.0.0:5000` for webview
- Backend should bind to `localhost:8000` (internal only)
- Next.js config dynamically derives `allowedDevOrigins` from REPLIT_DEV_DOMAIN and REPLIT_DOMAINS environment variables with https:// protocol
- CORS configured to allow Replit domains

### Security Considerations
- API keys stored in Replit Secrets (not committed to repo)
- No authentication system in Phase 0 (single-user testing)
- Rate limiting enabled (60 requests/minute per IP)
