/**
 * useWebSocket Hook
 *
 * React hook for WebSocket connection to backend AG-UI Protocol endpoint.
 * Provides auto-reconnect, exponential backoff, and typed event handling.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { AGUIEvent, ConnectionStatus, WebSocketMessage } from '@/types/ag-ui';

interface UseWebSocketOptions {
  url?: string; // WebSocket URL (defaults to NEXT_PUBLIC_API_URL/ws)
  autoConnect?: boolean; // Auto-connect on mount (default: true)
  reconnect?: boolean; // Enable auto-reconnect (default: true)
  reconnectInterval?: number; // Initial reconnect interval in ms (default: 1000)
  maxReconnectInterval?: number; // Max reconnect interval in ms (default: 30000)
  maxReconnectAttempts?: number; // Max reconnect attempts (default: 10)
  onEvent?: (event: AGUIEvent) => void; // Callback for AG-UI events
  onError?: (error: Error) => void; // Callback for errors
}

interface UseWebSocketReturn {
  sendMessage: (
    message: string,
    thread_id: string,
    metadata?: Record<string, any>
  ) => void;
  connectionStatus: ConnectionStatus;
  isConnected: boolean;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 1000,
    maxReconnectInterval = 30000,
    maxReconnectAttempts = 10,
    onEvent,
    onError,
  } = options;

  // State
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<Error | null>(null);
  const isConnected = connectionStatus === 'connected';

  // Refs (don't trigger re-renders)
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Callback refs (HIGH-1 fix: prevent infinite reconnection loops)
  const onEventRef = useRef(onEvent);
  const onErrorRef = useRef(onError);

  // Rate limiting refs (HIGH-2 fix: prevent message spam)
  const sendTimestampsRef = useRef<number[]>([]);
  const SEND_RATE_LIMIT = 10; // messages
  const SEND_RATE_WINDOW = 60000; // 60 seconds

  // Update callback refs when callbacks change
  useEffect(() => {
    onEventRef.current = onEvent;
    onErrorRef.current = onError;
  }, [onEvent, onError]);

  /**
   * Get WebSocket URL from env or parameter
   */
  const getWebSocketUrl = useCallback((): string => {
    if (url) return url;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    // Convert http(s):// to ws(s)://
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    return `${wsUrl}/api/v1/ws`;
  }, [url]);

  /**
   * Calculate reconnect delay with exponential backoff
   */
  const getReconnectDelay = useCallback((): number => {
    const delay = Math.min(
      reconnectInterval * Math.pow(2, reconnectAttemptRef.current),
      maxReconnectInterval
    );
    return delay;
  }, [reconnectInterval, maxReconnectInterval]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      setConnectionStatus('connecting');
      setError(null);

      const wsUrl = getWebSocketUrl();
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[useWebSocket] Connected to', wsUrl);
        setConnectionStatus('connected');
        reconnectAttemptRef.current = 0; // Reset reconnect counter
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as AGUIEvent;

          // Call event callback if provided
          if (onEventRef.current) {
            onEventRef.current(data);
          }
        } catch (err) {
          const parseError = new Error(`Failed to parse WebSocket message: ${err}`);
          console.error('[useWebSocket]', parseError);
          setError(parseError);

          if (onErrorRef.current) {
            onErrorRef.current(parseError);
          }
        }
      };

      ws.onerror = (event) => {
        console.error('[useWebSocket] WebSocket error:', event);
        const wsError = new Error('WebSocket connection error');
        setError(wsError);

        if (onErrorRef.current) {
          onErrorRef.current(wsError);
        }
      };

      ws.onclose = (event) => {
        console.log('[useWebSocket] Disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Auto-reconnect if enabled and not a normal closure (HIGH-3 fix: max attempts)
        if (reconnect && event.code !== 1000) {
          reconnectAttemptRef.current += 1;

          // Check max reconnection attempts
          if (reconnectAttemptRef.current > maxReconnectAttempts) {
            const maxAttemptsError = new Error(
              `Max reconnection attempts (${maxReconnectAttempts}) exceeded`
            );
            console.error('[useWebSocket]', maxAttemptsError);
            setError(maxAttemptsError);
            setConnectionStatus('error');

            if (onErrorRef.current) {
              onErrorRef.current(maxAttemptsError);
            }
            return; // Stop reconnecting
          }

          setConnectionStatus('reconnecting');
          const delay = getReconnectDelay();
          console.log(
            `[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current}/${maxReconnectAttempts})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      const connectionError = err instanceof Error ? err : new Error(String(err));
      console.error('[useWebSocket] Connection error:', connectionError);
      setError(connectionError);
      setConnectionStatus('error');

      if (onErrorRef.current) {
        onErrorRef.current(connectionError);
      }
    }
  }, [getWebSocketUrl, reconnect, getReconnectDelay, maxReconnectAttempts]); // HIGH-1 fix: removed onEvent, onError from deps

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect'); // Normal closure
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
  }, []);

  /**
   * Send message to backend
   */
  const sendMessage = useCallback(
    (message: string, thread_id: string, metadata?: Record<string, any>) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.warn('[useWebSocket] Cannot send message: not connected');
        return;
      }

      // HIGH-2 fix: Rate limiting to prevent message spam
      const now = Date.now();
      sendTimestampsRef.current = sendTimestampsRef.current.filter(
        (ts) => now - ts < SEND_RATE_WINDOW
      );

      if (sendTimestampsRef.current.length >= SEND_RATE_LIMIT) {
        const rateLimitError = new Error(
          `Rate limit exceeded: ${SEND_RATE_LIMIT} messages per ${SEND_RATE_WINDOW / 1000}s`
        );
        console.error('[useWebSocket]', rateLimitError);
        setError(rateLimitError);

        if (onErrorRef.current) {
          onErrorRef.current(rateLimitError);
        }
        return;
      }

      sendTimestampsRef.current.push(now);

      const wsMessage: WebSocketMessage = {
        type: 'chat',
        message,
        thread_id,
        metadata,
      };

      try {
        wsRef.current.send(JSON.stringify(wsMessage));
        console.log('[useWebSocket] Sent message:', wsMessage);
      } catch (err) {
        const sendError = err instanceof Error ? err : new Error(String(err));
        console.error('[useWebSocket] Send error:', sendError);
        setError(sendError);

        if (onErrorRef.current) {
          onErrorRef.current(sendError);
        }
      }
    },
    [] // Empty deps after HIGH-1 fix (using refs for callbacks)
  );

  /**
   * Auto-connect on mount, cleanup on unmount
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    sendMessage,
    connectionStatus,
    isConnected,
    error,
    connect,
    disconnect,
  };
}
