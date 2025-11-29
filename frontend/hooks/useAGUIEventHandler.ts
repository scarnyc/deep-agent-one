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
   * Extract text token from streaming chunk.
   * Supports OpenAI and Gemini formats.
   * Returns null for non-text chunks (tool calls, signatures, etc.)
   */
  const extractTokenFromChunk = (chunk: unknown): string | null => {
    if (!chunk) return null;

    // 1. Direct string chunk
    if (typeof chunk === 'string') {
      return chunk || null;
    }

    // Type guard for object chunks
    if (typeof chunk !== 'object') return null;
    const chunkObj = chunk as Record<string, unknown>;

    // 2. Check for tool call chunks FIRST - skip silently
    const functionCall = (chunkObj.additional_kwargs as Record<string, unknown>)?.function_call;
    const toolCalls = chunkObj.tool_calls as unknown[];
    if (functionCall || (Array.isArray(toolCalls) && toolCalls.length > 0)) {
      // Tool call being streamed - not text content
      return null;
    }

    // 3. Handle content field
    const content = chunkObj.content;

    // 3a. Empty array - Gemini non-text event (skip)
    if (Array.isArray(content) && content.length === 0) {
      return null;
    }

    // 3b. Non-empty array - Gemini format: [{type: "text", text: "...", index: 0}]
    if (Array.isArray(content) && content.length > 0) {
      const textParts = content
        .filter((block: unknown): block is { type: string; text: string } => {
          if (typeof block === 'string') return true;
          if (typeof block === 'object' && block !== null) {
            const b = block as Record<string, unknown>;
            return b.type === 'text' && typeof b.text === 'string';
          }
          return false;
        })
        .map((block) => {
          if (typeof block === 'string') return block;
          return (block as { text: string }).text;
        })
        .filter((text) => text.length > 0); // Filter out empty (signature chunks)

      return textParts.length > 0 ? textParts.join('') : null;
    }

    // 3c. String content - OpenAI format: {content: "text"}
    if (typeof content === 'string' && content.length > 0) {
      return content;
    }

    // 4. Nested content.content (some providers)
    const nestedContent = (content as Record<string, unknown>)?.content;
    if (typeof nestedContent === 'string' && nestedContent.length > 0) {
      return nestedContent;
    }

    // 5. Text field: {text: "content"}
    if (typeof chunkObj.text === 'string' && (chunkObj.text as string).length > 0) {
      return chunkObj.text as string;
    }

    // 6. Delta format: {delta: {content: "text"}}
    const delta = chunkObj.delta as Record<string, unknown> | undefined;
    if (typeof delta?.content === 'string' && (delta.content as string).length > 0) {
      return delta.content as string;
    }

    // 7. Check for finish_reason - end of stream, not an error
    const finishReason =
      (chunkObj.response_metadata as Record<string, unknown>)?.finish_reason ||
      chunkObj.finish_reason ||
      (chunkObj.response_metadata as Record<string, unknown>)?.stop_reason;
    if (finishReason) {
      return null; // End of stream marker
    }

    // 8. Unknown format - log in development only
    if (process.env.NODE_ENV === 'development') {
      console.debug('[AG-UI] Unhandled chunk format:', JSON.stringify(chunk).substring(0, 300));
    }

    return null;
  };

  /**
   * Handle streaming token events
   *
   * Supports multiple LLM providers:
   * - OpenAI: Streams tokens as {type: "ai_chunk", content: "text"}
   * - Gemini: Streams tokens as {type: "ai_chunk", content: [{type: "text", text: "..."}]}
   */
  const handleChatModelStream = (event: TextMessageContentEvent) => {
    const chunk = event.data?.chunk;

    // Extract token using universal extractor (supports OpenAI, Gemini, etc.)
    const token = extractTokenFromChunk(chunk);

    // No token? Skip (tool calls, empty chunks, finish markers)
    if (!token) {
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
      }

      // Now append the token
      streamingContentRef.current += token;

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
   *
   * For non-streaming providers (like Gemini), extracts content from event.data.output
   * since these providers don't stream tokens character-by-character.
   */
  const handleChatModelEnd = (event: TextMessageEndEvent) => {
    console.log('[AG-UI] Chat model end - marking end of shard');

    // Check if we have accumulated streaming content
    // If not, try to get content from event.data.output (for non-streaming responses like Gemini)
    let finalContent = streamingContentRef.current;

    if (!finalContent || finalContent.trim() === '') {
      // Try to extract from event.data.output (LangChain AIMessage)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const output = (event as any).data?.output;
      if (output) {
        // Handle AIMessage object: {type: "ai", content: "..."}
        if (typeof output.content === 'string' && output.content.trim()) {
          finalContent = output.content;
          console.log('[AG-UI] Extracted content from on_chat_model_end output:', finalContent.substring(0, 100));
        }
        // Handle direct string output
        else if (typeof output === 'string' && output.trim()) {
          finalContent = output;
          console.log('[AG-UI] Extracted direct string from on_chat_model_end output:', finalContent.substring(0, 100));
        }
      }
    }

    // If we now have content but no message exists, create one
    // This handles Gemini and other non-streaming providers
    if (finalContent && finalContent.trim() && !streamingMessageIdRef.current) {
      const messageId = addMessage(threadId, {
        role: 'assistant',
        content: finalContent,
        metadata: {
          run_id: event.run_id,
          streaming: false,
          completed: true,
        },
      });
      streamingMessageIdRef.current = messageId;
      streamingContentRef.current = finalContent;
      console.log('[AG-UI] Created message from non-streaming output, id:', messageId);
    }

    if (streamingMessageIdRef.current) {
      // Update message content (may have been extracted from output)
      updateMessage(threadId, streamingMessageIdRef.current, {
        content: streamingContentRef.current,
        metadata: {
          streaming: true,  // Keep streaming for next shard
          run_id: event.run_id,
        },
      });

      // Mark that next shard needs separator BEFORE its first token
      needsShardSeparatorRef.current = true;

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

    // IMPORTANT: Finalize any orphaned streaming message before clearing refs
    if (streamingMessageIdRef.current) {
      console.warn('[AG-UI] Finalizing orphaned streaming message due to error');
      updateMessage(threadId, streamingMessageIdRef.current, {
        content: streamingContentRef.current || '[Response interrupted by error]',
        metadata: {
          streaming: false,
          completed: true,
          completion_reason: 'error',
          error: normalizedError.message,
        },
      });

      // Clear timers
      clearCompletionTimers();
    }

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
    needsShardSeparatorRef.current = false;
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
