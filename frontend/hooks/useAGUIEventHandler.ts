/**
 * AG-UI Event Handler Hook
 *
 * Processes WebSocket AG-UI Protocol events and updates Zustand store.
 * Part of Phase 0 AG-UI Protocol implementation.
 *
 * Event Handlers:
 * - on_chain_start / on_llm_start → Update agent status to "running"
 * - on_chat_model_stream → Append streaming tokens to current message
 * - on_chat_model_end → Mark message complete
 * - on_tool_start → Add tool call to store
 * - on_tool_end → Update tool call result
 * - hitl_request → Show HITL approval UI
 * - hitl_approval → Resume agent execution
 * - on_chain_end / on_llm_end → Update agent status to "completed"
 * - error → Update agent status to "error", show error message
 */

import { useRef, useEffect } from 'react';
import { useAgentState } from './useAgentState';
import { useWebSocketContext } from './useWebSocketContext';
import {
  AGUIEvent,
  RunStartedEvent,
  RunFinishedEvent,
  RunErrorEvent,
  TextMessageContentEvent,
  TextMessageEndEvent,
  ToolCallStartEvent,
  ToolCallArgsEvent,
  ToolCallEndEvent,
  ToolCallResultEvent,
  HITLRequestEvent,
  ErrorEvent,
} from '@/types/ag-ui';

/**
 * Hook to handle AG-UI Protocol events
 */
export function useAGUIEventHandler(threadId: string) {
  const {
    addMessage,
    updateMessage,
    addToolCall,
    updateToolCall,
    setAgentStatus,
    addStep,
    updateStep,
    setHITLRequest,
  } = useAgentState();

  // Track current streaming message ID
  const streamingMessageIdRef = useRef<string | null>(null);
  const streamingContentRef = useRef<string>('');

  /**
   * Handle run started events (chain/llm start)
   */
  const handleRunStarted = (event: RunStartedEvent) => {
    console.log('[AG-UI] Run started:', event.name);

    // Update agent status to running
    setAgentStatus(threadId, 'running');

    // Add a step for this run
    addStep(threadId, {
      id: event.run_id,
      name: event.name,
      status: 'running',
      started_at: new Date().toISOString(),
      metadata: {
        tags: event.tags,
        ...event.metadata,
      },
    });
  };

  /**
   * Handle run finished events (chain/llm end)
   */
  const handleRunFinished = (event: RunFinishedEvent) => {
    console.log('[AG-UI] Run finished:', event.run_id);

    // Update step status
    updateStep(threadId, event.run_id, {
      status: 'completed',
      completed_at: new Date().toISOString(),
    });

    // Update agent status to completed
    setAgentStatus(threadId, 'completed');

    // Clear streaming message ref
    streamingMessageIdRef.current = null;
    streamingContentRef.current = '';
  };

  /**
   * Handle streaming token events
   */
  const handleChatModelStream = (event: TextMessageContentEvent) => {
    const token = event.data.chunk.content || '';
    if (!token) return;

    // If no streaming message exists, create one
    if (!streamingMessageIdRef.current) {
      const messageId = `msg-${Date.now()}`;
      streamingMessageIdRef.current = messageId;
      streamingContentRef.current = token;

      addMessage(threadId, {
        role: 'assistant',
        content: token,
        metadata: {
          run_id: event.run_id,
          streaming: true,
        },
      });
    } else {
      // Append token to existing message
      streamingContentRef.current += token;

      // Find and update the streaming message
      updateMessage(threadId, streamingMessageIdRef.current, {
        content: streamingContentRef.current,
      });
    }
  };

  /**
   * Handle chat model end event
   */
  const handleChatModelEnd = (event: TextMessageEndEvent) => {
    console.log('[AG-UI] Chat model end');

    if (streamingMessageIdRef.current) {
      // Mark message as complete
      updateMessage(threadId, streamingMessageIdRef.current, {
        metadata: {
          streaming: false,
          completed: true,
          run_id: event.run_id,
        },
      });

      // Clear refs
      streamingMessageIdRef.current = null;
      streamingContentRef.current = '';
    }
  };

  /**
   * Handle tool call start event
   */
  const handleToolCallStart = (event: ToolCallStartEvent | ToolCallArgsEvent) => {
    console.log('[AG-UI] Tool call started:', event.name);

    // Get input from event (if it's a ToolCallArgsEvent)
    const input = 'input' in event ? event.input : {};

    // Add tool call to store
    addToolCall(threadId, {
      id: event.run_id,
      name: event.name || 'unknown',
      args: typeof input === 'object' ? input : {},
      status: 'running',
      started_at: new Date().toISOString(),
    });

    // Add step for tool execution
    addStep(threadId, {
      id: `tool-${event.run_id}`,
      name: `Executing ${event.name}`,
      status: 'running',
      started_at: new Date().toISOString(),
    });
  };

  /**
   * Handle tool call end event
   */
  const handleToolCallEnd = (event: ToolCallEndEvent | ToolCallResultEvent) => {
    console.log('[AG-UI] Tool call finished:', event.run_id);

    // Get output from event (if it's a ToolCallResultEvent)
    const output = 'output' in event ? event.output : undefined;

    // Update tool call with result
    updateToolCall(threadId, event.run_id, {
      status: 'completed',
      result: output,
      completed_at: new Date().toISOString(),
    });

    // Update corresponding step
    updateStep(threadId, `tool-${event.run_id}`, {
      status: 'completed',
      completed_at: new Date().toISOString(),
    });
  };

  /**
   * Handle HITL request event
   */
  const handleHITLRequest = (event: HITLRequestEvent) => {
    console.log('[AG-UI] HITL request:', event.data?.tool_name);

    // Update agent status
    setAgentStatus(threadId, 'waiting_for_approval');

    // Set HITL request in store
    setHITLRequest(threadId, {
      run_id: event.run_id,
      thread_id: threadId,
      tool_name: event.data?.tool_name || 'unknown',
      tool_args: event.data?.tool_args || {},
      reason: event.data?.reason,
      requested_at: new Date().toISOString(),
    });

    // Add step
    addStep(threadId, {
      id: `hitl-${event.run_id}`,
      name: 'Awaiting user approval',
      status: 'pending',
      started_at: new Date().toISOString(),
      metadata: {
        tool_name: event.data?.tool_name,
      },
    });
  };

  /**
   * Handle run error event
   */
  const handleRunError = (event: RunErrorEvent | ErrorEvent) => {
    console.error('[AG-UI] Run error:', event);

    // Update agent status
    setAgentStatus(threadId, 'error');

    // Extract error message
    const errorMessage = event.error?.message || 'An unknown error occurred';

    // Add error message
    addMessage(threadId, {
      role: 'system',
      content: `Error: ${errorMessage}`,
      metadata: {
        error: true,
        run_id: event.run_id,
        error_type: event.error?.type,
      },
    });

    // Update step if exists
    if (event.run_id) {
      updateStep(threadId, event.run_id, {
        status: 'error',
        completed_at: new Date().toISOString(),
        metadata: {
          error: errorMessage,
          error_type: event.error?.type,
        },
      });
    }

    // Clear streaming refs
    streamingMessageIdRef.current = null;
    streamingContentRef.current = '';
  };

  /**
   * Main event handler router
   */
  const handleEvent = (event: AGUIEvent) => {
    console.log('[AG-UI] Event received:', event.event, event);

    try {
      switch (event.event) {
        case 'on_chain_start':
        case 'on_llm_start':
        case 'on_chat_model_start':
          handleRunStarted(event as RunStartedEvent);
          break;

        case 'on_chain_end':
        case 'on_llm_end':
          handleRunFinished(event as RunFinishedEvent);
          break;

        case 'on_chat_model_stream':
          handleChatModelStream(event as TextMessageContentEvent);
          break;

        case 'on_chat_model_end':
          handleChatModelEnd(event as TextMessageEndEvent);
          break;

        case 'on_tool_start':
          handleToolCallStart(event as ToolCallStartEvent);
          break;

        case 'on_tool_end':
          handleToolCallEnd(event as ToolCallEndEvent);
          break;

        case 'hitl_request':
          handleHITLRequest(event as HITLRequestEvent);
          break;

        case 'on_chain_error':
        case 'on_llm_error':
        case 'error':
          handleRunError(event as RunErrorEvent | ErrorEvent);
          break;

        default:
          console.log('[AG-UI] Unhandled event type:', event.event);
      }
    } catch (error) {
      console.error('[AG-UI] Error handling event:', error, event);
    }
  };

  // Get WebSocket context (shared connection)
  const { addEventListener } = useWebSocketContext();

  // Register event handler with WebSocket
  useEffect(() => {
    const unsubscribe = addEventListener(handleEvent);
    return unsubscribe; // Cleanup on unmount
  }, [addEventListener, handleEvent]);

  return {
    handleEvent,
  };
}
