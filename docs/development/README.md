# Development Documentation

## Purpose
Developer guides, setup instructions, coding standards, and contribution guidelines.

## Contents

### Current Documentation
- [Setup Guide](setup.md) - Local development environment setup
- [Testing Guide](testing.md) - Testing strategies and guidelines
- [WebSocket Implementation](websocket.md) - WebSocket protocol and implementation
- [Debugging Guide](debugging.md) - Debugging tools and techniques

### Planned Documentation (Phase 1+)
- Code standards and style guide
- Contributing guidelines
- Environment configuration
- IDE setup (VSCode, Cursor)
- Performance optimization
- Git workflow and branching strategy

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Poetry (Python package manager)
- Git

### Setup
```bash
# Clone repository
git clone <repository-url>
cd deep-agent-agi

# Set up Python environment
poetry install
poetry shell

# Install Node.js dependencies (Playwright MCP)
npm install -g @modelcontextprotocol/server-playwright
npx playwright install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest

# Start development server
cd backend && uvicorn deep_agent.api.main:app --reload
```

See [Setup Guide](setup.md) for detailed instructions.

## Development Workflow

### 1. Environment Setup
- Create virtual environment with Poetry
- Install Node.js and Playwright MCP
- Configure environment variables (.env files)
- Never commit secrets

### 2. Development Process
- Write tests FIRST (TDD)
- Implement incrementally
- Commit constantly (every logical unit)
- Run code-review-expert and testing-expert before EVERY commit
- Run security scans (TheAuditor)

### 3. Code Quality Gates
- **Pre-commit:** Run testing-expert and code-review-expert agents
- **Testing:** 80%+ coverage required
- **Security:** TheAuditor scan must pass
- **Linting:** Ruff for Python, ESLint for TypeScript
- **Type checking:** mypy for Python, TypeScript for frontend

### 4. Commit Workflow
```bash
# After implementing feature
git add <files>
# Run agents (mandatory)
# - Run testing-expert (verify tests)
# - Run code-review-expert (verify code quality)
# After approval, commit
git commit -m "feat(phase-X): <description>"
```

See [CLAUDE.md](../../CLAUDE.md) for complete workflow details.

## Testing Strategy

### Test Types
- **Unit Tests:** Individual functions and methods
- **Integration Tests:** Component interactions
- **E2E Tests:** Complete user workflows
- **UI Tests:** Playwright MCP for browser testing
- **Security Tests:** TheAuditor for vulnerability scanning

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov

# Specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Generate reports
pytest --html=reports/test_report.html --self-contained-html
```

See [Testing Guide](testing.md) for detailed testing documentation.

## Debugging

### Tools
- Python debugger (pdb, ipdb)
- VSCode debugger
- LangSmith tracing
- FastAPI interactive docs (http://localhost:8000/docs)

### Common Issues
- WebSocket connection problems
- Agent timeout issues
- Tool execution errors
- Streaming response issues

See [Debugging Guide](debugging.md) for debugging strategies.

## Code Standards

### Python
- **Style:** PEP 8 (enforced by Ruff)
- **Docstrings:** Google-style
- **Type hints:** Required for all functions
- **Error handling:** Structured exceptions
- **Logging:** Structured logging with context

### TypeScript
- **Style:** ESLint configuration
- **Comments:** JSDoc format
- **Type safety:** Strict TypeScript
- **Components:** React functional components with hooks

### Commit Messages
Follow semantic commit format:
- `feat:` New features
- `fix:` Bug fixes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `docs:` Documentation updates
- `chore:` Dependency updates, configs
- `security:` Security enhancements

Example: `feat(phase-0): implement WebSocket streaming with AG-UI Protocol`

## Architecture Patterns

### Backend Patterns
- **Dependency Injection:** FastAPI dependencies
- **Event Streaming:** AG-UI Protocol for real-time updates
- **Error Handling:** Structured exceptions with user-friendly messages
- **State Management:** LangGraph checkpointer for agent state

### Frontend Patterns
- **Component Structure:** Atomic design principles
- **State Management:** React Context API
- **Event Handling:** AG-UI event listeners
- **Error Boundaries:** React error boundaries for graceful failures

## Tools and Scripts

### Development Scripts
- `scripts/test.sh` - Run comprehensive test suite
- `scripts/security_scan.sh` - Run TheAuditor security scan
- `scripts/lint.sh` - Run linting and formatting
- `scripts/dev.sh` - Start development servers

### Code Quality Tools
- **Ruff:** Fast Python linter and formatter
- **mypy:** Python type checking
- **pytest:** Testing framework
- **TheAuditor:** Security vulnerability scanning

## Related Documentation
- [Main README](../../README.md) - Project overview
- [CLAUDE.md](../../CLAUDE.md) - Development guide for Claude Code
- [Tests README](../../tests/README.md) - Testing documentation
- [Architecture](../architecture/) - System architecture
- [API](../api/) - API documentation

## Contributing

### Pre-Commit Checklist
- [ ] Tests written and passing (80%+ coverage)
- [ ] testing-expert agent approved tests
- [ ] code-review-expert agent approved code
- [ ] TheAuditor security scan passed
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Commit message follows convention

### Pull Request Process
1. Create feature branch from `phase-X-mvp`
2. Implement feature with tests
3. Run all code quality checks
4. Create pull request with description
5. Address review feedback
6. Merge after approval

See [Contributing Guidelines](contributing.md) (planned) for detailed process.

## Getting Help

### Resources
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AG-UI Documentation](https://docs.ag-ui.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

### Support Channels
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Project documentation for guides

## Quick Reference

### Essential Commands
```bash
# Environment setup
poetry install && poetry shell

# Run tests
pytest --cov

# Security scan
./scripts/security_scan.sh

# Code quality
ruff check .
ruff format .
mypy backend/deep_agent/

# Start servers
cd backend && uvicorn deep_agent.api.main:app --reload
cd frontend && npm run dev
```

### File Locations
- Backend: `backend/deep_agent/`
- Frontend: `frontend/`
- Tests: `tests/`
- Scripts: `scripts/`
- Docs: `docs/`
