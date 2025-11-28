/**
 * Chat Page - Main Chat Interface (Route: `/chat`)
 *
 * @fileoverview Main chat interface page using native AG-UI Protocol components
 * with the Deep Agent backend. This is the primary user interaction page for
 * conversing with the AI agent.
 *
 * Features:
 * - Thread initialization on mount (crypto.randomUUID with fallback)
 * - Custom AG-UI components (ChatInterface, ToolCallDisplay, ProgressTracker, AgentStatus)
 * - WebSocket event processing via useAGUIEventHandler hook
 * - Error boundary for graceful error handling
 * - Loading state during initialization
 * - 3-column responsive layout (status | chat | tools)
 *
 * @example
 * // Accessible at http://localhost:3000/chat
 * // Navigated to from home page "Start Chat" button
 *
 * @see ./components/ChatInterface.tsx - Main chat UI with message display and input
 * @see @/components/ag-ui/ToolCallDisplay.tsx - Tool execution visualization
 * @see @/components/ag-ui/ProgressTracker.tsx - Subtask progress list
 * @see @/components/ag-ui/AgentStatus.tsx - Agent state indicator (idle/running/error)
 * @see @/hooks/useAgentState.ts - Zustand store for agent state management
 * @see @/hooks/useAGUIEventHandler.ts - WebSocket event processing
 * @see {@link https://docs.ag-ui.com/sdk/python/core/overview|AG-UI Protocol Documentation}
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
 *
 * @param {Object} props - Component props
 * @param {Error} props.error - Error object caught by boundary
 * @param {Function} props.resetErrorBoundary - Function to reset error state and retry
 * @returns {JSX.Element} Error UI with retry button
 *
 * @remarks
 * - Displays error message in development mode only
 * - Production shows generic error message for security
 * - Allows user to retry by resetting error boundary
 * - Accessible error display with semantic HTML
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
 * Chat content component - renders the actual chat UI
 *
 * @param {Object} props - Component props
 * @param {string} props.threadId - Valid thread ID (guaranteed to exist in store)
 * @returns {JSX.Element} Chat interface with 3-column layout
 *
 * @remarks
 * This component is rendered ONLY after the thread is created, ensuring
 * the useAGUIEventHandler hook always receives a valid threadId.
 * This prevents the race condition where events arrive before the thread exists.
 *
 * Layout:
 * - Left (col-span-3): AgentStatus + ProgressTracker
 * - Center (col-span-6): ChatInterface (main conversation)
 * - Right (col-span-3): ToolCallDisplay (tool execution details)
 *
 * @see {@link ChatPageContent} - Parent component that manages thread initialization
 * @see {@link useAGUIEventHandler} - WebSocket event processor
 */
function ChatContent({ threadId }: { threadId: string }) {
  // Initialize WebSocket event handler with VALID threadId
  // This is guaranteed to be a real thread ID because ChatPageContent
  // only renders this component after thread creation is complete
  useAGUIEventHandler(threadId);

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
 * Chat page content component (wrapped in error boundary)
 *
 * @returns {JSX.Element} Chat interface with 3-column layout or loading spinner
 *
 * @remarks
 * Main chat page logic including:
 * - Thread creation and initialization on mount
 * - Loading state management until thread ready
 * - Delegates to ChatContent for actual UI rendering
 *
 * Thread Initialization:
 * - Uses crypto.randomUUID() if available
 * - Falls back to timestamp + random string for older browsers
 * - Creates thread in Zustand store
 * - Sets as active thread for WebSocket connection
 *
 * IMPORTANT: WebSocket event handler (useAGUIEventHandler) is NOT called here.
 * It's called in ChatContent to ensure threadId is valid when hook registers.
 * This prevents the race condition where events arrive before thread exists.
 *
 * @see {@link useAgentState} - Zustand store for thread/message management
 * @see {@link ChatContent} - Child component that registers event handler
 */
function ChatPageContent() {
  const [isReady, setIsReady] = useState(false);
  const { createThread, setActiveThread, active_thread_id } = useAgentState();

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

  // Show loading state until thread is initialized AND active_thread_id is set
  // Both conditions must be true to ensure thread exists before rendering ChatContent
  if (!isReady || !active_thread_id) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-4"></div>
          <p className="text-muted-foreground">Initializing chat...</p>
        </div>
      </div>
    );
  }

  // Render ChatContent ONLY after thread exists
  // This ensures useAGUIEventHandler receives a valid threadId
  return <ChatContent threadId={active_thread_id} />;
}

/**
 * Chat page with error boundary wrapper
 *
 * @returns {JSX.Element} ChatPageContent wrapped in ErrorBoundary
 *
 * @remarks
 * Top-level page component that wraps ChatPageContent in an error boundary
 * for graceful error handling. If any error occurs during rendering or in
 * child components, ChatErrorFallback will be displayed instead of crashing
 * the entire app.
 *
 * Error Boundary Benefits:
 * - Prevents entire app from crashing on error
 * - Shows user-friendly error message
 * - Provides retry mechanism
 * - Logs errors for debugging
 *
 * @see {@link ChatPageContent} - Main chat page implementation
 * @see {@link ChatErrorFallback} - Error UI component
 */
export default function ChatPage() {
  return (
    <ErrorBoundary FallbackComponent={ChatErrorFallback}>
      <ChatPageContent />
    </ErrorBoundary>
  );
}
