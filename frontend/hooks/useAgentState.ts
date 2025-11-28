/**
 * useAgentState Hook
 *
 * Zustand store for managing agent conversation state, messages, tool calls,
 * and HITL (Human-in-the-Loop) workflows.
 *
 * This store provides a centralized state management solution for the Deep Agent
 * frontend, handling multiple conversation threads, real-time message updates,
 * tool execution tracking, and approval workflows.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  AgentMessage,
  AgentState,
  AgentStatus,
  AgentStep,
  ConversationThread,
  HITLRequest,
  ToolCall,
} from '@/types/agent';

/**
 * Generate unique ID for messages and tool calls
 *
 * Uses crypto.randomUUID() for cryptographically strong unique IDs.
 * Fallback to timestamp + random for older browsers (though Next.js 14 requires modern browsers).
 */
function generateId(): string {
  // Use crypto.randomUUID() for better uniqueness (prevents collision risk)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback for older environments (though unlikely in Next.js 14+)
  return `${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * Create empty conversation thread
 */
function createEmptyThread(thread_id: string): ConversationThread {
  const now = new Date().toISOString();
  return {
    thread_id,
    messages: [],
    tool_calls: [],
    hitl_request: undefined,
    agent_status: 'idle',
    current_step: undefined,
    steps: [],
    created_at: now,
    updated_at: now,
  };
}

/**
 * Zustand store for agent state management
 */
export const useAgentState = create<AgentState>()(
  devtools(
    (set, get) => ({
      // State
      threads: {},
      active_thread_id: null,

      // Actions

      /**
       * Set the active thread ID
       */
      setActiveThread: (thread_id: string) => {
        set({ active_thread_id: thread_id }, false, 'setActiveThread');
      },

      /**
       * Create a new conversation thread
       */
      createThread: (thread_id: string) => {
        set(
          (state) => ({
            threads: {
              ...state.threads,
              [thread_id]: createEmptyThread(thread_id),
            },
            active_thread_id: thread_id,
          }),
          false,
          'createThread'
        );
      },

      /**
       * Add a message to a thread
       * @returns The ID of the newly created message
       */
      addMessage: (thread_id: string, message: Omit<AgentMessage, 'id' | 'timestamp'>): string => {
        // Generate ID before set() so we can return it
        const messageId = generateId();

        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) {
              // Defensive logging for debugging race conditions
              console.error('[useAgentState] addMessage failed: thread not found');
              console.error('[useAgentState]   requested thread_id:', thread_id);
              console.error('[useAgentState]   available threads:', Object.keys(state.threads));
              return state;
            }

            const newMessage: AgentMessage = {
              ...message,
              id: messageId,
              timestamp: new Date().toISOString(),
            };

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  messages: [...thread.messages, newMessage],
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'addMessage'
        );

        return messageId;
      },

      /**
       * Update an existing message in a thread
       */
      updateMessage: (
        thread_id: string,
        message_id: string,
        updates: Partial<AgentMessage>
      ) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) {
              // Defensive logging for debugging race conditions
              console.error('[useAgentState] updateMessage failed: thread not found');
              console.error('[useAgentState]   requested thread_id:', thread_id);
              console.error('[useAgentState]   message_id:', message_id);
              console.error('[useAgentState]   available threads:', Object.keys(state.threads));
              return state;
            }

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  messages: thread.messages.map((msg) =>
                    msg.id === message_id ? { ...msg, ...updates } : msg
                  ),
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'updateMessage'
        );
      },

      /**
       * Add a tool call to a thread
       */
      addToolCall: (thread_id: string, tool_call: ToolCall) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  tool_calls: [...thread.tool_calls, tool_call],
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'addToolCall'
        );
      },

      /**
       * Update an existing tool call in a thread
       */
      updateToolCall: (
        thread_id: string,
        tool_call_id: string,
        updates: Partial<ToolCall>
      ) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  tool_calls: thread.tool_calls.map((tc) =>
                    tc.id === tool_call_id ? { ...tc, ...updates } : tc
                  ),
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'updateToolCall'
        );
      },

      /**
       * Set or clear HITL approval request for a thread
       */
      setHITLRequest: (thread_id: string, request: HITLRequest | undefined) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  hitl_request: request,
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'setHITLRequest'
        );
      },

      /**
       * Set agent status for a thread
       */
      setAgentStatus: (thread_id: string, status: AgentStatus) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  agent_status: status,
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'setAgentStatus'
        );
      },

      /**
       * Add a step/subtask to a thread
       */
      addStep: (thread_id: string, step: AgentStep) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  steps: [...thread.steps, step],
                  current_step: step,
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'addStep'
        );
      },

      /**
       * Update an existing step in a thread
       */
      updateStep: (thread_id: string, step_id: string, updates: Partial<AgentStep>) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            const updatedSteps = thread.steps.map((s) =>
              s.id === step_id ? { ...s, ...updates } : s
            );

            return {
              threads: {
                ...state.threads,
                [thread_id]: {
                  ...thread,
                  steps: updatedSteps,
                  // Update current_step if it's the one being updated
                  current_step:
                    thread.current_step?.id === step_id
                      ? { ...thread.current_step, ...updates }
                      : thread.current_step,
                  updated_at: new Date().toISOString(),
                },
              },
            };
          },
          false,
          'updateStep'
        );
      },

      /**
       * Clear all data for a thread
       */
      clearThread: (thread_id: string) => {
        set(
          (state) => {
            const thread = state.threads[thread_id];
            if (!thread) return state;

            return {
              threads: {
                ...state.threads,
                [thread_id]: createEmptyThread(thread_id),
              },
            };
          },
          false,
          'clearThread'
        );
      },

      // Selectors (computed values)

      /**
       * Get the active conversation thread
       */
      getActiveThread: () => {
        const state = get();
        if (!state.active_thread_id) return null;
        return state.threads[state.active_thread_id] || null;
      },

      /**
       * Get pending HITL request for a thread
       */
      getPendingHITL: (thread_id: string) => {
        const state = get();
        const thread = state.threads[thread_id];
        return thread?.hitl_request;
      },

      /**
       * Get all messages for a thread
       */
      getMessagesByThread: (thread_id: string) => {
        const state = get();
        const thread = state.threads[thread_id];
        return thread?.messages || [];
      },
    }),
    {
      name: 'agent-state',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);
