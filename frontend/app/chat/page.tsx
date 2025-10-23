/**
 * Chat Page with Error Boundary (Phase 0 - Security Hardened)
 *
 * Main chat interface using CopilotKit for AG-UI Protocol communication
 * with the Deep Agent backend.
 *
 * Features:
 * - Thread initialization on mount
 * - HITL approval actions
 * - Error boundary for graceful error handling
 * - Loading state during initialization
 */

'use client';

import { CopilotChat } from '@copilotkit/react-ui';
import { useAgentState } from '@/hooks/useAgentState';
import { useHITLActions } from './components/HITLApproval';
import { useEffect, useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

/**
 * Error fallback component for chat page errors
 */
function ChatErrorFallback({
  error,
  resetErrorBoundary,
}: {
  error: Error;
  resetErrorBoundary: () => void;
}) {
  return (
    <div className="h-screen w-full flex items-center justify-center p-4 bg-background">
      <div className="text-center max-w-md p-8 border border-border rounded-lg shadow-lg">
        <h2 className="text-xl font-bold mb-4 text-foreground">Chat Unavailable</h2>
        <p className="text-muted-foreground mb-6">
          {process.env.NODE_ENV === 'development'
            ? error.message
            : 'Unable to load the chat interface. Please try again.'}
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
 * Chat page content component (wrapped in error boundary)
 */
function ChatPageContent() {
  const [isReady, setIsReady] = useState(false);
  const { createThread, setActiveThread } = useAgentState();

  // Register HITL approval actions
  useHITLActions();

  useEffect(() => {
    // Create a new thread on page load (runs once)
    const threadId = crypto.randomUUID();
    createThread(threadId);
    setActiveThread(threadId);
    setIsReady(true);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - run once on mount

  // Show loading state until thread is initialized
  if (!isReady) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-4"></div>
          <p className="text-muted-foreground">Initializing chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="h-screen w-full flex items-center justify-center p-4 bg-background"
      role="main"
      aria-label="Chat interface"
    >
      <div className="w-full max-w-5xl h-full">
        <CopilotChat
          className="h-full rounded-2xl shadow-xl border border-border"
          labels={{
            title: 'Deep Agent',
            initial:
              "Hi! I'm Deep Agent. I can search the web, execute code, manage files, and more. How can I help you today?",
            placeholder: 'Ask me anything...',
          }}
          aria-label="Deep Agent conversation"
        />
      </div>
    </div>
  );
}

/**
 * Chat page with error boundary wrapper
 */
export default function ChatPage() {
  return (
    <ErrorBoundary FallbackComponent={ChatErrorFallback}>
      <ChatPageContent />
    </ErrorBoundary>
  );
}
