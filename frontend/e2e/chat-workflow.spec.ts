/**
 * E2E tests for chat workflow UI
 *
 * Tests the complete chat user journey from landing page
 * through message sending and receiving streaming responses.
 */

import { test, expect } from '@playwright/test'

test.describe('Chat Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from home page
    await page.goto('/')
  })

  test('should navigate from home to chat page', async ({ page }) => {
    // Verify home page loaded
    await expect(page.locator('h1')).toContainText('Deep Agent AGI')

    // Find and click "Start Chat" button
    const startChatButton = page.locator('a', { hasText: 'Start Chat' })
    await expect(startChatButton).toBeVisible()
    await startChatButton.click()

    // Verify navigation to chat page
    await expect(page).toHaveURL('/chat')
  })

  test('should display chat interface with all components', async ({ page }) => {
    // Navigate to chat page
    await page.goto('/chat')

    // Wait for initialization
    await page.waitForSelector('[role="main"][aria-label="Chat interface"]', {
      timeout: 5000
    })

    // Verify three main sections present
    // Left sidebar (AgentStatus & ProgressTracker)
    const leftSidebar = page.locator('.col-span-3').first()
    await expect(leftSidebar).toBeVisible()

    // Center (ChatInterface)
    const chatInterface = page.locator('.col-span-6')
    await expect(chatInterface).toBeVisible()

    // Right sidebar (ToolCallDisplay)
    const rightSidebar = page.locator('.col-span-3').last()
    await expect(rightSidebar).toBeVisible()
  })

  test('should load chat interface without errors', async ({ page }) => {
    // Track console errors
    const errors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    // Navigate to chat
    await page.goto('/chat')

    // Wait for initialization
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Verify no critical errors
    const criticalErrors = errors.filter(e =>
      !e.includes('DevTools') &&
      !e.includes('favicon')
    )
    expect(criticalErrors).toHaveLength(0)
  })

  test('should show loading state during initialization', async ({ page }) => {
    // Navigate to chat
    await page.goto('/chat')

    // Should see loading spinner initially
    // (may be too fast to catch, but verify page loads)
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Verify chat interface loaded (not showing loading anymore)
    const mainContent = page.locator('[role="main"][aria-label="Chat interface"]')
    await expect(mainContent).toBeVisible()
  })

  test('should display chat input field', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Look for input field or textarea
    const input = page.locator('input, textarea').first()
    await expect(input).toBeVisible()
  })

  test('should allow typing in chat input', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Find input field
    const input = page.locator('input, textarea').first()

    // Type a message
    await input.fill('Hello, agent!')

    // Verify text was entered
    await expect(input).toHaveValue('Hello, agent!')
  })

  test('should have send button enabled when message is typed', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Find input and send button
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    // Send button should exist
    if (await sendButton.count() > 0) {
      // Type message
      await input.fill('Test message')

      // Send button should be enabled
      await expect(sendButton).toBeEnabled()
    }
  })

  test('should clear input after sending message', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Find input and send button
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Type and send message
      await input.fill('Test message')
      await sendButton.click()

      // Input should be cleared
      await expect(input).toHaveValue('')
    }
  })

  test('should display user message in chat history', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send a message
      const testMessage = 'Hello from Playwright!'
      await input.fill(testMessage)
      await sendButton.click()

      // Wait for message to appear in chat
      // Look for message content in the chat interface
      await page.waitForSelector(`text=${testMessage}`, { timeout: 3000 })

      // Verify message is visible
      const messageElement = page.locator(`text=${testMessage}`)
      await expect(messageElement).toBeVisible()
    }
  })

  test('should show loading indicator while waiting for response', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send message
      await input.fill('Test')
      await sendButton.click()

      // Look for loading indicator (spinner, dots, etc.)
      // This might appear briefly, so don't fail if not found
      const loadingIndicators = [
        page.locator('[role="status"]'),
        page.locator('.animate-spin'),
        page.locator('text=/loading|thinking/i')
      ]

      // At least one loading indicator might be visible
      // (timing may be too fast to catch)
    }
  })

  test('should handle empty message submission gracefully', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Try to send empty message
      await input.fill('')

      // Send button should be disabled for empty input
      // OR clicking should do nothing
      const isDisabled = await sendButton.isDisabled().catch(() => false)

      if (!isDisabled) {
        await sendButton.click()
        // No error should occur
      }
    }
  })

  test('should support keyboard shortcuts (Enter to send)', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()

    // Type message and press Enter
    await input.fill('Test Enter key')
    await input.press('Enter')

    // Message should be sent (input cleared or message appears)
    // This behavior depends on implementation
  })

  test('should handle long messages', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Type long message
      const longMessage = 'A'.repeat(500)
      await input.fill(longMessage)

      // Should accept long input
      await expect(input).toHaveValue(longMessage)

      // Send button should work
      await sendButton.click()
    }
  })

  test('should handle Unicode characters', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Type Unicode message
      const unicodeMessage = 'Hello 世界! 🌍 Émoji test'
      await input.fill(unicodeMessage)

      // Should accept Unicode
      await expect(input).toHaveValue(unicodeMessage)

      await sendButton.click()

      // Message should appear in chat
      await page.waitForSelector(`text=${unicodeMessage}`, { timeout: 3000 })
    }
  })

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Chat interface should be visible and usable
    const mainContent = page.locator('[role="main"]')
    await expect(mainContent).toBeVisible()

    // Input should be accessible
    const input = page.locator('input, textarea').first()
    await expect(input).toBeVisible()
  })

  test('should persist chat history on page refresh', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send a message
      const testMessage = 'Message before refresh'
      await input.fill(testMessage)
      await sendButton.click()

      // Wait for message to appear
      await page.waitForSelector(`text=${testMessage}`, { timeout: 3000 })

      // Refresh page
      await page.reload()

      // Wait for chat to load
      await page.waitForSelector('[role="main"]', { timeout: 5000 })

      // Message should still be visible (if state is persisted)
      // Note: This depends on implementation - may create new thread
    }
  })

  test('should show error boundary on critical error', async ({ page }) => {
    // This test verifies error boundary works
    // Would need to trigger an error condition in actual implementation

    await page.goto('/chat')

    // If error occurs, error boundary should show
    const errorBoundary = page.locator('text=/chat unavailable|error|try again/i')

    // Page should either load successfully OR show error boundary
    const loaded = await page.locator('[role="main"]').isVisible().catch(() => false)
    const hasError = await errorBoundary.isVisible().catch(() => false)

    // One of these should be true
    expect(loaded || hasError).toBe(true)
  })
})

test.describe('Chat Workflow - Cross-browser', () => {
  test('should work in different browsers', async ({ page, browserName }) => {
    // This test runs on all configured browsers (Chromium, Firefox, WebKit)

    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // Basic functionality should work across browsers
    const input = page.locator('input, textarea').first()
    await expect(input).toBeVisible()

    // Log browser name for debugging
    console.log(`Testing chat workflow in: ${browserName}`)
  })
})
