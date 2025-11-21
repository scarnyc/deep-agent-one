/**
 * AG-UI Protocol Event Validator
 *
 * Validates WebSocket events against the AG-UI Protocol specification.
 * Distinguishes between standard AG-UI events and custom backend events.
 *
 * AG-UI Protocol Reference:
 * - https://docs.ag-ui.com/sdk/python/core/overview
 *
 * Standard AG-UI Events:
 * - Lifecycle: on_chain_start, on_chain_end, on_llm_start, on_llm_end, etc.
 * - Streaming: on_chat_model_stream
 * - Tools: on_tool_start, on_tool_end
 * - Errors: on_chain_error, on_llm_error, error
 * - HITL: hitl_request, hitl_approval
 * - Heartbeat: heartbeat (keepalive during long operations)
 *
 * Transformed Events (Backend EventTransformer):
 * - on_step: Transformed chain events (on_chain_start/end → on_step with status: running/completed)
 * - on_tool_call: Transformed tool events (on_tool_start/end → on_tool_call with status: running/completed)
 * These events decouple the frontend from LangGraph's event schema, allowing independent evolution.
 * See: backend/deep_agent/services/event_transformer.py
 *
 * Custom Backend Events (NOT part of AG-UI Protocol):
 * - processing_started: Cold start notification (8-10s delay)
 * - connection_established: (deprecated, no longer sent by backend)
 */

/**
 * Standard AG-UI Protocol event types
 */
export const STANDARD_AGUI_EVENTS = {
  // Lifecycle Events
  CHAIN_START: 'on_chain_start',
  CHAIN_END: 'on_chain_end',
  CHAIN_ERROR: 'on_chain_error',

  LLM_START: 'on_llm_start',
  LLM_END: 'on_llm_end',
  LLM_ERROR: 'on_llm_error',

  CHAT_MODEL_START: 'on_chat_model_start',
  CHAT_MODEL_END: 'on_chat_model_end',

  // Streaming Events
  CHAT_MODEL_STREAM: 'on_chat_model_stream',

  // Tool Events
  TOOL_START: 'on_tool_start',
  TOOL_END: 'on_tool_end',

  // Transformed Events (EventTransformer)
  STEP: 'on_step',
  TOOL_CALL: 'on_tool_call',

  // Retriever Events (optional)
  RETRIEVER_START: 'on_retriever_start',
  RETRIEVER_END: 'on_retriever_end',

  // HITL Events
  HITL_REQUEST: 'hitl_request',
  HITL_APPROVAL: 'hitl_approval',

  // Error Events
  ERROR: 'error',
  ON_ERROR: 'on_error',

  // Heartbeat Events (keepalive during long operations)
  HEARTBEAT: 'heartbeat',
} as const;

/**
 * Custom backend events (NOT part of AG-UI Protocol)
 * These events must be filtered out before passing to AG-UI handlers.
 */
export const CUSTOM_BACKEND_EVENTS = {
  // Processing notification during cold start (8-10s delay)
  PROCESSING_STARTED: 'processing_started',

  // Deprecated: No longer sent by backend (removed in commit)
  CONNECTION_ESTABLISHED: 'connection_established',
} as const;

/**
 * All recognized event types (AG-UI + custom)
 */
export const ALL_EVENT_TYPES = {
  ...STANDARD_AGUI_EVENTS,
  ...CUSTOM_BACKEND_EVENTS,
} as const;

/**
 * Event validation result
 */
export interface ValidationResult {
  /** Whether the event is valid (recognized and well-formed) */
  isValid: boolean;

  /** Whether this is a custom backend event (not part of AG-UI Protocol) */
  isCustomEvent: boolean;

  /** The event type string */
  eventType: string;

  /** Error message if validation failed */
  error?: string;

  /** Warning message for non-critical issues */
  warning?: string;
}

/**
 * Validates an event against the AG-UI Protocol specification.
 *
 * Checks:
 * 1. Event has required 'event' field
 * 2. Event type is recognized (AG-UI or custom)
 * 3. Event structure is well-formed
 *
 * @param event - The event object to validate
 * @returns Validation result with details
 *
 * @example
 * ```typescript
 * const result = validateAGUIEvent({ event: 'on_chat_model_stream', data: {...} });
 * if (!result.isValid) {
 *   console.error('Invalid event:', result.error);
 * }
 * ```
 */
export function validateAGUIEvent(event: any): ValidationResult {
  // Defensive: Handle null/undefined
  if (!event || typeof event !== 'object') {
    return {
      isValid: false,
      isCustomEvent: false,
      eventType: 'unknown',
      error: 'Event must be a non-null object',
    };
  }

  // Check required 'event' field
  if (!event.event || typeof event.event !== 'string') {
    return {
      isValid: false,
      isCustomEvent: false,
      eventType: event.event || 'unknown',
      error: "Event must have an 'event' field of type string",
    };
  }

  const eventType = event.event.trim();

  // Check if empty
  if (!eventType) {
    return {
      isValid: false,
      isCustomEvent: false,
      eventType: 'unknown',
      error: 'Event type cannot be empty',
    };
  }

  // Check if recognized event type
  const isStandard = isStandardAGUIEvent(eventType);
  const isCustom = isCustomEvent(eventType);

  if (!isStandard && !isCustom) {
    return {
      isValid: false,
      isCustomEvent: false,
      eventType,
      error: `Unrecognized event type: ${eventType}`,
    };
  }

  // Handle deprecated events
  if (eventType === CUSTOM_BACKEND_EVENTS.CONNECTION_ESTABLISHED) {
    return {
      isValid: true,
      isCustomEvent: true,
      eventType,
      warning: 'connection_established is deprecated and should be filtered',
    };
  }

  // Valid event
  return {
    isValid: true,
    isCustomEvent: isCustom,
    eventType,
  };
}

/**
 * Checks if an event type is a standard AG-UI Protocol event.
 *
 * @param eventType - The event type string
 * @returns True if standard AG-UI event, false otherwise
 *
 * @example
 * ```typescript
 * isStandardAGUIEvent('on_chat_model_stream') // true
 * isStandardAGUIEvent('processing_started')   // false
 * ```
 */
export function isStandardAGUIEvent(eventType: string): boolean {
  return Object.values(STANDARD_AGUI_EVENTS).includes(
    eventType as any
  );
}

/**
 * Checks if an event type is a custom backend event.
 *
 * @param eventType - The event type string
 * @returns True if custom event, false otherwise
 *
 * @example
 * ```typescript
 * isCustomEvent('processing_started')       // true
 * isCustomEvent('on_chat_model_stream')     // false
 * ```
 */
export function isCustomEvent(eventType: string): boolean {
  return Object.values(CUSTOM_BACKEND_EVENTS).includes(
    eventType as any
  );
}

/**
 * Determines if an event should be filtered out before passing to AG-UI handlers.
 *
 * Custom backend events must be filtered to prevent "unknown event" errors
 * in AG-UI Protocol handlers.
 *
 * @param eventType - The event type string
 * @returns True if event should be filtered, false otherwise
 *
 * @example
 * ```typescript
 * shouldFilterEvent('processing_started')  // true (custom event)
 * shouldFilterEvent('on_chat_model_stream') // false (standard AG-UI)
 * ```
 */
export function shouldFilterEvent(eventType: string): boolean {
  return isCustomEvent(eventType);
}

/**
 * Type guard for lifecycle events (start/end).
 *
 * @param eventType - The event type string
 * @returns True if lifecycle event
 */
export function isLifecycleEvent(eventType: string): boolean {
  return [
    STANDARD_AGUI_EVENTS.CHAIN_START,
    STANDARD_AGUI_EVENTS.CHAIN_END,
    STANDARD_AGUI_EVENTS.LLM_START,
    STANDARD_AGUI_EVENTS.LLM_END,
    STANDARD_AGUI_EVENTS.CHAT_MODEL_START,
    STANDARD_AGUI_EVENTS.CHAT_MODEL_END,
  ].includes(eventType as any);
}

/**
 * Type guard for streaming events.
 *
 * @param eventType - The event type string
 * @returns True if streaming event
 */
export function isStreamingEvent(eventType: string): boolean {
  return eventType === STANDARD_AGUI_EVENTS.CHAT_MODEL_STREAM;
}

/**
 * Type guard for tool events.
 *
 * @param eventType - The event type string
 * @returns True if tool event
 */
export function isToolEvent(eventType: string): boolean {
  return [
    STANDARD_AGUI_EVENTS.TOOL_START,
    STANDARD_AGUI_EVENTS.TOOL_END,
  ].includes(eventType as any);
}

/**
 * Type guard for error events.
 *
 * @param eventType - The event type string
 * @returns True if error event
 */
export function isErrorEvent(eventType: string): boolean {
  return [
    STANDARD_AGUI_EVENTS.CHAIN_ERROR,
    STANDARD_AGUI_EVENTS.LLM_ERROR,
    STANDARD_AGUI_EVENTS.ERROR,
    STANDARD_AGUI_EVENTS.ON_ERROR,
  ].includes(eventType as any);
}

/**
 * Type guard for HITL (Human-in-the-Loop) events.
 *
 * @param eventType - The event type string
 * @returns True if HITL event
 */
export function isHITLEvent(eventType: string): boolean {
  return [
    STANDARD_AGUI_EVENTS.HITL_REQUEST,
    STANDARD_AGUI_EVENTS.HITL_APPROVAL,
  ].includes(eventType as any);
}

/**
 * Type guard for retriever events.
 *
 * @param eventType - The event type string
 * @returns True if retriever event
 */
export function isRetrieverEvent(eventType: string): boolean {
  return [
    STANDARD_AGUI_EVENTS.RETRIEVER_START,
    STANDARD_AGUI_EVENTS.RETRIEVER_END,
  ].includes(eventType as any);
}

/**
 * Gets a human-readable category name for an event type.
 *
 * @param eventType - The event type string
 * @returns Category name (e.g., "Lifecycle", "Streaming", "Custom")
 *
 * @example
 * ```typescript
 * getEventCategory('on_chat_model_stream') // "Streaming"
 * getEventCategory('processing_started')   // "Custom"
 * ```
 */
export function getEventCategory(eventType: string): string {
  if (isLifecycleEvent(eventType)) return 'Lifecycle';
  if (isStreamingEvent(eventType)) return 'Streaming';
  if (isToolEvent(eventType)) return 'Tool';
  if (isErrorEvent(eventType)) return 'Error';
  if (isHITLEvent(eventType)) return 'HITL';
  if (isRetrieverEvent(eventType)) return 'Retriever';
  if (isCustomEvent(eventType)) return 'Custom';
  return 'Unknown';
}

/**
 * Validates multiple events in batch.
 *
 * @param events - Array of events to validate
 * @returns Array of validation results
 *
 * @example
 * ```typescript
 * const results = validateBatch([
 *   { event: 'on_chat_model_stream', data: {...} },
 *   { event: 'processing_started', data: {...} },
 * ]);
 * const invalidEvents = results.filter(r => !r.isValid);
 * ```
 */
export function validateBatch(events: any[]): ValidationResult[] {
  if (!Array.isArray(events)) {
    return [{
      isValid: false,
      isCustomEvent: false,
      eventType: 'unknown',
      error: 'Input must be an array of events',
    }];
  }

  return events.map(validateAGUIEvent);
}

/**
 * Filters out custom events from an event array.
 *
 * @param events - Array of events
 * @returns Array with only standard AG-UI events
 *
 * @example
 * ```typescript
 * const filtered = filterCustomEvents([
 *   { event: 'on_chat_model_stream', data: {...} },  // kept
 *   { event: 'processing_started', data: {...} },     // removed
 * ]);
 * ```
 */
export function filterCustomEvents(events: any[]): any[] {
  if (!Array.isArray(events)) return [];

  return events.filter(event => {
    if (!event || typeof event !== 'object' || !event.event) return false;
    return !shouldFilterEvent(event.event);
  });
}
