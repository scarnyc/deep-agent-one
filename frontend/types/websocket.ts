/**
 * WebSocket Message Types
 *
 * Type definitions for WebSocket communication between frontend and backend.
 * These types must match the backend's WebSocketMessage Pydantic model.
 */

/**
 * WebSocket message sent from client to server
 *
 * Example:
 * ```typescript
 * const message: WebSocketMessage = {
 *   type: 'chat',
 *   message: 'Hello, agent!',
 *   thread_id: 'user-123',
 *   metadata: { user_id: '123' }
 * };
 * ```
 */
export interface WebSocketMessage {
  /** Message type (currently only 'chat' is supported) */
  type: 'chat';

  /** User message content (min 1 char after trimming) */
  message: string;

  /** Conversation thread identifier (min 1 char after trimming) */
  thread_id: string;

  /** Optional metadata for the message */
  metadata?: Record<string, any>;
}

/**
 * WebSocket error response from server
 */
export interface WebSocketError {
  type: 'error';
  error: string;
  request_id?: string;
}

/**
 * Type guard to check if a message is a WebSocketMessage
 */
export function isWebSocketMessage(value: any): value is WebSocketMessage {
  return (
    typeof value === 'object' &&
    value !== null &&
    value.type === 'chat' &&
    typeof value.message === 'string' &&
    value.message.trim().length > 0 &&
    typeof value.thread_id === 'string' &&
    value.thread_id.trim().length > 0
  );
}

/**
 * Type guard to check if a message is a WebSocketError
 */
export function isWebSocketError(value: any): value is WebSocketError {
  return (
    typeof value === 'object' &&
    value !== null &&
    value.type === 'error' &&
    typeof value.error === 'string'
  );
}
