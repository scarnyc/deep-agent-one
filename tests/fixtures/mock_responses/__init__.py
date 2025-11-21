"""
Mock API response data for testing.

This module provides pre-configured mock responses for external API calls,
allowing tests to run without making actual network requests or incurring costs.

Available Mock Data:
    - OpenAI chat completion responses
    - Perplexity web search results
    - LangSmith tracing responses
    - Tool execution results

Usage:
    Mock responses are used by fixtures in tests/conftest.py to simulate
    external service behavior without making real API calls.

    Example:
        >>> from tests.fixtures.mock_responses import MOCK_CHAT_RESPONSE
        >>> response = mock_openai_client.chat.completions.create(...)
        >>> assert response.choices[0].message.content == MOCK_CHAT_RESPONSE

Structure:
    Mock responses should follow the actual API response structure to ensure
    tests accurately reflect production behavior.

Best Practices:
    - Keep mock data minimal but realistic
    - Update mock data when APIs change
    - Use distinct mock data for different test scenarios
    - Document any deviations from actual API responses

Related:
    - tests/conftest.py: Mock service fixtures that use this data
    - OpenAI API docs: https://platform.openai.com/docs/api-reference
    - Perplexity API docs: https://docs.perplexity.ai/
"""
