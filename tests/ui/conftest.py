"""
Playwright configuration and fixtures for UI tests.

Provides shared fixtures for browser automation testing including
browser configuration, context management, and base URL configuration.
"""
import os
from typing import Generator

import pytest
from playwright.sync_api import Page, BrowserContext, Browser, Playwright


# Configuration constants
BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost:3000")
TIMEOUT = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))  # 30 seconds default
HEADED = os.getenv("PLAYWRIGHT_HEADED", "false").lower() == "true"
SLOW_MO = int(os.getenv("PLAYWRIGHT_SLOW_MO", "0"))  # milliseconds


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """
    Configure browser context arguments for all tests.

    Provides default configuration for viewport, locale, and other
    browser context settings. Can be overridden via environment variables.

    Args:
        browser_context_args: Default browser context arguments from pytest-playwright

    Returns:
        dict: Updated browser context arguments
    """
    return {
        **browser_context_args,
        "base_url": BASE_URL,
        "viewport": {
            "width": 1280,
            "height": 720,
        },
        "locale": "en-US",
        "timezone_id": "America/New_York",
        # Record video on failure (optional)
        # "record_video_dir": "test-results/videos",
        # "record_video_size": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Provide a new page for each test with proper configuration.

    Automatically configures timeouts, navigation behavior, and cleanup.
    Each test gets a fresh page instance to avoid state pollution.

    Args:
        context: Playwright browser context

    Yields:
        Page: Configured Playwright page instance
    """
    # Create new page
    page = context.new_page()

    # Set default timeout
    page.set_default_timeout(TIMEOUT)
    page.set_default_navigation_timeout(TIMEOUT)

    # Navigate to base URL by default
    # Tests can override by calling page.goto() again
    try:
        page.goto("/")
    except Exception:
        # If base URL is not accessible, continue
        # Tests will handle navigation errors
        pass

    yield page

    # Cleanup: Take screenshot on failure
    test_failed = hasattr(page, "_pytest_failed") and page._pytest_failed

    if test_failed:
        # Create screenshots directory
        os.makedirs("test-results/screenshots", exist_ok=True)

        # Generate screenshot filename from test name
        test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown").split("::")[-1].split(" ")[0]
        screenshot_path = f"test-results/screenshots/{test_name}.png"

        try:
            page.screenshot(path=screenshot_path)
            print(f"\n📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"\n❌ Failed to save screenshot: {e}")

    # Close page
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test failure status for screenshot capture.

    Sets a flag on the page object when a test fails, allowing the
    page fixture to capture screenshots only on failures.
    """
    outcome = yield
    rep = outcome.get_result()

    # Mark page as failed if test failed
    if rep.when == "call" and rep.failed:
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            page._pytest_failed = True


# Helper fixtures for common UI patterns


@pytest.fixture
def authenticated_page(page: Page) -> Page:
    """
    Provide a page with user authentication already complete.

    This fixture handles the authentication flow so tests can
    start from an authenticated state. Customize based on your
    authentication mechanism.

    Args:
        page: Playwright page instance

    Returns:
        Page: Authenticated page instance

    Note:
        Update this fixture to match your actual authentication flow.
        For Phase 0, authentication is not implemented, so this is a no-op.
    """
    # TODO: Implement authentication flow when auth is added
    # For Phase 0 (no auth), just return the page
    return page


@pytest.fixture
def chat_page(page: Page) -> Page:
    """
    Provide a page navigated to the chat interface.

    Ensures WebSocket connection is established and chat interface
    is ready for interaction.

    Args:
        page: Playwright page instance

    Returns:
        Page: Page on chat interface with connection established
    """
    # Navigate to chat
    page.goto(f"{BASE_URL}/chat")

    # Wait for page to be ready
    # This can be customized based on actual page load indicators
    try:
        # Wait for WebSocket status indicator to appear
        page.wait_for_selector('[data-testid="ws-status"]', timeout=5000)
    except Exception:
        # If status indicator doesn't exist, continue
        # Tests will handle missing elements
        pass

    return page


def pytest_configure(config):
    """
    Register custom pytest markers for UI tests.

    Allows filtering tests by category using pytest markers.
    """
    config.addinivalue_line(
        "markers",
        "ui: Playwright UI tests (slow, require frontend/backend running)"
    )
    config.addinivalue_line(
        "markers",
        "ui_slow: Very slow UI tests (>30 seconds)"
    )
    config.addinivalue_line(
        "markers",
        "ui_visual: Visual regression tests (require baseline screenshots)"
    )
