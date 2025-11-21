/**
 * Jest Setup and Global Mocks (Phase 0)
 *
 * This file configures the Jest testing environment with:
 * - Jest DOM matchers for enhanced assertions
 * - Mock implementations for Next.js navigation
 * - Mock implementations for third-party libraries (react-error-boundary)
 * - Global browser API mocks (matchMedia, IntersectionObserver, etc.)
 * - Environment variable setup for tests
 *
 * This file is automatically run before each test suite via
 * setupFilesAfterEnv in jest.config.js.
 *
 * References:
 * - https://testing-library.com/docs/react-testing-library/setup
 * - https://jestjs.io/docs/configuration#setupfilesafterenv-array
 */

// Import Jest DOM matchers
import '@testing-library/jest-dom'

// Mock react-error-boundary to avoid ESM issues
jest.mock('react-error-boundary', () => {
  const React = require('react')

  return {
    ErrorBoundary: class ErrorBoundary extends React.Component {
      constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
      }

      static getDerivedStateFromError(error) {
        return { hasError: true, error }
      }

      componentDidCatch(error, errorInfo) {
        if (this.props.onError) {
          this.props.onError(error, errorInfo)
        }
      }

      render() {
        if (this.state.hasError) {
          const FallbackComponent = this.props.FallbackComponent
          return React.createElement(FallbackComponent, {
            error: this.state.error,
            resetErrorBoundary: () => {
              this.setState({ hasError: false, error: null })
            }
          })
        }
        return this.props.children
      }
    },
    withErrorBoundary: (Component, options) => Component,
    useErrorHandler: () => (error) => { throw error },
  }
})

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    }
  },
  usePathname() {
    return '/'
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  useParams() {
    return {}
  },
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_ENV = 'test'
process.env.NODE_ENV = 'test'

// Mock crypto.randomUUID for consistent test IDs
if (typeof global.crypto === 'undefined') {
  global.crypto = {
    randomUUID: () => 'test-uuid-' + Math.random().toString(36).substring(2, 15),
  }
} else if (typeof global.crypto.randomUUID === 'undefined') {
  global.crypto.randomUUID = () => 'test-uuid-' + Math.random().toString(36).substring(2, 15)
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return []
  }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock window.scrollTo
global.scrollTo = jest.fn()

// Suppress console errors during tests (optional - remove if you want to see all errors)
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
       args[0].includes('Warning: useLayoutEffect') ||
       args[0].includes('Not implemented: HTMLFormElement.prototype.submit'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})
