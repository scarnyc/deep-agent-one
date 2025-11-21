/**
 * Unit Tests for Providers Component (Phase 0)
 *
 * Test Coverage:
 * - Component rendering
 * - CopilotKit configuration
 * - Error boundary functionality
 * - Error logging
 * - Environment-specific error display
 *
 * Testing Pattern: AAA (Arrange-Act-Assert)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Providers } from '../providers'

// Mock CopilotKit
jest.mock('@copilotkit/react-core', () => ({
  CopilotKit: jest.fn(({ runtimeUrl, agent, children }) => (
    <div
      data-testid="copilot-kit"
      data-runtime-url={runtimeUrl}
      data-agent={agent}
    >
      {children}
    </div>
  )),
}))

// Store original console.error for restoration
const originalConsoleError = console.error

describe('Providers', () => {
  // Restore console.error after each test
  afterEach(() => {
    console.error = originalConsoleError
    jest.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render children successfully', () => {
      // Arrange
      const testChild = <div data-testid="test-child">Test Child Content</div>

      // Act
      render(<Providers>{testChild}</Providers>)

      // Assert
      expect(screen.getByTestId('test-child')).toBeInTheDocument()
      expect(screen.getByText('Test Child Content')).toBeInTheDocument()
    })

    it('should render CopilotKit with correct runtimeUrl prop', () => {
      // Arrange
      const expectedRuntimeUrl = '/api/copilotkit'
      const testChild = <div>Test</div>

      // Act
      render(<Providers>{testChild}</Providers>)

      // Assert
      const copilotKit = screen.getByTestId('copilot-kit')
      expect(copilotKit).toHaveAttribute('data-runtime-url', expectedRuntimeUrl)
    })

    it('should render CopilotKit with correct agent prop', () => {
      // Arrange
      const expectedAgent = 'deepAgent'
      const testChild = <div>Test</div>

      // Act
      render(<Providers>{testChild}</Providers>)

      // Assert
      const copilotKit = screen.getByTestId('copilot-kit')
      expect(copilotKit).toHaveAttribute('data-agent', expectedAgent)
    })

    it('should render multiple children successfully', () => {
      // Arrange
      const children = (
        <>
          <div data-testid="child-1">First Child</div>
          <div data-testid="child-2">Second Child</div>
          <div data-testid="child-3">Third Child</div>
        </>
      )

      // Act
      render(<Providers>{children}</Providers>)

      // Assert
      expect(screen.getByTestId('child-1')).toBeInTheDocument()
      expect(screen.getByTestId('child-2')).toBeInTheDocument()
      expect(screen.getByTestId('child-3')).toBeInTheDocument()
    })
  })

  describe('Error Boundary - Error Catching', () => {
    // Component that throws error on render
    const ThrowError = ({ shouldThrow = true }: { shouldThrow?: boolean }) => {
      if (shouldThrow) {
        throw new Error('Test error from child component')
      }
      return <div>No error</div>
    }

    it('should catch and handle errors from child components', () => {
      // Arrange
      console.error = jest.fn() // Suppress error output

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })

    it('should display error message in development mode', () => {
      // Arrange
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'development'
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(screen.getByText('Test error from child component')).toBeInTheDocument()

      // Cleanup
      process.env.NODE_ENV = originalEnv
    })

    it('should hide error details in production mode', () => {
      // Arrange
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'production'
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(
        screen.getByText(/an unexpected error occurred/i)
      ).toBeInTheDocument()
      expect(
        screen.queryByText('Test error from child component')
      ).not.toBeInTheDocument()

      // Cleanup
      process.env.NODE_ENV = originalEnv
    })

    it('should call resetErrorBoundary when Try Again button is clicked', () => {
      // Arrange
      console.error = jest.fn()
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Act
      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      fireEvent.click(tryAgainButton)

      // Assert
      // After reset, error boundary attempts to re-render children
      // Since our ThrowError component still throws, we should still see the error UI
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })

  describe('Error Boundary - Error Logging', () => {
    const ThrowError = () => {
      throw new Error('Test logging error')
    }

    it('should log error to console with error message', () => {
      // Arrange
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(console.error).toHaveBeenCalled()
      const errorCall = (console.error as jest.Mock).mock.calls.find((call) =>
        typeof call[0] === 'string' && call[0].includes('[Providers] Error caught by boundary:')
      )
      expect(errorCall).toBeDefined()
    })

    it('should log error with timestamp', () => {
      // Arrange
      console.error = jest.fn()
      const beforeTime = new Date().toISOString()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(console.error).toHaveBeenCalled()
      const errorCall = (console.error as jest.Mock).mock.calls.find((call) =>
        typeof call[0] === 'string' && call[0].includes('[Providers] Error caught by boundary:')
      )
      expect(errorCall).toBeDefined()
      const errorObject = errorCall[1]
      expect(errorObject).toHaveProperty('timestamp')
      expect(typeof errorObject.timestamp).toBe('string')
      // Verify timestamp is recent (within 1 second)
      const timestamp = new Date(errorObject.timestamp)
      const now = new Date()
      expect(now.getTime() - timestamp.getTime()).toBeLessThan(1000)
    })

    it('should log componentStack when available', () => {
      // Arrange
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(console.error).toHaveBeenCalled()
      const errorCall = (console.error as jest.Mock).mock.calls.find((call) =>
        typeof call[0] === 'string' && call[0].includes('[Providers] Error caught by boundary:')
      )
      expect(errorCall).toBeDefined()
      const errorObject = errorCall[1]
      expect(errorObject).toHaveProperty('componentStack')
    })

    it('should log error stack trace', () => {
      // Arrange
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      expect(console.error).toHaveBeenCalled()
      const errorCall = (console.error as jest.Mock).mock.calls.find((call) =>
        typeof call[0] === 'string' && call[0].includes('[Providers] Error caught by boundary:')
      )
      expect(errorCall).toBeDefined()
      const errorObject = errorCall[1]
      expect(errorObject).toHaveProperty('stack')
      expect(typeof errorObject.stack).toBe('string')
    })
  })

  describe('Error Boundary - UI Elements', () => {
    const ThrowError = () => {
      throw new Error('Test UI error')
    }

    it('should render error fallback with correct heading', () => {
      // Arrange
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('Something went wrong')
    })

    it('should render Try Again button with correct styling classes', () => {
      // Arrange
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      const button = screen.getByRole('button', { name: /try again/i })
      expect(button).toHaveClass('px-6', 'py-3', 'bg-primary')
    })

    it('should render error fallback container with correct layout classes', () => {
      // Arrange
      console.error = jest.fn()

      // Act
      render(
        <Providers>
          <ThrowError />
        </Providers>
      )

      // Assert
      const heading = screen.getByText('Something went wrong')
      const outerContainer = heading.closest('.flex')
      expect(outerContainer).toHaveClass('flex', 'items-center', 'justify-center')
    })
  })

  describe('Integration Tests', () => {
    it('should wrap children with both ErrorBoundary and CopilotKit', () => {
      // Arrange
      const testChild = <div data-testid="wrapped-child">Wrapped Content</div>

      // Act
      render(<Providers>{testChild}</Providers>)

      // Assert
      const copilotKit = screen.getByTestId('copilot-kit')
      const wrappedChild = screen.getByTestId('wrapped-child')
      expect(copilotKit).toContainElement(wrappedChild)
    })

    it('should maintain CopilotKit functionality when no errors occur', () => {
      // Arrange
      const { CopilotKit } = require('@copilotkit/react-core')
      const testChild = <div>Test</div>

      // Act
      render(<Providers>{testChild}</Providers>)

      // Assert
      expect(CopilotKit).toHaveBeenCalledWith(
        expect.objectContaining({
          runtimeUrl: '/api/copilotkit',
          agent: 'deepAgent',
        }),
        expect.anything()
      )
    })
  })

  describe('Edge Cases', () => {
    it('should handle null children gracefully', () => {
      // Arrange & Act
      render(<Providers>{null}</Providers>)

      // Assert
      const copilotKit = screen.getByTestId('copilot-kit')
      expect(copilotKit).toBeInTheDocument()
    })

    it('should handle undefined children gracefully', () => {
      // Arrange & Act
      render(<Providers>{undefined}</Providers>)

      // Assert
      const copilotKit = screen.getByTestId('copilot-kit')
      expect(copilotKit).toBeInTheDocument()
    })

    it('should handle empty fragment children', () => {
      // Arrange & Act
      render(<Providers>{<></>}</Providers>)

      // Assert
      const copilotKit = screen.getByTestId('copilot-kit')
      expect(copilotKit).toBeInTheDocument()
    })

    it('should handle nested error boundaries correctly', () => {
      // Arrange
      console.error = jest.fn()
      const ThrowError = () => {
        throw new Error('Nested error')
      }

      // Act
      render(
        <Providers>
          <div>
            <ThrowError />
          </div>
        </Providers>
      )

      // Assert
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })
})
