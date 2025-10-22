/**
 * Chat Page
 *
 * Main chat interface using CopilotKit for AG-UI Protocol communication
 * with the Deep Agent backend.
 */

'use client';

import { CopilotChat } from '@copilotkit/react-ui';
import { useAgentState } from '@/hooks/useAgentState';
import { useHITLActions } from './components/HITLApproval';
import { useEffect } from 'react';

export default function ChatPage() {
  const { createThread, setActiveThread } = useAgentState();

  // Register HITL approval actions
  useHITLActions();

  useEffect(() => {
    // Create a new thread on page load
    const threadId = crypto.randomUUID();
    createThread(threadId);
    setActiveThread(threadId);
  }, [createThread, setActiveThread]);

  return (
    <div className="h-screen w-full flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-5xl h-full">
        <CopilotChat
          className="h-full rounded-2xl shadow-xl border border-border"
          labels={{
            title: 'Deep Agent',
            initial: "Hi! I'm Deep Agent. I can search the web, execute code, manage files, and more. How can I help you today?",
            placeholder: 'Ask me anything...',
          }}
        />
      </div>
    </div>
  );
}
