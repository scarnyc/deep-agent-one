/**
 * Client-side Providers with Error Boundary (Phase 0 - AG-UI Protocol)
 *
 * This component wraps the app with an error boundary for graceful error handling.
 * Uses native AG-UI Protocol components instead of CopilotKit.
 *
 * Provider hierarchy:
 * 1. ErrorBoundary - Catch and display errors gracefully
 * 2. WebSocketProvider - Singleton WebSocket connection for entire app
 *
 * Separated from layout.tsx to maintain server component benefits.
 */

'use client';

import { ErrorBoundary } from 'react-error-boundary';
import { WebSocketProvider } from '@/contexts/WebSocketProvider';

interface ProvidersProps {
  children: React.ReactNode;
}

/**
 * Error fallback component displayed when providers crash
 */
function ErrorFallback({
  error,
  resetErrorBoundary,
}: {
  error: Error;
  resetErrorBoundary: () => void;
}) {
  return (
    <div className="flex items-center justify-center h-screen bg-background">
      <div className="text-center max-w-md p-8 border border-border rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold mb-4 text-foreground">Something went wrong</h1>
        <p className="text-muted-foreground mb-6">
          {process.env.NODE_ENV === 'development'
            ? error.message
            : 'An unexpected error occurred. Please try reloading the page.'}
        </p>
        <button
          onClick={resetErrorBoundary}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}

/**
 * Error handler for logging errors to monitoring service
 */
function handleError(error: Error, errorInfo: { componentStack?: string | null }) {
  // Log to console (in production, send to monitoring service)
  console.error('[Providers] Error caught by boundary:', {
    error: error.message,
    stack: error.stack,
    componentStack: errorInfo.componentStack || 'No stack available',
    timestamp: new Date().toISOString(),
  });

  // TODO: In Phase 1, send to LangSmith or Sentry
  // logErrorToMonitoring(error, errorInfo);
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onError={handleError}>
      <WebSocketProvider>
        {children}
      </WebSocketProvider>
    </ErrorBoundary>
  );
}
