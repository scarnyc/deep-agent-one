'use client';

/**
 * AG-UI Components Test Page
 *
 * Test page to verify AG-UI components render correctly
 * and integrate with Zustand store.
 */

import { useEffect } from 'react';
import { useAgentState } from '@/hooks/useAgentState';
import ToolCallDisplay from '@/components/ag-ui/ToolCallDisplay';
import ProgressTracker from '@/components/ag-ui/ProgressTracker';
import AgentStatus from '@/components/ag-ui/AgentStatus';
import { Button } from '@/components/ui/button';

export default function TestAGUIPage() {
  const {
    createThread,
    setActiveThread,
    addMessage,
    addToolCall,
    setAgentStatus,
    addStep,
    active_thread_id,
  } = useAgentState();

  // Initialize test thread
  useEffect(() => {
    const threadId = 'test-thread-1';
    createThread(threadId);
    setActiveThread(threadId);
  }, [createThread, setActiveThread]);

  // Add mock data for testing
  const handleAddMockData = () => {
    if (!active_thread_id) return;

    // Add a message
    addMessage(active_thread_id, {
      role: 'assistant',
      content: 'Testing AG-UI components!',
      metadata: {
        reasoning_effort: 'medium',
        tokens_used: 150,
        model: 'gpt-5',
      },
    });

    // Add a tool call
    addToolCall(active_thread_id, {
      id: 'tool-1',
      name: 'web_search',
      args: {
        query: 'Latest AI news',
        num_results: 5,
      },
      status: 'completed',
      result: {
        results: ['AI breakthrough', 'New model release'],
        count: 2,
      },
      started_at: new Date().toISOString(),
      completed_at: new Date(Date.now() + 2000).toISOString(),
    });

    // Add some steps
    const step1Id = 'step-1';
    addStep(active_thread_id, {
      id: step1Id,
      name: 'Analyzing query',
      status: 'completed',
      started_at: new Date().toISOString(),
      completed_at: new Date(Date.now() + 1000).toISOString(),
    });

    const step2Id = 'step-2';
    addStep(active_thread_id, {
      id: step2Id,
      name: 'Searching web',
      status: 'running',
      started_at: new Date().toISOString(),
    });

    // Set agent status
    setAgentStatus(active_thread_id, 'running');
  };

  const handleClearData = () => {
    if (!active_thread_id) return;
    const threadId = active_thread_id;
    createThread(threadId);
    setActiveThread(threadId);
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold mb-2">AG-UI Components Test</h1>
          <p className="text-muted-foreground">
            Testing ToolCallDisplay, ProgressTracker, and AgentStatus components
          </p>
        </div>

        {/* Controls */}
        <div className="flex gap-4">
          <Button onClick={handleAddMockData}>Add Mock Data</Button>
          <Button onClick={handleClearData} variant="outline">
            Clear Data
          </Button>
        </div>

        {/* Components Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: AgentStatus */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Agent Status</h2>
            <AgentStatus />
          </div>

          {/* Center: ProgressTracker */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Progress Tracker</h2>
            <ProgressTracker />
          </div>

          {/* Right: ToolCallDisplay */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Tool Calls</h2>
            <ToolCallDisplay />
          </div>
        </div>

        {/* Debug Info */}
        {active_thread_id && (
          <div className="mt-8 p-4 bg-muted rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Debug Info</h3>
            <p className="text-sm text-muted-foreground font-mono">
              Active Thread: {active_thread_id}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
