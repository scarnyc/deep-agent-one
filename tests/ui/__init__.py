"""
UI Tests Module.

This module contains Playwright-based UI tests for the Deep Agent AGI frontend.
Tests cover WebSocket connections, agent state management, HITL workflows, and
critical user paths through the application.

Test Categories:
    - WebSocket connection and reconnection logic
    - Zustand agent state management (threads, messages, tool calls)
    - HITL (Human-in-the-Loop) approval workflows
    - Streaming message updates and AG-UI Protocol events
    - Error handling and edge cases

Running UI Tests:
    # Run all UI tests
    pytest tests/ui/ -v

    # Run specific test file
    pytest tests/ui/test_websocket_connection.py -v

    # Run with markers
    pytest -m ui -v
    pytest -m ui_slow -v

    # Run in headful mode (see browser)
    PLAYWRIGHT_HEADED=true pytest tests/ui/ -v

Requirements:
    - Frontend and backend servers must be running
    - Playwright browsers must be installed (npx playwright install)
    - pytest-playwright package installed

See tests/ui/README.md for comprehensive documentation.
"""
