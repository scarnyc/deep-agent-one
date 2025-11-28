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
 * - on_step → Transformed chain events (status: running/completed)
 * - on_tool_call → Transformed tool events (status: running/completed)
 * - hitl_request → Show HITL approval UI
 * - hitl_approval → Resume agent execution
 * - on_chain_end / on_llm_end → Update agent status to "completed"
 * - on_error / on_chain_error / on_llm_error / error → Update agent status to "error", show error message
 *
 * Error Handling:
 * Supports multiple AI service protocols via normalizeErrorEvent():
 * - LangChain: on_error with data.error
 * - AG-UI: on_chain_error, on_llm_error with error.message
 * - Generic: error with error.message
 */

import { useRef, useEffect, useCallback } from 'react';
import { useAgentState } from './useAgentState';
import { useWebSocketContext } from './useWebSocketContext';
import { validateAGUIEvent, getEventCategory } from '@/lib/eventValidator';
import { normalizeErrorEvent } from '@/lib/errorEventAdapter';
import {
  AGUIEvent,
  RunStartedEvent,
  RunFinishedEvent,
  RunErrorEvent,
  OnErrorEvent,
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
  // Track if we just finished a shard (need separator before next token)
  const needsShardSeparatorRef = useRef<boolean>(false);
  // Fallback completion timer (if completion event never arrives)
  const completionFallbackTimerRef = useRef<NodeJS.Timeout | null>(null);
  // Stream watchdog timer (if streaming stalls)
  const streamWatchdogTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastStreamTokenTimeRef = useRef<number>(Date.now());

  /**
   * Helper: Clear all completion timers
   * Wrapped in useCallback to prevent recreation on every render
   */
  const clearCompletionTimers = useCallback(() => {
    if (completionFallbackTimerRef.current) {
      clearTimeout(completionFallbackTimerRef.current);
      completionFallbackTimerRef.current = null;
    }
    if (streamWatchdogTimerRef.current) {
      clearTimeout(streamWatchdogTimerRef.current);
      streamWatchdogTimerRef.current = null;
    }
  }, []); // No deps - only uses refs which are stable

  /**
   * Helper: Finalize message (mark complete and clear refs)
   * Used by both normal completion and fallback completion
   * Wrapped in useCallback to prevent recreation on every render
   */
  const finalizeMessage = useCallback((runId?: string, reason: 'normal' | 'fallback' | 'watchdog' = 'normal') => {
    if (!streamingMessageIdRef.current) return;

    console.log(`[AG-UI] Finalizing message (reason: ${reason})`);

    // Update message to mark complete
    updateMessage(threadId, streamingMessageIdRef.current, {
      content: streamingContentRef.current,
      metadata: {
        streaming: false,
        completed: true,
        run_id: runId,
        completion_reason: reason,
      },
    });

    // Update agent status to completed
    setAgentStatus(threadId, 'completed');

    // Clear all timers
    clearCompletionTimers();

    // Clear streaming refs
    streamingMessageIdRef.current = null;
    streamingContentRef.current = '';
    needsShardSeparatorRef.current = false;
  }, [threadId, updateMessage, setAgentStatus, clearCompletionTimers]);

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
   *
   * Marks the completion of the ENTIRE agent run (all shards complete).
   * This is when we mark the message as fully complete and clear refs.
   */
  const handleRunFinished = (event: RunFinishedEvent) => {
    console.log('[AG-UI] Run finished:', event.run_id);

    // Update step status
    updateStep(threadId, event.run_id, {
      status: 'completed',
      completed_at: new Date().toISOString(),
    });

    // Finalize message (mark complete and clear refs/timers)
    finalizeMessage(event.run_id, 'normal');
  };

  /**
   * Handle streaming token events
   */
  const handleChatModelStream = (event: TextMessageContentEvent) => {
    // Extract token from serialized chunk - backend serializes AIMessageChunk to {type, content}
    // Supports multiple formats from different LLM providers (OpenAI, Gemini, etc.)
    const chunk = event.data?.chunk;
    let token = '';

    // Debug: Log raw chunk format to diagnose provider-specific issues
    if (process.env.NODE_ENV === 'development') {
      console.log('[AG-UI] Raw chunk received:', JSON.stringify(chunk)?.substring(0, 200));
    }

    if (typeof chunk === 'string') {
      // Direct string content (some providers may send raw strings)
      token = chunk;
    } else if (chunk && typeof chunk.content === 'string') {
      // Standard format from backend serialization: {type: "ai_chunk", content: "text"}
      // This is what serialize_event() produces for AIMessageChunk
      token = chunk.content;
    } else if (chunk && typeof chunk === 'object') {
      // Handle nested object cases from different LLM providers:
      // - Gemini may send: {content: {type: "ai_chunk", content: "text"}}
      // - Some providers may send: {text: "content"}
      // - Others may send: {delta: {content: "text"}}
      const nestedContent = (chunk.content as { content?: string })?.content;
      const textContent = (chunk as { text?: string })?.text;
      const deltaContent = (chunk as { delta?: { content?: string } })?.delta?.content;

      if (typeof nestedContent === 'string') {
        token = nestedContent;
      } else if (typeof textContent === 'string') {
        token = textContent;
      } else if (typeof deltaContent === 'string') {
        token = deltaContent;
      }
    }

    // If no token extracted, log the chunk format for debugging
    if (!token) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('[AG-UI] Failed to extract token from chunk:', JSON.stringify(chunk)?.substring(0, 500));
      }
      return;
    }

    // Update last token timestamp for watchdog
    lastStreamTokenTimeRef.current = Date.now();

    // Reset watchdog timer (restart countdown on each token)
    if (streamWatchdogTimerRef.current) {
      clearTimeout(streamWatchdogTimerRef.current);
    }
    streamWatchdogTimerRef.current = setTimeout(() => {
      const timeSinceLastToken = Date.now() - lastStreamTokenTimeRef.current;
      if (streamingMessageIdRef.current && timeSinceLastToken >= 8000) {
        console.warn('[AG-UI] Stream watchdog timeout - no tokens for 8s, assuming completion');
        finalizeMessage(event.run_id, 'watchdog');
      }
    }, 8000); // 8 second watchdog timeout

    // If no streaming message exists, create one
    if (!streamingMessageIdRef.current) {
      streamingContentRef.current = token;

      // addMessage now returns the actual ID that was generated
      const generatedId = addMessage(threadId, {
        role: 'assistant',
        content: token,
        metadata: {
          run_id: event.run_id,
          streaming: true,
        },
      });

      // Store the ACTUAL ID returned from addMessage
      streamingMessageIdRef.current = generatedId;
    } else {
      // Check if we need to add separator BEFORE this token (new shard starting)
      if (needsShardSeparatorRef.current) {
        streamingContentRef.current += '\n\n';  // Add separator BEFORE token
        needsShardSeparatorRef.current = false;
        console.log('[DEBUG] Added \\n\\n separator before new shard token:', JSON.stringify(token));
      }

      // Now append the token
      streamingContentRef.current += token;

      console.log('[DEBUG] After appending token, content length:', streamingContentRef.current.length);
      console.log('[DEBUG] Last 100 chars:', streamingContentRef.current.slice(-100));

      // Now this ID matches the one in the store
      updateMessage(threadId, streamingMessageIdRef.current, {
        content: streamingContentRef.current,
      });
    }
  };

  /**
   * Handle chat model end event
   *
   * Marks the end of a response "shard" (one reasoning cycle).
   * Sets flag so next shard's first token will be preceded by \n\n separator.
   * Message is only marked complete when full agent run finishes (handleRunFinished).
   */
  const handleChatModelEnd = (event: TextMessageEndEvent) => {
    console.log('[AG-UI] Chat model end - marking end of shard');

    if (streamingMessageIdRef.current) {
      // DON'T add separator at end - we'll add it at the BEGINNING of the next shard
      console.log('[DEBUG] Shard ended, content length:', streamingContentRef.current.length);
      console.log('[DEBUG] Last 100 chars:', streamingContentRef.current.slice(-100));

      // Update message to mark shard complete but keep streaming
      updateMessage(threadId, streamingMessageIdRef.current, {
        content: streamingContentRef.current,
        metadata: {
          streaming: true,  // Keep streaming for next shard
          run_id: event.run_id,
        },
      });

      // Mark that next shard needs separator BEFORE its first token
      needsShardSeparatorRef.current = true;
      console.log('[DEBUG] Set needsShardSeparatorRef = true (next shard will start with \\n\\n)');

      // FALLBACK: Set timeout to finalize message if no run finish event arrives
      // This handles cases where on_chain_end/on_llm_end events are missing
      if (completionFallbackTimerRef.current) {
        clearTimeout(completionFallbackTimerRef.current);
      }
      completionFallbackTimerRef.current = setTimeout(() => {
        if (streamingMessageIdRef.current) {
          console.warn('[AG-UI] Fallback completion timeout - no run finish event received after chat model end');
          finalizeMessage(event.run_id, 'fallback');
        }
      }, 5000); // 5 second fallback timeout

      // DON'T clear refs - keep message ID active for next shard or until timeout
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
   *
   * Supports multiple error event formats:
   * - LangChain: on_error with data.error
   * - AG-UI: on_chain_error, on_llm_error with error.message
   * - Generic: error with error.message
   *
   * Uses normalizeErrorEvent() to extract error data consistently.
   */
  const handleRunError = (event: RunErrorEvent | OnErrorEvent | ErrorEvent) => {
    console.error('[AG-UI] Run error:', event);

    // Normalize error data from any format
    const normalizedError = normalizeErrorEvent(event);

    // Update agent status
    setAgentStatus(threadId, 'error');

    // Add error message
    addMessage(threadId, {
      role: 'system',
      content: `Error: ${normalizedError.message}`,
      metadata: {
        error: true,
        run_id: normalizedError.run_id,
        error_type: normalizedError.type,
        error_code: normalizedError.code,
        request_id: normalizedError.request_id,
      },
    });

    // Update step if exists
    if (normalizedError.run_id) {
      updateStep(threadId, normalizedError.run_id, {
        status: 'error',
        completed_at: new Date().toISOString(),
        metadata: {
          error: normalizedError.message,
          error_type: normalizedError.type,
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
  const handleEvent = useCallback((event: AGUIEvent) => {
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

        case 'on_step':
          // Transformed event from EventTransformer (backend)
          // Backend sends unique ID per step (based on run_id)
          if (event.data?.status === 'running') {
            // Use backend-provided ID (should be unique per step)
            // Fallback to generating unique ID if backend doesn't provide one
            const stepId = event.data.id || `step-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

            addStep(threadId, {
              id: stepId,
              name: event.data.name || 'Processing',
              status: 'running',
              started_at: new Date().toISOString(),
              metadata: event.data.metadata || {},
            });
          } else if (event.data?.status === 'completed') {
            // Use same ID as the running event to update existing step
            const stepId = event.data.id || event.run_id || 'unknown';

            updateStep(threadId, stepId, {
              status: 'completed',
              completed_at: new Date().toISOString(),
            });
          }
          break;

        case 'on_tool_call':
          // Transformed event from EventTransformer (backend)
          // Backend sends unique ID per tool call (based on run_id)
          if (event.data?.status === 'running') {
            // Use backend-provided ID (should be unique per tool call)
            // Fallback to generating unique ID if backend doesn't provide one
            const toolCallId = event.data.id || `tool-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

            addToolCall(threadId, {
              id: toolCallId,
              name: event.data.name || 'unknown',
              args: event.data.args || {},
              status: 'running',
              started_at: new Date().toISOString(),
            });
          } else if (event.data?.status === 'completed') {
            // Use same ID as the running event to update existing tool call
            const toolCallId = event.data.id || event.run_id || 'unknown';

            updateToolCall(threadId, toolCallId, {
              status: 'completed',
              result: event.data.result,
              completed_at: new Date().toISOString(),
            });
          }
          break;

        case 'hitl_request':
          handleHITLRequest(event as HITLRequestEvent);
          break;

        case 'on_chain_error':
        case 'on_llm_error':
        case 'on_error':      // LangChain convention
        case 'error':
          handleRunError(event as RunErrorEvent | OnErrorEvent | ErrorEvent);
          break;

        case 'heartbeat':
          // Heartbeat event - agent is still processing
          // Just log it to show activity, no state updates needed
          console.log('[AG-UI] Heartbeat received:', event.data);
          // Could update a "last activity" timestamp in state if needed
          break;

        default:
          // Validate and provide detailed logging for unhandled events
          const validation = validateAGUIEvent(event);
          const category = getEventCategory(event.event);

          if (!validation.isValid) {
            console.error(
              '[AG-UI] Received invalid event:',
              validation.error,
              event
            );
          } else if (validation.isCustomEvent) {
            console.warn(
              `[AG-UI] Custom event should have been filtered:`,
              `${category} event "${event.event}"`,
              validation.warning || 'This event is not part of AG-UI Protocol'
            );
          } else {
            console.warn(
              `[AG-UI] Unhandled ${category} event:`,
              event.event,
              'This is a valid AG-UI event but no handler is implemented yet.'
            );
          }
      }
    } catch (error) {
      console.error('[AG-UI] Error handling event:', error, event);
    }
  }, [
    threadId,
    addMessage,
    updateMessage,
    addToolCall,
    updateToolCall,
    setAgentStatus,
    addStep,
    updateStep,
    setHITLRequest,
    finalizeMessage,
    clearCompletionTimers,
  ]);

  // Get WebSocket context (shared connection)
  const { addEventListener } = useWebSocketContext();

  // Register event handler with WebSocket
  useEffect(() => {
    const unsubscribe = addEventListener(handleEvent);
    return unsubscribe; // Cleanup on unmount
  }, [addEventListener, handleEvent]);

  // Recovery: Finalize any orphaned streaming messages on mount
  useEffect(() => {
    const messages = useAgentState.getState().threads[threadId]?.messages || [];
    const orphanedMessages = messages.filter(
      (msg) => msg.metadata?.streaming === true && msg.role === 'assistant'
    );

    if (orphanedMessages.length > 0) {
      console.warn(
        `[AG-UI] Found ${orphanedMessages.length} orphaned streaming messages, finalizing them`
      );

      orphanedMessages.forEach((msg) => {
        updateMessage(threadId, msg.id, {
          metadata: {
            ...msg.metadata,
            streaming: false,
            completed: true,
            completion_reason: 'recovered',
          },
        });
      });
    }
  }, [threadId, updateMessage]); // Run once on mount and when threadId changes

  // Cleanup: Clear all timers on unmount
  useEffect(() => {
    return () => {
      clearCompletionTimers();
    };
  }, [clearCompletionTimers]);

  return {
    handleEvent,
  };
}
