/**
 * Error Event Adapter
 *
 * Normalizes error events from multiple AI service protocols into a consistent format.
 * Supports:
 * - LangChain convention: on_error with data.error
 * - AG-UI convention: RUN_ERROR, on_chain_error, on_llm_error
 * - Generic error: error with message field
 *
 * This adapter enables the Deep Agent framework to work with multiple
 * AI service backends without requiring protocol-specific error handling.
 */

import type { AGUIEvent, RunErrorEvent, OnErrorEvent, ErrorEvent } from '@/types/ag-ui';

/**
 * Normalized error structure
 *
 * All error events are converted to this consistent format
 * regardless of the original protocol.
 */
export interface NormalizedError {
  /** Error message (user-facing) */
  message: string;

  /** Error type (e.g., "ValueError", "APIError") */
  type: string;

  /** Error code (optional, protocol-specific) */
  code?: string;

  /** Stack trace (optional, debug only) */
  stack?: string;

  /** Run ID for tracing (optional) */
  run_id?: string;

  /** Request ID for tracking (optional) */
  request_id?: string;
}

/**
 * Normalizes error events from any protocol into a consistent format.
 *
 * Handles multiple error event structures:
 * 1. LangChain: { event: "on_error", data: { error: "msg", error_type: "type" } }
 * 2. AG-UI: { event: "on_chain_error", error: { message: "msg", type: "type" } }
 * 3. Generic: { event: "error", error: { message: "msg" } }
 *
 * @param event - Error event from WebSocket
 * @returns Normalized error data
 *
 * @example
 * ```typescript
 * const normalized = normalizeErrorEvent({
 *   event: "on_error",
 *   data: { error: "API timeout", error_type: "TimeoutError" }
 * });
 * // Returns: { message: "API timeout", type: "TimeoutError", ... }
 * ```
 */
export function normalizeErrorEvent(
  event: RunErrorEvent | OnErrorEvent | ErrorEvent | AGUIEvent
): NormalizedError {
  // Default fallback values
  let message = 'An unknown error occurred';
  let type = 'UnknownError';
  let code: string | undefined;
  let stack: string | undefined;
  let run_id: string | undefined;
  let request_id: string | undefined;

  // Extract run_id if present
  if ('run_id' in event) {
    run_id = event.run_id;
  }

  // Extract request_id from metadata or data
  if ('metadata' in event && event.metadata?.request_id) {
    request_id = event.metadata.request_id;
  } else if ('data' in event && (event as any).data?.request_id) {
    request_id = (event as any).data.request_id;
  }

  // Handle different error event formats
  switch (event.event) {
    case 'on_error': {
      // LangChain convention: error in data.error
      const onErrorEvent = event as OnErrorEvent;

      if (onErrorEvent.data?.error) {
        if (typeof onErrorEvent.data.error === 'string') {
          // Simple string error
          message = onErrorEvent.data.error;
        } else if (typeof onErrorEvent.data.error === 'object') {
          // Object with message/type/stack
          message = onErrorEvent.data.error.message || message;
          type = onErrorEvent.data.error.type || type;
          stack = onErrorEvent.data.error.stack;
        }
      }

      // Extract error_type if present
      if (onErrorEvent.data?.error_type) {
        type = onErrorEvent.data.error_type;
      }

      break;
    }

    case 'on_chain_error':
    case 'on_llm_error': {
      // AG-UI convention: error object with message/type
      const runErrorEvent = event as RunErrorEvent;

      if (runErrorEvent.error) {
        message = runErrorEvent.error.message || message;
        type = runErrorEvent.error.type || type;
        stack = runErrorEvent.error.stack;
      }

      break;
    }

    case 'error': {
      // Generic error event
      const errorEvent = event as ErrorEvent;

      if (errorEvent.error) {
        message = errorEvent.error.message || message;
        type = errorEvent.error.type || type;
        code = errorEvent.error.code;
      }

      break;
    }

    default: {
      // Unrecognized error event format
      // Try to extract error from common locations
      const anyEvent = event as any;

      // Try data.error
      if (anyEvent.data?.error) {
        if (typeof anyEvent.data.error === 'string') {
          message = anyEvent.data.error;
        } else if (anyEvent.data.error.message) {
          message = anyEvent.data.error.message;
          type = anyEvent.data.error.type || type;
        }
      }

      // Try error.message
      if (anyEvent.error?.message) {
        message = anyEvent.error.message;
        type = anyEvent.error.type || type;
      }

      // Try top-level message
      if (anyEvent.message) {
        message = anyEvent.message;
      }

      break;
    }
  }

  // Security: Sanitize message to prevent XSS
  // (Browser will escape HTML in text nodes, but be defensive)
  message = sanitizeErrorMessage(message);

  return {
    message,
    type,
    code,
    stack,
    run_id,
    request_id,
  };
}

/**
 * Sanitizes error messages to prevent potential XSS or information leakage.
 *
 * Removes:
 * - HTML tags (with loop to prevent bypass via nested tags)
 * - All angle brackets (escaped to prevent injection)
 * - Potential API keys/secrets
 *
 * Security: Applies regex replacement repeatedly until no more changes occur,
 * preventing bypass attacks like `<scr<script>ipt>alert(1)</script>` which
 * would otherwise result in `<script>alert(1)</script>` after one pass.
 *
 * @param message - Raw error message
 * @returns Sanitized error message
 */
function sanitizeErrorMessage(message: string): string {
  if (!message || typeof message !== 'string') {
    return 'An unknown error occurred';
  }

  let sanitized = message;

  // Remove HTML tags repeatedly until no more changes occur
  // This prevents bypass via nested tags like `<scr<script>ipt>`
  const htmlTagPattern = /<[^>]*>/g;
  let previous: string;
  let iterations = 0;
  const MAX_ITERATIONS = 10; // Prevent infinite loops on malformed input

  do {
    previous = sanitized;
    sanitized = sanitized.replace(htmlTagPattern, '');
    iterations++;
  } while (sanitized !== previous && iterations < MAX_ITERATIONS);

  // Escape any remaining angle brackets as a final safety measure
  // This ensures no HTML elements can be injected even if regex missed something
  sanitized = sanitized.replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Redact potential secrets (API keys, tokens)
  if (/sk-|lsv2_|key=|token=|password=/i.test(sanitized)) {
    sanitized = '[REDACTED: Potential secret in error message]';
  }

  // Limit length to prevent DoS
  const MAX_LENGTH = 500;
  if (sanitized.length > MAX_LENGTH) {
    sanitized = sanitized.substring(0, MAX_LENGTH) + '... (truncated)';
  }

  return sanitized.trim();
}

/**
 * Type guard to check if an event is an error event.
 *
 * @param event - Event to check
 * @returns True if error event
 */
export function isErrorEvent(event: AGUIEvent): boolean {
  return [
    'on_error',
    'on_chain_error',
    'on_llm_error',
    'error',
    'RUN_ERROR', // Future-proof for AG-UI convention
  ].includes(event.event);
}

/**
 * Gets a user-friendly error message from an error event.
 *
 * Convenience function for quick error message extraction.
 *
 * @param event - Error event
 * @returns User-friendly error message
 *
 * @example
 * ```typescript
 * const message = getErrorMessage(event);
 * toast.error(message);
 * ```
 */
export function getErrorMessage(event: AGUIEvent): string {
  const normalized = normalizeErrorEvent(event);
  return normalized.message;
}

/**
 * Gets the error type from an error event.
 *
 * @param event - Error event
 * @returns Error type string
 */
export function getErrorType(event: AGUIEvent): string {
  const normalized = normalizeErrorEvent(event);
  return normalized.type;
}
