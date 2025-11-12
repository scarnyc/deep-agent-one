# UI Tests Directory

Comprehensive browser automation and UI testing for Deep Agent AGI frontend using Playwright.

## Purpose

This directory contains Playwright-based UI tests that verify the frontend application's behavior from a user's perspective. Tests cover:

- **Browser Automation**: Automated interaction with the web UI across multiple browsers
- **Visual Regression**: Detection of unintended visual changes
- **Accessibility**: WCAG compliance and screen reader compatibility
- **Critical User Paths**: Core workflows like chat, HITL approval, and tool usage
- **WebSocket Integration**: Real-time communication between frontend and backend
- **State Management**: Zustand store behavior for threads, messages, and agent state

## Playwright MCP Integration

### What is Playwright MCP?

Playwright MCP (Model Context Protocol) is a server that provides automated browser testing capabilities. It allows agents and automated tests to interact with web applications just like a human user would.

### Setup

**Prerequisites:**
```bash
# Node.js 18+ required
node --version  # Must be 18+

# Install Playwright MCP globally
npm install -g @modelcontextprotocol/server-playwright

# Install Playwright browsers
npx playwright install
npx playwright install-deps  # System dependencies
```

**Verify Installation:**
```bash
npx playwright --version
```

### Configuration

Playwright MCP is configured via `.mcp/playwright.json` (if using MCP server) and `frontend/playwright.config.ts` for the test runner.

**Key Configuration Options:**
- **Base URL**: `http://localhost:3000` (development server)
- **Timeout**: 30 seconds per test
- **Browsers**: Chromium, Firefox, WebKit (Safari), Mobile Chrome, Mobile Safari
- **Headless Mode**: Controlled via `PLAYWRIGHT_HEADED` environment variable
- **Screenshots**: Captured on test failure
- **Videos**: Recorded only on failure
- **Traces**: Collected on retry for debugging

## Directory Structure

```
tests/ui/
├── __init__.py                      # Module docstring and overview
├── conftest.py                      # Playwright fixtures and configuration
├── test_agent_state.py              # Zustand agent state management tests
├── test_websocket_connection.py     # WebSocket connection and event handling tests
└── README.md                        # This file
```

## Running UI Tests

### Basic Commands

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run specific test file
pytest tests/ui/test_websocket_connection.py -v
pytest tests/ui/test_agent_state.py -v

# Run specific test method
pytest tests/ui/test_websocket_connection.py::TestWebSocketConnection::test_websocket_connects_to_backend -v
```

### Using Markers

```bash
# Run only UI tests (excludes unit/integration tests)
pytest -m ui -v

# Run slow UI tests only
pytest -m ui_slow -v

# Run visual regression tests
pytest -m ui_visual -v
```

### Environment Variables

```bash
# Run in headed mode (see browser UI)
PLAYWRIGHT_HEADED=true pytest tests/ui/ -v

# Use different base URL
PLAYWRIGHT_BASE_URL=http://localhost:8080 pytest tests/ui/ -v

# Increase timeout (milliseconds)
PLAYWRIGHT_TIMEOUT=60000 pytest tests/ui/ -v

# Enable slow motion (milliseconds between actions)
PLAYWRIGHT_SLOW_MO=500 pytest tests/ui/ -v
```

### Prerequisites

**Backend and Frontend Must Be Running:**

```bash
# Terminal 1: Start backend
cd backend
poetry run uvicorn deep_agent.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run UI tests
pytest tests/ui/ -v
```

**Without running servers, tests will fail with connection errors.**

## Writing UI Tests

### Page Object Pattern

UI tests follow the **Page Object Pattern** to separate test logic from page structure.

**Example:**
```python
from playwright.sync_api import Page, expect

def test_user_sends_message(page: Page) -> None:
    """Test user can send a chat message."""
    # Arrange: Navigate to chat
    page.goto("http://localhost:3000/chat")

    # Wait for WebSocket connection
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Act: Send message
    message_input = page.locator('[data-testid="message-input"]')
    message_input.fill("Hello, agent!")

    send_button = page.locator('[data-testid="send-button"]')
    send_button.click()

    # Assert: Message appears in chat history
    chat_history = page.locator('[data-testid="chat-history"]')
    expect(chat_history).to_contain_text("Hello, agent!", timeout=3000)
```

### Selectors

**Use `data-testid` attributes for stable selectors:**

```html
<!-- Good: Stable, semantic -->
<button data-testid="send-button">Send</button>

<!-- Bad: Fragile, implementation-dependent -->
<button class="btn-primary submit-btn">Send</button>
```

**Selector Priority:**
1. **data-testid**: Best for tests (semantic, stable)
2. **ARIA roles**: Good for accessibility and tests
3. **Text content**: Acceptable for unique text
4. **CSS selectors**: Avoid (fragile, coupled to styling)

### Waits and Assertions

**Always use explicit waits:**

```python
# Good: Explicit wait with timeout
expect(page.locator('[data-testid="message"]')).to_be_visible(timeout=5000)

# Bad: Implicit wait (timing-dependent)
time.sleep(2)
assert page.locator('[data-testid="message"]').is_visible()
```

**Common Assertions:**
```python
# Visibility
expect(element).to_be_visible()
expect(element).to_be_hidden()

# Text content
expect(element).to_have_text("Expected text")
expect(element).to_contain_text("Partial text")

# Attributes
expect(element).to_have_attribute("data-status", "connected")

# State
expect(element).to_be_enabled()
expect(element).to_be_disabled()
expect(element).to_be_checked()

# Count
expect(page.locator('[data-testid="message"]')).to_have_count(5)
```

### Isolated Tests

**Each test should be independent:**

```python
# Good: Test creates its own data
def test_user_message(page: Page) -> None:
    page.goto("/chat")
    page.fill('[data-testid="message-input"]', "Test message")
    page.click('[data-testid="send-button"]')
    # Assertions...

# Bad: Test depends on previous test state
def test_view_message(page: Page) -> None:
    # Assumes message from previous test exists
    expect(page.locator('[data-testid="message"]')).to_be_visible()
```

**Use fixtures for shared setup:**

```python
@pytest.fixture
def authenticated_user(page: Page) -> Page:
    """Provide a page with authenticated user."""
    page.goto("/login")
    page.fill('[data-testid="username"]', "testuser")
    page.fill('[data-testid="password"]', "testpass")
    page.click('[data-testid="login-button"]')
    expect(page.locator('[data-testid="user-menu"]')).to_be_visible()
    return page

def test_user_can_chat(authenticated_user: Page) -> None:
    """Test authenticated user can send messages."""
    authenticated_user.goto("/chat")
    # Test logic...
```

## UI Test Scenarios

### WebSocket Connection Tests

**File:** `test_websocket_connection.py`

Tests the `useWebSocket` React hook that manages WebSocket connections to the backend AG-UI Protocol endpoint.

**Scenarios:**
- Initial connection establishment
- Message sending and receiving
- AG-UI Protocol event handling
- Disconnection and reconnection logic
- Exponential backoff reconnection strategy
- Invalid JSON error handling
- Required field validation
- Connection status tracking across all states
- Multiple thread ID handling
- Cleanup on component unmount

**Example:**
```python
def test_websocket_connects_to_backend(page: Page) -> None:
    """Test WebSocket successfully connects to backend /ws endpoint."""
    page.goto("http://localhost:3000/chat")

    # Verify connection established
    connection_status = page.locator('[data-testid="ws-status"]')
    expect(connection_status).to_have_text("connected", timeout=5000)
```

### Agent State Management Tests

**File:** `test_agent_state.py`

Tests the `useAgentState` Zustand store that manages conversation threads, messages, tool calls, HITL state, and agent status.

**Scenarios:**
- Thread creation and management
- User message addition to threads
- Assistant message updates via streaming events
- Tool call tracking with status
- Agent status transitions (idle → running → completed)
- HITL approval request state
- Multiple thread isolation
- Thread clearing and switching
- State persistence across page refresh (Phase 1 feature)

**Example:**
```python
def test_track_tool_calls_in_state(page: Page) -> None:
    """Test tool calls are tracked in agent state."""
    page.goto("http://localhost:3000/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Send message that triggers tool usage
    page.fill('[data-testid="message-input"]', "Search for Python tutorials")
    page.click('[data-testid="send-button"]')

    # Verify tool call appears
    tool_call = page.locator('[data-testid="tool-call"]').first
    expect(tool_call).to_be_visible(timeout=10000)
    expect(tool_call).to_have_attribute("data-tool-name", re.compile(r"web_search|search"))
    expect(tool_call).to_have_attribute("data-status", re.compile(r"pending|running|completed"))
```

### Chat Interface Tests

**Scenarios (to be implemented):**
- Message input and submission
- Streaming message display
- Message history scrolling
- Error message display
- Loading states
- Empty state handling

### HITL Approval UI Tests

**Scenarios (to be implemented):**
- Approval dialog appearance
- Accept/reject/edit actions
- Agent pause during approval
- Resume after approval
- Timeout handling

### Streaming Updates Tests

**Scenarios (to be implemented):**
- Real-time message streaming
- Tool call progress updates
- Agent status changes
- Partial message rendering
- Streaming error recovery

### Error Display Tests

**Scenarios (to be implemented):**
- Connection error messages
- API error messages
- Validation error display
- Error recovery actions
- User-friendly error formatting

## Playwright Configuration

### Browser Configuration

**Supported Browsers:**
- **Chromium**: Desktop Chrome (default)
- **Firefox**: Desktop Firefox
- **WebKit**: Desktop Safari
- **Mobile Chrome**: Pixel 5 viewport
- **Mobile Safari**: iPhone 12 viewport

**Run specific browser:**
```bash
pytest tests/ui/ --browser chromium -v
pytest tests/ui/ --browser firefox -v
pytest tests/ui/ --browser webkit -v
```

### Headless Mode

**Default:** Headless (no visible browser)

**Run headed (see browser UI):**
```bash
PLAYWRIGHT_HEADED=true pytest tests/ui/ -v
```

**Use Cases for Headed Mode:**
- Debugging test failures
- Developing new tests
- Demonstrating test execution
- Visual verification

### Timeouts

**Timeout Hierarchy:**
1. **Test Timeout**: 30 seconds (entire test)
2. **Action Timeout**: 10 seconds (single action like click)
3. **Navigation Timeout**: 15 seconds (page navigation)
4. **Expect Timeout**: Varies by assertion (typically 5 seconds)

**Override Timeouts:**
```python
# Per-action timeout
page.click('[data-testid="button"]', timeout=5000)

# Per-expectation timeout
expect(element).to_be_visible(timeout=10000)

# Global timeout override
page.set_default_timeout(60000)  # 60 seconds
```

## Screenshots and Videos

### Automatic Capture

**Screenshots:**
- Captured automatically on test failure
- Saved to `test-results/screenshots/`
- Named after test function

**Videos:**
- Recorded only on test failure
- Saved to `test-results/videos/`
- Full test execution recorded

**Traces:**
- Collected on first retry attempt
- Full network, DOM, and console logs
- View with `playwright show-trace trace.zip`

### Manual Screenshots

```python
def test_example(page: Page) -> None:
    page.goto("/chat")

    # Take screenshot at specific point
    page.screenshot(path="test-results/screenshots/custom-screenshot.png")

    # Full page screenshot (scrolls to capture all)
    page.screenshot(path="test-results/screenshots/full-page.png", full_page=True)

    # Element screenshot
    element = page.locator('[data-testid="chat-history"]')
    element.screenshot(path="test-results/screenshots/chat-history.png")
```

### Debugging with Screenshots

```bash
# Run test and capture screenshots on failure
pytest tests/ui/test_websocket_connection.py::test_websocket_connects_to_backend -v

# If test fails, check:
ls test-results/screenshots/
```

## Accessibility Testing

### WCAG Guidelines

Tests verify compliance with **Web Content Accessibility Guidelines (WCAG) 2.1 Level AA**.

**Key Areas:**
1. **Keyboard Navigation**: All interactive elements accessible via keyboard
2. **Screen Reader Support**: Proper ARIA labels and roles
3. **Color Contrast**: Text readable with sufficient contrast
4. **Focus Management**: Clear focus indicators
5. **Error Identification**: Errors announced to screen readers

### Accessibility Tests

```python
def test_keyboard_navigation(page: Page) -> None:
    """Test chat interface is keyboard-accessible."""
    page.goto("/chat")

    # Focus message input via Tab key
    page.keyboard.press("Tab")
    expect(page.locator('[data-testid="message-input"]')).to_be_focused()

    # Type message
    page.keyboard.type("Hello")

    # Submit via Enter
    page.keyboard.press("Enter")

    # Verify message sent
    expect(page.locator('[data-testid="chat-history"]')).to_contain_text("Hello")

def test_aria_labels(page: Page) -> None:
    """Test ARIA labels present for screen readers."""
    page.goto("/chat")

    # Verify ARIA labels
    message_input = page.locator('[data-testid="message-input"]')
    expect(message_input).to_have_attribute("aria-label", re.compile(r"message|chat"))

    send_button = page.locator('[data-testid="send-button"]')
    expect(send_button).to_have_attribute("aria-label", re.compile(r"send|submit"))
```

### Automated Accessibility Scanning

**Using axe-core (to be integrated):**
```python
# Install: npm install --save-dev axe-playwright

from axe_playwright import Axe

def test_accessibility_compliance(page: Page) -> None:
    """Test page meets WCAG 2.1 Level AA."""
    page.goto("/chat")

    # Run accessibility scan
    axe = Axe(page)
    results = axe.analyze()

    # Assert no violations
    assert len(results.violations) == 0, f"Accessibility violations: {results.violations}"
```

## Dependencies

### Python Packages

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-playwright = "^0.4.0"
playwright = "^1.40.0"
```

### Node.js Packages

```json
{
  "devDependencies": {
    "@modelcontextprotocol/server-playwright": "^0.1.0",
    "@playwright/test": "^1.40.0"
  }
}
```

### Installation

```bash
# Install Python dependencies
poetry install

# Install Node.js dependencies
npm install

# Install Playwright browsers
npx playwright install
```

## Related Documentation

### Official Documentation

- **Playwright Docs**: https://playwright.dev/python/docs/intro
- **Playwright Best Practices**: https://playwright.dev/python/docs/best-practices
- **pytest-playwright**: https://github.com/microsoft/playwright-pytest
- **AG-UI Protocol**: https://docs.ag-ui.com/sdk/python/core/overview
- **Playwright MCP**: https://github.com/modelcontextprotocol/servers/tree/main/src/playwright

### Internal Documentation

- **Project Setup**: `/docs/development/setup.md`
- **Testing Guide**: `/docs/development/testing.md`
- **API Endpoints**: `/docs/api/endpoints.md`
- **Development Guide**: `CLAUDE.md`
- **Integration Tests**: `tests/integration/README.md`
- **E2E Tests**: `tests/e2e/README.md`

## Best Practices

### 1. Use Stable Selectors

**Good:**
```python
page.locator('[data-testid="send-button"]')
page.locator('role=button[name="Send"]')
```

**Bad:**
```python
page.locator('.btn-primary.submit')  # Fragile (CSS classes)
page.locator('xpath=//button[1]')    # Fragile (structure-dependent)
```

### 2. Explicit Waits

**Good:**
```python
expect(page.locator('[data-testid="message"]')).to_be_visible(timeout=5000)
page.wait_for_selector('[data-testid="loading"]', state="hidden", timeout=10000)
```

**Bad:**
```python
time.sleep(2)  # Flaky (timing-dependent)
```

### 3. Isolated Tests

**Good:**
```python
def test_send_message(page: Page) -> None:
    # Create own data
    page.goto("/chat")
    page.fill('[data-testid="message-input"]', "Test message")
    page.click('[data-testid="send-button"]')
    expect(page.locator('[data-testid="chat-history"]')).to_contain_text("Test message")
```

**Bad:**
```python
def test_view_message(page: Page) -> None:
    # Depends on previous test
    expect(page.locator('[data-testid="chat-history"]')).to_contain_text("Test message")
```

### 4. Meaningful Test Names

**Good:**
```python
def test_user_can_send_message_and_receive_assistant_response(page: Page) -> None:
    """Test complete chat flow with assistant response."""
    pass
```

**Bad:**
```python
def test_chat(page: Page) -> None:
    """Test chat."""
    pass
```

### 5. AAA Pattern

**Arrange-Act-Assert:**
```python
def test_send_message(page: Page) -> None:
    """Test user can send a chat message."""
    # Arrange: Set up test state
    page.goto("/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Act: Perform action
    page.fill('[data-testid="message-input"]', "Hello")
    page.click('[data-testid="send-button"]')

    # Assert: Verify outcome
    expect(page.locator('[data-testid="chat-history"]')).to_contain_text("Hello", timeout=3000)
```

### 6. Use Fixtures for Shared Setup

**Good:**
```python
@pytest.fixture
def chat_page(page: Page) -> Page:
    """Provide page navigated to chat with connection established."""
    page.goto("/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)
    return page

def test_send_message(chat_page: Page) -> None:
    """Test sending message on connected chat page."""
    chat_page.fill('[data-testid="message-input"]', "Hello")
    chat_page.click('[data-testid="send-button"]')
    expect(chat_page.locator('[data-testid="chat-history"]')).to_contain_text("Hello")
```

**Bad:**
```python
def test_send_message(page: Page) -> None:
    # Duplicate setup in every test
    page.goto("/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)
    # Test logic...

def test_receive_response(page: Page) -> None:
    # Duplicate setup again
    page.goto("/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)
    # Test logic...
```

### 7. Test Error Paths

**Don't just test happy paths:**
```python
def test_websocket_reconnects_after_disconnect(page: Page) -> None:
    """Test WebSocket reconnects when network restored."""
    page.goto("/chat")
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=5000)

    # Simulate disconnect
    page.context.set_offline(True)
    expect(page.locator('[data-testid="ws-status"]')).not_to_have_text("connected", timeout=3000)

    # Restore network
    page.context.set_offline(False)
    expect(page.locator('[data-testid="ws-status"]')).to_have_text("connected", timeout=10000)
```

### 8. Clean Up After Tests

**Use fixtures for cleanup:**
```python
@pytest.fixture
def page_with_cleanup(page: Page) -> Generator[Page, None, None]:
    """Provide page with automatic cleanup."""
    yield page

    # Cleanup: Clear local storage
    page.evaluate("localStorage.clear()")
    page.evaluate("sessionStorage.clear()")
```

### 9. Mock External Dependencies

**For tests that don't require real backend:**
```python
def test_loading_state_display(page: Page) -> None:
    """Test loading indicator appears while waiting for response."""
    page.goto("/chat")

    # Mock slow backend response
    page.route("**/api/v1/ws", lambda route: time.sleep(2))

    page.fill('[data-testid="message-input"]', "Hello")
    page.click('[data-testid="send-button"]')

    # Verify loading state
    expect(page.locator('[data-testid="loading"]')).to_be_visible()
```

### 10. Document Test Scenarios

**Use comprehensive docstrings:**
```python
def test_hitl_approval_workflow(page: Page) -> None:
    """
    Test complete HITL approval workflow.

    UI Element: HITL approval dialog with accept/reject buttons
    User Action: Send message requiring approval, then approve
    Expected Behavior: Agent pauses, shows approval UI, resumes after accept

    Args:
        page: Playwright page fixture

    Verifies:
        - HITL dialog appears for destructive actions
        - Agent status shows "waiting for approval"
        - Accept button resumes agent execution
        - Reject button cancels operation
        - Edit allows user to modify action before approving
    """
    # Test implementation...
```

---

## Troubleshooting

### Common Issues

**1. Tests fail with "Target page, context or browser has been closed"**

**Cause:** Page closed prematurely or browser crashed.

**Solution:**
```bash
# Run in headed mode to debug
PLAYWRIGHT_HEADED=true pytest tests/ui/ -v

# Check browser console logs
page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
```

**2. Element not found errors**

**Cause:** Selector incorrect or element not rendered yet.

**Solution:**
```python
# Add explicit wait
expect(page.locator('[data-testid="element"]')).to_be_visible(timeout=10000)

# Debug selector
print(page.content())  # Print HTML to verify element exists
```

**3. Timeout errors**

**Cause:** Operation takes longer than expected.

**Solution:**
```python
# Increase timeout
expect(element).to_be_visible(timeout=30000)  # 30 seconds

# Or globally
page.set_default_timeout(60000)
```

**4. WebSocket connection failures**

**Cause:** Backend not running or port mismatch.

**Solution:**
```bash
# Verify backend running
curl http://localhost:8000/api/v1/health

# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/api/v1/ws
```

### Debug Commands

```bash
# Run single test with full output
pytest tests/ui/test_websocket_connection.py::test_websocket_connects_to_backend -vv -s

# Run in headed mode with slow motion
PLAYWRIGHT_HEADED=true PLAYWRIGHT_SLOW_MO=1000 pytest tests/ui/ -v

# Generate HTML report
pytest tests/ui/ --html=test-results/ui-report.html --self-contained-html

# View trace
playwright show-trace test-results/trace.zip
```

---

**Last Updated:** 2025-11-12

**Maintained By:** Deep Agent AGI Development Team

**Questions?** See `CLAUDE.md` for development guidelines or `docs/development/testing.md` for testing strategy.
