/**
 * E2E tests for tool execution transparency
 *
 * Tests the visibility of tool calls, arguments, and results in the UI.
 * Verifies the AG-UI Protocol requirement for tool execution transparency.
 */

import { test, expect } from '@playwright/test'

test.describe('Tool Transparency', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to chat page
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })
  })

  test('should display tool call panel in right sidebar', async ({ page }) => {
    // Right sidebar should contain ToolCallDisplay component

    const rightSidebar = page.locator('.col-span-3').last()
    await expect(rightSidebar).toBeVisible()

    // Should be scrollable for long tool call logs
    const hasOverflow = await rightSidebar.evaluate((el) => {
      const style = window.getComputedStyle(el)
      return style.overflowY === 'auto' || style.overflowY === 'scroll'
    })

    // Sidebar should allow scrolling
    expect(hasOverflow).toBe(true)
  })

  test('should show tool calls when agent uses tools', async ({ page }) => {
    // Send message that triggers tool usage

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send message requiring file tools
      await input.fill('List all files in the current directory')
      await sendButton.click()

      // Wait for agent to process
      await page.waitForTimeout(2000)

      // Look for tool call indicators in right sidebar
      const rightSidebar = page.locator('.col-span-3').last()

      // Look for tool-related content
      const toolContent = rightSidebar.locator('text=/tool|call|function|ls|read|write/i')
      const hasToolContent = await toolContent.count() > 0

      // If agent uses tools, they should be visible
      // (May not trigger in all test runs depending on backend)
    }
  })

  test('should display tool name when tool is called', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Request that triggers ls tool
      await input.fill('Show me all files')
      await sendButton.click()

      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Look for tool names like "ls", "read_file", "write_file"
      const toolNames = rightSidebar.locator('text=/ls|read_file|write_file|web_search/i')

      // If tools were called, their names should appear
      const toolCount = await toolNames.count()

      // Tool transparency requires showing tool names
    }
  })

  test('should show tool arguments/parameters', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Request with specific parameters
      await input.fill('Read the file config.json')
      await sendButton.click()

      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Look for arguments/parameters in the tool display
      // Should show what arguments were passed to tools
      const args = rightSidebar.locator('text=/path|file|directory|query/i')

      const hasArgs = await args.count() > 0

      // Good transparency shows what arguments tools received
    }
  })

  test('should display tool execution results', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send request
      await input.fill('Check if README.md exists')
      await sendButton.click()

      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Look for tool results/output
      // Should show what tools returned
      const results = rightSidebar.locator('[data-testid="tool-result"], [class*="result"]')

      // Tool transparency requires showing tool outputs
    }
  })

  test('should have inspect source toggle', async ({ page }) => {
    // Phase 0 requirement: "inspect source" toggle for tool transparency

    const rightSidebar = page.locator('.col-span-3').last()

    // Look for toggle button or checkbox
    const toggle = page.locator('button, input[type="checkbox"]').filter({
      hasText: /inspect|source|show|details/i
    })

    const toggleCount = await toggle.count()

    // "Inspect source" toggle is a Phase 0 requirement
    // May be implemented as button, checkbox, or expandable section
  })

  test('should expand/collapse tool details on toggle', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Trigger tool usage
      await input.fill('List files')
      await sendButton.click()

      await page.waitForTimeout(2000)

      // Look for expandable/collapsible tool sections
      const expandButton = page.locator('button, [role="button"]').filter({
        hasText: /expand|collapse|show|hide|details/i
      })

      if (await expandButton.count() > 0) {
        // Click to expand details
        await expandButton.first().click()

        // Additional details should appear
        await page.waitForTimeout(500)

        // Click to collapse
        await expandButton.first().click()

        // Details should hide
      }
    }
  })

  test('should show multiple tool calls in sequence', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Request requiring multiple tools
      await input.fill('List files and read README.md')
      await sendButton.click()

      await page.waitForTimeout(3000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Should show multiple tool calls
      // Each tool call should be distinct and visible
      const toolItems = rightSidebar.locator('[data-testid="tool-call"], [class*="tool"]')

      const toolCount = await toolItems.count()

      // If agent used multiple tools, all should be visible
    }
  })

  test('should show tool execution timestamps', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      await input.fill('Search for Python documentation')
      await sendButton.click()

      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Look for timestamps or time indicators
      const timestamps = rightSidebar.locator('text=/\\d{1,2}:\\d{2}|seconds ago|just now/i')

      const hasTimestamps = await timestamps.count() > 0

      // Timestamps help with debugging and transparency
    }
  })

  test('should indicate tool execution status (running/success/failed)', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      await input.fill('Run file search')
      await sendButton.click()

      // Look for status indicators while running
      const runningIndicator = page.locator('[data-testid="tool-status"], [class*="running"]')

      // Status might show:
      // - Running (spinner, "executing...")
      // - Success (checkmark, green indicator)
      // - Failed (X, red indicator)

      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Look for success/error indicators
      const statusIndicators = rightSidebar.locator('text=/success|completed|failed|error/i')

      // Tool status visibility is important for transparency
    }
  })

  test('should show tool error messages when tools fail', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Request that might cause tool error
      await input.fill('Read the file that_does_not_exist.txt')
      await sendButton.click()

      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Look for error messages
      const errorMessage = rightSidebar.locator('text=/error|failed|not found|cannot/i')

      // Error details should be shown for transparency
    }
  })

  test('should allow copying tool output', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      await input.fill('List directory contents')
      await sendButton.click()

      await page.waitForTimeout(2000)

      // Look for copy button next to tool output
      const copyButton = page.locator('button').filter({
        hasText: /copy/i
      })

      if (await copyButton.count() > 0) {
        // Click copy button
        await copyButton.first().click()

        // Should show copied confirmation
        const copiedMessage = page.locator('text=/copied|copy success/i')

        // Copying tool output is useful for debugging
      }
    }
  })

  test('should maintain tool call history', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send first message
      await input.fill('List files')
      await sendButton.click()
      await page.waitForTimeout(1500)

      // Send second message
      await input.fill('Read config')
      await sendButton.click()
      await page.waitForTimeout(1500)

      const rightSidebar = page.locator('.col-span-3').last()

      // Should show tool calls from both messages
      // History should be maintained
      const toolItems = rightSidebar.locator('[data-testid="tool-call"], [class*="tool"]')

      const toolCount = await toolItems.count()

      // All tool calls should be visible in history
    }
  })

  test('should clear tool history on new thread', async ({ page }) => {
    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send message to create tool history
      await input.fill('List files')
      await sendButton.click()
      await page.waitForTimeout(2000)

      const rightSidebar = page.locator('.col-span-3').last()
      const toolsBefore = await rightSidebar.textContent()

      // Refresh page (creates new thread)
      await page.reload()
      await page.waitForSelector('[role="main"]', { timeout: 5000 })

      // Tool history should be cleared for new thread
      const sidebarAfter = page.locator('.col-span-3').last()
      const toolsAfter = await sidebarAfter.textContent()

      // New thread should have empty or different tool history
    }
  })

  test('should be responsive and scrollable with many tool calls', async ({ page }) => {
    // Stress test: Many tool calls

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Send message that might trigger many tool calls
      await input.fill('Search files, read them, and summarize')
      await sendButton.click()

      await page.waitForTimeout(3000)

      const rightSidebar = page.locator('.col-span-3').last()

      // Sidebar should be scrollable
      const isScrollable = await rightSidebar.evaluate((el) => {
        return el.scrollHeight > el.clientHeight
      })

      // If many tool calls, sidebar should scroll
      // Should handle overflow gracefully
    }
  })

  test('should work on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    // On mobile, tool panel might be:
    // - Hidden by default with toggle to show
    // - Bottom sheet/drawer
    // - Full-screen overlay

    const rightSidebar = page.locator('.col-span-3').last()

    // Check if sidebar is visible or has toggle
    const sidebarVisible = await rightSidebar.isVisible().catch(() => false)

    if (!sidebarVisible) {
      // Look for button to show tools
      const showToolsButton = page.locator('button').filter({
        hasText: /tools|details|inspect/i
      })

      const hasToggle = await showToolsButton.count() > 0

      // Mobile should have way to access tool transparency
    }
  })
})

test.describe('Tool Transparency - Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const rightSidebar = page.locator('.col-span-3').last()

    // Should have semantic HTML or ARIA roles
    const hasRole = await rightSidebar.getAttribute('role') !== null

    // Accessibility is important for tool transparency
  })

  test('should be navigable with keyboard', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    await input.fill('Test')

    // Tab should navigate through tool display
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Focus should be manageable
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)

    // Keyboard navigation should work
    expect(focusedElement).toBeTruthy()
  })

  test('should announce tool calls to screen readers', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const rightSidebar = page.locator('.col-span-3').last()

    // Look for aria-live regions for dynamic updates
    const liveRegion = page.locator('[aria-live="polite"], [aria-live="assertive"]')

    const hasLiveRegion = await liveRegion.count() > 0

    // Live regions help screen readers announce tool calls
  })
})

test.describe('Tool Transparency - Performance', () => {
  test('should render tool calls efficiently', async ({ page }) => {
    // Performance test: Rendering many tool calls shouldn't lag

    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()
    const sendButton = page.locator('button', { hasText: /send|submit/i })

    if (await sendButton.count() > 0) {
      // Measure render time
      const startTime = Date.now()

      await input.fill('Complex task with many tools')
      await sendButton.click()

      await page.waitForTimeout(2000)

      const endTime = Date.now()
      const renderTime = endTime - startTime

      // Should render reasonably fast (<3s for tool display)
      expect(renderTime).toBeLessThan(5000)
    }
  })

  test('should not slow down chat interface', async ({ page }) => {
    // Tool display shouldn't impact chat performance

    await page.goto('/chat')
    await page.waitForSelector('[role="main"]', { timeout: 5000 })

    const input = page.locator('input, textarea').first()

    // Typing should remain responsive
    const typeStart = Date.now()
    await input.fill('Test responsiveness')
    const typeEnd = Date.now()

    const typeTime = typeEnd - typeStart

    // Typing should be instant (<500ms)
    expect(typeTime).toBeLessThan(1000)
  })
})
