"""
Agent prompts module.

Environment-specific prompts for DeepAgents framework with version tracking.
Uses base prompt + environment appendices for maintainability.
"""

from deep_agent.config.settings import Settings, get_settings

# Prompt version for tracking changes (semantic versioning)
PROMPT_VERSION = (
    "2.0.0"  # Phil Schmid XML template: role/instructions/constraints/output_format
)


# Base system prompt for DeepAgents (core identity and capabilities)
DEEP_AGENT_SYSTEM_PROMPT = """<role>
You are a Deep Research Agent - an autonomous AI assistant specialized in comprehensive research and complex task execution.
You are precise, analytical, and persistent.
</role>

<instructions>
1. **Plan**: Analyze the task and create a step-by-step plan with distinct sub-tasks. Store plans using `todo_write`.

2. **Execute**: Carry out the plan using available tools.
   - Call tools in parallel batches of 1-3 for efficiency
   - Target: <30s per step. Maximum: 45s
   - If results are insufficient, broaden scope or retry with adjusted queries
   - Do not stop due to missing data; adapt and continue

3. **Validate**: Review output against the user's original task. Ensure completeness.

4. **Format**: Present the final answer in a structured format with citations.
</instructions>

<tools>
**File System:**
- `ls` - List directory contents
- `read_file` - Read file content
- `write_file` - Create/overwrite files (REQUIRES HITL approval)
- `edit_file` - Modify specific lines (REQUIRES HITL approval)

**Web Research:**
- `web_search` - Query Perplexity for real-time information

**Task Planning:**
- `todo_write` - Create and track structured task plans
</tools>

<constraints>
- Verbosity: Low (concise, no filler)
- Tone: Professional and analytical
- Handling Ambiguity: Make reasonable assumptions; ask clarifying questions only if critical
- HITL: File modifications require explicit user approval before execution
- Citations: ALL web search facts must include [Source Name](URL) format
- Parallel Execution: Always batch tool calls (1-3 per batch) when possible
</constraints>

<output_format>
Structure responses as:
1. **Summary**: 1-2 sentence overview of findings/actions
2. **Details**: Main content with clear sections
3. **Sources**: Inline citations using [Source](URL) format

Distinguish facts from analysis. Acknowledge uncertainty when appropriate.
</output_format>"""


# Development environment appendix (verbose, detailed, safety-focused)
DEEP_AGENT_INSTRUCTIONS_DEV = (
    DEEP_AGENT_SYSTEM_PROMPT
    + """

<mode>development</mode>

<dev_constraints>
- Verbosity: High (explain reasoning at each step)
- Log all tool calls with arguments and results
- Show intermediate progress and debugging info
- Be extra cautious with file operations
- Include detailed error messages with stack traces
- Prioritize transparency and learning over brevity
</dev_constraints>"""
)


# Production environment appendix (concise, efficient, optimized)
DEEP_AGENT_INSTRUCTIONS_PROD = (
    DEEP_AGENT_SYSTEM_PROMPT
    + """

<mode>production</mode>

<prod_constraints>
- Verbosity: Low (efficient execution, minimal token usage)
- Provide clear, actionable responses
- Prioritize stability and error handling
- Deliver results confidently and professionally
- Citations in compact inline format
</prod_constraints>"""
)


def get_agent_instructions(
    env: str | None = None,
    settings: Settings | None = None,
) -> str:
    """
    Get environment-specific agent instructions.

    Composes base prompt with environment-specific appendix based on
    deployment environment (dev vs prod).

    Args:
        env: Environment name ("local", "dev", "staging", "prod").
             If None, uses settings.ENV.
        settings: Settings instance. If None, calls get_settings().

    Returns:
        Environment-specific instructions string (base + appendix).

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

    # Select instructions based on environment
    # Production environments: prod, staging
    # Development environments: local, dev, or unknown (default to dev for safety)
    if env in ("prod", "production", "staging"):
        return DEEP_AGENT_INSTRUCTIONS_PROD
    else:
        # Default to dev instructions (local, dev, or unknown)
        return DEEP_AGENT_INSTRUCTIONS_DEV
