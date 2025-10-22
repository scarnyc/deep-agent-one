/**
 * Chat Page
 *
 * Main chat interface using CopilotKit for AG-UI Protocol communication
 * with the Deep Agent backend.
 */

'use client';

import { CopilotSidebar } from '@copilotkit/react-ui';
import { useAgentState } from '@/hooks/useAgentState';
import { useEffect } from 'react';

export default function ChatPage() {
  const { createThread, setActiveThread } = useAgentState();

  useEffect(() => {
    // Create a new thread on page load
    const threadId = crypto.randomUUID();
    createThread(threadId);
    setActiveThread(threadId);
  }, [createThread, setActiveThread]);

  return (
    <div className="h-screen w-full flex">
      {/* Main content area */}
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Deep Agent AGI</h1>
          <p className="text-muted-foreground text-lg">
            Ask me anything. I can search the web, analyze code, and help with your tasks.
          </p>
          <div className="flex gap-2 justify-center flex-wrap max-w-2xl mx-auto">
            <span className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm">
              Web Search
            </span>
            <span className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm">
              Code Execution
            </span>
            <span className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm">
              File Operations
            </span>
            <span className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm">
              HITL Approval
            </span>
          </div>
        </div>
      </div>

      {/* CopilotKit Sidebar - handles chat UI automatically */}
      <CopilotSidebar
        defaultOpen={true}
        labels={{
          title: 'Deep Agent',
          initial: 'How can I help you today?',
        }}
      />
    </div>
  );
}
