"""Integration tests for Pydantic models.

This package contains integration tests that validate business logic,
API contracts, and validation rules for all Pydantic models.

Test Modules:
    test_chat_integration: Chat API models (Message, ChatRequest, ChatResponse, StreamEvent)
    test_agents_integration: Agent management models (AgentRunInfo, HITL workflows, ErrorResponse)
    test_llm_integration: LLM configuration models (GPTConfig, GeminiConfig)

Test Focus:
    - Business logic validation rules
    - API contract enforcement (required fields)
    - Error handling paths
    - Edge cases (empty strings, large payloads, deep nesting)
    - Security constraints (metadata size/depth limits)
"""
