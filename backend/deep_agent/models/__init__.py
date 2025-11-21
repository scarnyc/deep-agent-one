"""
Models package for Deep Agent AGI.

This package contains Pydantic models for request/response validation,
configuration, and data transfer objects across the application.

Modules:
    agents: Agent management models (run tracking, HITL workflows, errors)
    chat: Chat API models (messages, requests, responses, streams)
    llm: GPT configuration models (reasoning effort, verbosity, ChatOpenAI config)

Categories:
    API Models: ChatRequest, ChatResponse, StreamEvent
    Agent Models: AgentRunInfo, HITLApprovalRequest, HITLApprovalResponse
    Error Models: ErrorResponse
    Config Models: GPTConfig, ReasoningEffort, Verbosity
    Enum Models: MessageRole, ResponseStatus, AgentRunStatus, HITLAction

Example:
    >>> from deep_agent.models import ChatRequest, ChatResponse, MessageRole
    >>> request = ChatRequest(message="Hello", thread_id="user-123")
    >>> # ... process request ...
    >>> response = ChatResponse(
    ...     messages=[{"role": MessageRole.ASSISTANT, "content": "Hi!"}],
    ...     thread_id="user-123",
    ...     status="success"
    ... )
"""
