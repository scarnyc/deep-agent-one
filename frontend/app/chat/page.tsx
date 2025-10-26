/**
 * Chat Page with Error Boundary (Phase 0 - AG-UI Protocol)
 *
 * Main chat interface using native AG-UI Protocol components
 * with the Deep Agent backend.
 *
 * Features:
 * - Thread initialization on mount
 * - Custom AG-UI components (ChatInterface, ToolCallDisplay, ProgressTracker, AgentStatus)
 * - WebSocket event processing via useAGUIEventHandler
 * - Error boundary for graceful error handling
 * - Loading state during initialization
 */

'use client';

import { useAgentState } from '@/hooks/useAgentState';
import { useAGUIEventHandler } from '@/hooks/useAGUIEventHandler';
import ChatInterface from './components/ChatInterface';
import ToolCallDisplay from '@/components/ag-ui/ToolCallDisplay';
import ProgressTracker from '@/components/ag-ui/ProgressTracker';
import AgentStatus from '@/components/ag-ui/AgentStatus';
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
  const { createThread, setActiveThread, active_thread_id } = useAgentState();

  // Initialize WebSocket event handler
  useAGUIEventHandler(active_thread_id || '');

  useEffect(() => {
    // Create a new thread on page load (runs once)
    // Issue 81 fix: Fallback for crypto.randomUUID()
    const threadId =
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
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
      className="h-screen w-full p-4 bg-background"
      role="main"
      aria-label="Chat interface"
    >
      <div className="w-full h-full">
        {/* AG-UI Component Layout */}
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Left sidebar: Agent Status & Progress Tracker */}
          <div className="col-span-3 space-y-4 overflow-y-auto">
            <AgentStatus />
            <ProgressTracker />
          </div>

          {/* Center: Chat Interface */}
          <div className="col-span-6 h-full">
            <ChatInterface />
          </div>

          {/* Right sidebar: Tool Call Display */}
          <div className="col-span-3 h-full overflow-y-auto">
            <ToolCallDisplay />
          </div>
        </div>
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
