"""
Agent prompts module.

Environment-specific prompts for DeepAgents framework with version tracking.
Uses base prompt + environment appendices for maintainability.

v3.0.0 Changes:
- Pure Markdown format (no XML tags) to match LangChain middleware style
- Sequential execution guidance (langchain_google_genai wrapper limitation)
- Loop prevention: synthesize after 3-6 searches (Issue #122)
- Removed duplicate tool docs (middleware handles most tools)
- Fixed naming: write_todos (was todo_write)
- ~32% token reduction (415 → 280 tokens)
"""

from deep_agent.config.settings import Settings, get_settings

# Prompt version for tracking changes (semantic versioning)
PROMPT_VERSION = "3.0.0"  # Pure Markdown, sequential execution, loop prevention

# Sequential execution guidance (due to langchain_google_genai wrapper limitation)
# Note: Gemini natively supports parallel tool calls, but the wrapper does not
# See: https://github.com/langchain-ai/langchain-google/issues/816
SEQUENTIAL_EXECUTION_GUIDANCE = (
    "Execute tools ONE AT A TIME. Wait for each result before proceeding.")

# Base system prompt for DeepAgents (~280 tokens, 32% reduction from v2.0.0)
# Middleware already documents: write_todos, ls, read_file, write_file, edit_file,
# glob, grep, execute, task - only web_search needs documentation here
DEEP_AGENT_SYSTEM_PROMPT = """# Deep Agent

You are an autonomous deep agent that is precise, analytical, and persistent.

**Workflow:** Plan → Execute → Synthesize → Complete

## Planning

- Analyze the user's task
- Break complex tasks into subtasks using `write_todos`
- Update status as you progress

## Execution

{parallel_execution_guidance}

- Target <30s per step (max 45s)
- If results are insufficient, broaden scope or retry with adjusted queries
- Do not stop for missing data; adapt and continue

## Validate

Review output against the user's original task. Ensure completeness.

### Web Search

- Use `web_search` for real-time information
- After 3-6 searches, STOP and synthesize findings
- Do not loop indefinitely

**Citation format:** [Source Name](URL) for ALL facts.

## Output Format

1. **Summary:** 1-2 sentences
2. **Details:** Clear sections, facts distinguished from analysis
3. **Sources:** Inline citations

## Constraints

- Concise responses, no filler
- Professional tone
- Make reasonable assumptions when dealing with ambiguity
- Ask clarifying questions only if critical
- File modifications require HITL approval before execution
"""

# Development environment appendix (Markdown format)
DEEP_AGENT_DEV_APPENDIX = """

---
**Mode:** Development

**Debug Settings:**
- Explain reasoning at each step
- Log all tool calls with arguments and results
- Show intermediate progress
- Include detailed error messages
- Prioritize transparency over brevity
"""

# Production environment appendix (Markdown format)
DEEP_AGENT_PROD_APPENDIX = """

---
**Mode:** Production

**Efficiency Settings:**
- Minimize token usage while maintaining quality
- Deliver results confidently
- Use compact inline citation format
"""


def get_agent_instructions(
    env: str | None = None,
    settings: Settings | None = None,
) -> str:
    """
    Get environment-specific agent instructions.

    Composes base prompt with sequential execution guidance and
    environment-specific appendix based on deployment environment.

    Args:
        env: Environment name ("local", "dev", "staging", "prod").
             If None, uses settings.ENV.
        settings: Settings instance. If None, calls get_settings().

    Returns:
        Complete system prompt with execution guidance and environment appendix.

    Examples:
        >>> # Get instructions for production
        >>> instructions = get_agent_instructions(env="prod")

        >>> # Get instructions from settings
        >>> from deep_agent.config.settings import get_settings
        >>> settings = get_settings()
        >>> instructions = get_agent_instructions(settings=settings)

        >>> # Override settings with explicit env
        >>> instructions = get_agent_instructions(env="dev", settings=settings)
    """
    # Determine environment
    if env is None:
        if settings is None:
            settings = get_settings()
        env = settings.ENV

    # Normalize environment name (case-insensitive)
    env = env.lower().strip()

    # Format base prompt with sequential execution guidance
    # Note: Using sequential mode due to langchain_google_genai wrapper limitation
    # See: https://github.com/langchain-ai/langchain-google/issues/816
    base_prompt = DEEP_AGENT_SYSTEM_PROMPT.format(
        parallel_execution_guidance=SEQUENTIAL_EXECUTION_GUIDANCE)

    # Add environment-specific appendix
    # Production environments: prod, staging
    # Development environments: local, dev, or unknown (default to dev for safety)
    if env in ("prod", "production", "staging"):
        return base_prompt + DEEP_AGENT_PROD_APPENDIX
    else:
        # Default to dev instructions (local, dev, or unknown)
        return base_prompt + DEEP_AGENT_DEV_APPENDIX
