/**
 * ErrorDisplay Component
 *
 * Displays error messages from AG-UI Protocol error events with proper formatting.
 * Handles missing/empty error data gracefully using errorEventAdapter.
 *
 * Part of WebSocket CancelledError fix (2025-11-06)
 */

import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { normalizeErrorEvent, NormalizedError } from '@/lib/errorEventAdapter';
import type { AGUIEvent } from '@/types/ag-ui';

/**
 * Props for ErrorDisplay component.
 *
 * Extends NormalizedError with optional className for styling.
 */
export interface ErrorDisplayProps extends NormalizedError {
  /** Optional CSS class name for styling */
  className?: string;
}

/**
 * Display error information from AG-UI error events
 *
 * Uses errorEventAdapter to normalize error data from multiple protocols.
 * Shows error type, code, message, and debugging info (run_id, request_id in dev mode).
 *
 * @param props - Error display props
 * @param props.message - Error message to display
 * @param props.type - Error type (e.g., "WebSocketError", "ValidationError")
 * @param props.code - Optional error code
 * @param props.run_id - Optional run ID (shown in development only)
 * @param props.request_id - Optional request ID (shown in development only)
 * @param props.className - Optional CSS class name
 *
 * @example
 * ```tsx
 * <ErrorDisplay
 *   message="Connection failed"
 *   type="WebSocketError"
 *   code="WS_CLOSED"
 * />
 * ```
 */
export function ErrorDisplay({
  message,
  type,
  code,
  run_id,
  request_id,
  className,
}: ErrorDisplayProps) {
  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>
        {type}
        {code && ` (${code})`}
      </AlertTitle>
      <AlertDescription>
        <div className="space-y-1">
          <p>{message}</p>

          {/* Show run_id for debugging (only in development) */}
          {process.env.NODE_ENV === 'development' && run_id && (
            <p className="text-xs text-muted-foreground mt-2">
              Run ID: {run_id}
            </p>
          )}

          {/* Show request_id for debugging (only in development) */}
          {process.env.NODE_ENV === 'development' && request_id && (
            <p className="text-xs text-muted-foreground">
              Request ID: {request_id}
            </p>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Convenience component that normalizes error event and displays it
 *
 * @example
 * ```tsx
 * <ErrorDisplayFromEvent event={errorEvent} />
 * ```
 */
export function ErrorDisplayFromEvent({
  event,
  className,
}: {
  event: AGUIEvent;
  className?: string;
}) {
  const normalized = normalizeErrorEvent(event);

  return <ErrorDisplay {...normalized} className={className} />;
}
