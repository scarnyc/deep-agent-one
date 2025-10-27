# Development Setup Guide

This guide will help you set up the Deep Agent AGI development environment on your local machine.

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **Poetry** - Python dependency management
- **Git** - Version control

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10 or higher

# Check Node.js version
node --version  # Should be 18 or higher
npm --version

# Check Git
git --version
```

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/deep-agent-agi.git
cd deep-agent-agi
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install Python dependencies
poetry install
```

### 3. Set Up Node.js Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Install Playwright browsers (for UI testing)
npx playwright install
npx playwright install-deps

# Return to project root
cd ..
```

### 4. Install MCP Servers

#### Playwright MCP (UI Testing)

```bash
# Install globally
npm install -g @modelcontextprotocol/server-playwright

# Verify installation
npx playwright --version
```

#### context7 MCP (Documentation)

context7 is built into Claude Code - no installation required.

---

## Configuration

### 1. Environment Variables

Create environment-specific `.env` files:

```bash
# Copy example files
cp .env.example .env.development
cp .env.example .env.test
cp .env.example .env.production
```

### 2. Configure `.env.development`

Edit `.env.development` with your API keys:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o  # or gpt-4o-mini for testing
DEFAULT_REASONING_EFFORT=medium

# LangSmith Configuration (Optional - for tracing)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=deep-agent-agi-dev
LANGSMITH_TRACING_ENABLED=true

# Perplexity MCP (Optional - for web search)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Application Configuration
ENV=development
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration (for Phase 1+)
DATABASE_URL=sqlite:///./deep_agent.db

# Security
SECRET_KEY=your_secret_key_here_generate_with_openssl
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Generate Secret Key

```bash
# Generate a secure secret key
openssl rand -hex 32
```

Copy the output and set it as `SECRET_KEY` in your `.env` file.

---

## Running the Development Servers

### Backend (FastAPI)

```bash
# Activate virtual environment
source venv/bin/activate

# Run FastAPI server
ENV=development python -m backend.deep_agent.main

# Or use uvicorn directly
uvicorn backend.deep_agent.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc

### Frontend (Next.js)

In a new terminal:

```bash
# Navigate to frontend
cd frontend

# Run development server
npm run dev
```

The frontend will be available at:
- **App:** http://localhost:3000
- **Chat:** http://localhost:3000/chat

---

## Verifying the Setup

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.1.0"}
```

### 2. Test API Endpoint

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me?",
    "thread_id": "test-thread-001"
  }'
```

### 3. Open Frontend

Navigate to http://localhost:3000/chat and verify:
- Chat interface loads
- WebSocket status shows "Connected"
- You can send messages

---

## Common Issues & Troubleshooting

### Issue: `ImportError: No module named 'backend'`

**Solution:** Ensure you're in the project root and the virtual environment is activated:

```bash
cd /path/to/deep-agent-agi
source venv/bin/activate
```

### Issue: `OpenAI API key not found`

**Solution:** Verify your `.env.development` file:

```bash
# Check if file exists
ls -la .env.development

# Verify it's loaded
ENV=development python -c "from backend.deep_agent.config.settings import get_settings; print(get_settings().openai_api_key)"
```

### Issue: Frontend can't connect to backend

**Solution:** Check CORS settings in `.env.development`:

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

And verify backend is running on port 8000:

```bash
curl http://localhost:8000/health
```

### Issue: Playwright tests fail with "Browser not found"

**Solution:** Install Playwright browsers:

```bash
npx playwright install
npx playwright install-deps  # System dependencies
```

### Issue: `ModuleNotFoundError: No module named 'langchain_openai'`

**Solution:** Reinstall dependencies:

```bash
poetry install --no-cache
```

### Issue: Port 8000 already in use

**Solution:** Kill the process using port 8000:

```bash
# On macOS/Linux
lsof -ti:8000 | xargs kill -9

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## IDE Setup (Optional)

### VS Code

Recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss"
  ]
}
```

### PyCharm

1. Open project in PyCharm
2. Go to **Settings → Project → Python Interpreter**
3. Select the virtual environment: `./venv/bin/python`
4. Enable **Ruff** for linting in **Settings → Tools → Ruff**

---

## Next Steps

Once your development environment is set up:

1. **Run Tests:** See [Testing Guide](testing.md)
2. **Explore API:** See [API Documentation](../api/endpoints.md)
3. **Start Developing:** Follow the TDD workflow in CLAUDE.md
4. **Review Architecture:** See README.md for system architecture

---

## Additional Resources

- **CLAUDE.md** - Complete development guide with Phase 0 requirements
- **README.md** - Project overview and architecture
- **API Documentation** - `docs/api/endpoints.md`
- **Testing Guide** - `docs/development/testing.md`

---

## Need Help?

- Check **CLAUDE.md** for detailed development instructions
- Review **GITHUB_ISSUES.md** for known issues
- Open an issue on GitHub for bugs or feature requests
