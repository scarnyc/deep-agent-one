/**
 * useWebSocket Hook
 *
 * React hook for WebSocket connection to backend AG-UI Protocol endpoint.
 * Provides auto-reconnect, exponential backoff, and typed event handling.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { AGUIEvent, ConnectionStatus, WebSocketMessage } from '@/types/ag-ui';

// Issue 51 fix: Conditional logging for production
const DEBUG = process.env.NODE_ENV === 'development';

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
    // Issue 50 fix: Validate URL origin if provided
    if (url) {
      try {
        const wsUrl = new URL(url);
        const apiUrl = new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

        // Ensure same origin (security: prevent connection to malicious servers)
        if (wsUrl.hostname !== apiUrl.hostname) {
          throw new Error(
            `WebSocket URL origin (${wsUrl.hostname}) doesn't match API URL (${apiUrl.hostname})`
          );
        }

        return url;
      } catch (err) {
        console.error('[useWebSocket] Invalid WebSocket URL:', err);
        throw new Error('Invalid WebSocket URL');
      }
    }

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

      // Issue 49 fix: Add connection timeout protection
      const CONNECTION_TIMEOUT = 10000; // 10 seconds
      const connectionTimeoutId = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          const timeoutError = new Error('WebSocket connection timeout (10s)');
          console.error('[useWebSocket]', timeoutError);
          setError(timeoutError);
          setConnectionStatus('error');

          ws.close();

          if (onErrorRef.current) {
            onErrorRef.current(timeoutError);
          }
        }
      }, CONNECTION_TIMEOUT);

      ws.onopen = () => {
        clearTimeout(connectionTimeoutId); // Clear timeout on successful connection
        if (DEBUG) {
          console.log('[useWebSocket] Connected to', wsUrl);
        }
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
        if (DEBUG) {
          console.log('[useWebSocket] Disconnected:', event.code, event.reason);
        }
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
          if (DEBUG) {
            console.log(
              `[useWebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current}/${maxReconnectAttempts})`
            );
          }

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

      // Issue 47 fix: Validate inputs
      if (!message || message.trim().length === 0) {
        const validationError = new Error('Message cannot be empty');
        console.warn('[useWebSocket]', validationError);
        setError(validationError);
        if (onErrorRef.current) {
          onErrorRef.current(validationError);
        }
        return;
      }

      if (!thread_id || thread_id.trim().length === 0) {
        const validationError = new Error('Thread ID is required');
        console.warn('[useWebSocket]', validationError);
        setError(validationError);
        if (onErrorRef.current) {
          onErrorRef.current(validationError);
        }
        return;
      }

      // Limit message length to prevent DoS
      const MAX_MESSAGE_LENGTH = 10000; // 10KB
      if (message.length > MAX_MESSAGE_LENGTH) {
        const validationError = new Error(
          `Message too long (${message.length} chars, max ${MAX_MESSAGE_LENGTH})`
        );
        console.error('[useWebSocket]', validationError);
        setError(validationError);
        if (onErrorRef.current) {
          onErrorRef.current(validationError);
        }
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
        if (DEBUG) {
          console.log('[useWebSocket] Sent message:', wsMessage);
        }
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

    // Issue 48 fix: Use inline cleanup to avoid stale closure
    return () => {
      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Close connection
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }

      setConnectionStatus('disconnected');
    };
  }, [autoConnect, connect]); // Removed disconnect from deps

  return {
    sendMessage,
    connectionStatus,
    isConnected,
    error,
    connect,
    disconnect,
  };
}
