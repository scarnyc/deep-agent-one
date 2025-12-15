# Changelog

All notable changes to Deep Agent One will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **BREAKING:** `context-engineering-expert` sub-agent removed
  - Prompt optimization is now handled by the main agent directly
  - Opik tools (`analyze_prompt`, `optimize_prompt`, `evaluate_prompt`, `create_evaluation_dataset`, `ab_test_prompts`) remain available
  - Migration: Use main agent for prompt engineering tasks; Opik tools can be invoked directly

### Changed
- Enhanced `code-review-expert` with systematic workflow, detailed review criteria, and code examples
- Enhanced `debugging-expert` with hypothesis-driven debugging, category-specific techniques, and proactive invocation
- Enhanced `testing-expert` with comprehensive test examples, mocking patterns, and fixtures guidance
- All sub-agents now include `Edit` tool for implementing fixes directly
- Removed GITHUB_ISSUES.md tracking from code-review-expert (LOW issues noted for future improvement instead)

## [0.2.0] - Phase 0 Public Release - 2025-11-29

### Changed
- Project renamed from "Deep Agent AGI" to "Deep Agent One"
- Repository URL updated to deep-agent-one
- Documentation refresh for public release
- License changed to Apache 2.0

## [0.1.0] - Phase 0 MVP - 2025-10-27

### Added
- **Dual-Model Architecture:** Gemini 3 Pro (primary) + GPT-5.1 (automatic fallback)
- **Opik Prompt Optimization:** 6 algorithms (Hierarchical, Bayesian, Evolutionary, MetaPrompt, GEPA, Parameter)
- Chat interface with real-time streaming (AG-UI Protocol)
- Human-in-the-loop (HITL) approval workflows
- Web search via Perplexity MCP integration
- File operations: ls, read_file, write_file, edit_file
- Planning tool with TodoWrite-based task tracking
- LangSmith integration for observability and tracing
- WebSocket-based bidirectional communication
- Reasoning effort infrastructure (stub - fixed at MEDIUM for Phase 0)
- Tool call transparency with "inspect source" toggle
- Model fallback middleware with rate limit handling
- FastAPI backend with WebSocket support
- Next.js frontend with AG-UI Protocol integration
- SQLite checkpointer for agent state persistence
- Structured logging (JSON in production, human-readable locally)
- Error tracking with trace IDs
- Cost tracking per request and model attribution

### Known Limitations
- No persistent memory between sessions
- No user authentication
- SQLite-based storage (not production-scale)
- Single-user focused
- Reasoning effort fixed at MEDIUM (dynamic routing in Phase 1)
- Opik tools available but not integrated into agent runtime

### Coming in Phase 1
- Dynamic reasoning effort routing (trigger phrases, complexity analysis)
- Memory system with PostgreSQL + pgvector
- User authentication (OAuth 2.0)
- Enhanced UI components with custom AG-UI widgets
- Opik integration into agent runtime for auto-optimization
- WebSocket reliability improvements
