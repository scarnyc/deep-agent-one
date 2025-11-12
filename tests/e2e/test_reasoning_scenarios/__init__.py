"""
Reasoning Scenario Tests for Deep Planning and Complex Problem Solving.

This module contains E2E tests that validate the system's ability to perform
deep reasoning, multi-step planning, and complex problem solving using the
LangGraph DeepAgents framework.

Purpose:
    Reasoning scenario tests verify that agents can:
    - Break down complex problems into subtasks
    - Create and execute multi-step plans
    - Adapt plans based on intermediate results
    - Coordinate multiple tools and sub-agents
    - Synthesize results from multiple sources
    - Provide clear reasoning chains

Example Scenarios:
    1. Deep Research with Synthesis
       - Complex question requiring multiple information sources
       - Agent plans research strategy (5-10 steps)
       - Agent gathers information from web, files, and APIs
       - Agent synthesizes findings with reasoning
       - Agent provides comprehensive answer with citations

    2. Multi-Step Code Generation
       - User requests complex feature implementation
       - Agent creates step-by-step plan (TodoWrite)
       - Agent generates code for each component
       - Agent runs tests and fixes issues
       - Agent refactors and optimizes

    3. Iterative Problem Solving
       - User presents problem with constraints
       - Agent proposes solution approach
       - Agent implements and tests solution
       - Agent encounters issues and adapts plan
       - Agent delivers working solution with explanation

Testing Approach:
    - Focus on reasoning quality, not just correctness
    - Verify plan creation and execution
    - Test plan adaptation when encountering errors
    - Validate reasoning transparency (visible to user)
    - Measure response quality against Phase 0 criteria

GPT-5 Variable Reasoning Effort (Phase 1):
    These tests will be extended in Phase 1 to test variable reasoning effort:
    - Simple queries: Low reasoning effort (fast, basic answers)
    - Medium queries: Medium reasoning effort (balanced speed/quality)
    - Complex queries: High reasoning effort (deep analysis, slow but thorough)
    - Trigger phrases: "think carefully", "analyze deeply", etc.

Success Criteria:
    - Plan creation: <10s for initial plan
    - Step execution: <30s per step
    - Reasoning transparency: All steps visible in UI
    - Plan adaptation: Handles 80% of errors gracefully
    - Final quality: Meets user requirements

Best Practices:
    1. Design scenarios requiring multi-step reasoning
    2. Test both successful and failed reasoning paths
    3. Verify reasoning chain is visible and logical
    4. Test plan adaptation when steps fail
    5. Validate final answers are comprehensive
    6. Measure token usage for optimization

Example:
    ```python
    def test_deep_research_with_synthesis(client):
        '''
        Test agent performs deep research and synthesizes findings.

        Scenario:
            User asks complex question requiring research across multiple
            sources, analysis, and synthesis into comprehensive answer.

        Reasoning Steps:
            1. Agent analyzes question complexity (high)
            2. Agent creates research plan (5 sources)
            3. Agent searches web for each source
            4. Agent reads and analyzes each source
            5. Agent identifies key findings
            6. Agent synthesizes findings with reasoning
            7. Agent provides answer with citations

        Success Criteria:
            - Plan includes e5 sources
            - Each source analyzed
            - Synthesis shows clear reasoning
            - Answer includes citations
            - Reasoning chain visible
        '''
        # Arrange
        complex_question = {
            "message": "Analyze the impact of AI on software development...",
            "thread_id": "reasoning-test-001",
        }

        # Act - Trigger deep reasoning
        response = client.post("/api/v1/chat", json=complex_question)

        # Assert - Verify reasoning quality
        assert response.json()["status"] == "success"
        # Verify plan was created, steps executed, synthesis provided
    ```

Placeholder:
    This directory is currently empty but will be populated with reasoning
    scenario tests in Phase 1 when variable reasoning effort is implemented.

    Planned tests:
    - Deep research with multiple sources
    - Complex code generation with planning
    - Multi-constraint problem solving
    - Iterative refinement workflows
    - Sub-agent coordination scenarios

See Also:
    - tests/e2e/test_complete_workflows/: Core workflow tests
    - tests/e2e/test_user_journeys/: Multi-step user scenarios
    - backend/deep_agent/models/llm.py: Reasoning effort configuration
    - CLAUDE.md: Phase 1 variable reasoning implementation plan
"""
