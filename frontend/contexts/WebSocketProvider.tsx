/**
 * WebSocketProvider React Context
 *
 * Provides a singleton WebSocket connection for the entire application.
 * Manages connection lifecycle, reconnection logic, and event distribution.
 *
 * Key Features:
 * - Single WebSocket instance shared across all components
 * - Auto-reconnection with exponential backoff
 * - Event filtering (removes custom backend events)
 * - Type-safe event subscription API
 * - Connection state management
 *
 * Usage:
 * ```tsx
 * <WebSocketProvider>
 *   <App />
 * </WebSocketProvider>
 * ```
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import type { AGUIEvent, ConnectionStatus } from '@/types/ag-ui';

// Development logging (disabled in production)
const DEBUG = process.env.NODE_ENV === 'development';

/**
 * Event handler function type
 */
type EventHandler = (event: AGUIEvent) => void;

/**
 * WebSocket context value
 */
export interface WebSocketContextValue {
  // Connection state
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  readyState: number; // 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED

  // Actions
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;

  // Event subscription (returns unsubscribe function)
  addEventListener: (handler: EventHandler) => () => void;
}

/**
 * WebSocket Provider props
 */
export interface WebSocketProviderProps {
  children: React.ReactNode;
  url?: string; // Default: ws://localhost:8000/api/v1/ws
  autoConnect?: boolean; // Default: true
}

/**
 * WebSocket context (undefined = not initialized)
 * Exported for use in custom hooks or testing
 */
export const WebSocketContext = createContext<WebSocketContextValue | undefined>(undefined);

/**
 * Hook to access WebSocket context
 * @throws Error if used outside WebSocketProvider
 */
export function useWebSocketContext(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

/**
 * WebSocketProvider Component
 *
 * Provides a singleton WebSocket connection to all child components.
 * Handles connection lifecycle, reconnection, and event distribution.
 */
export function WebSocketProvider({
  children,
  url,
  autoConnect = true,
}: WebSocketProviderProps) {
  // Connection state (triggers UI updates)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [readyState, setReadyState] = useState<number>(WebSocket.CLOSED); // 3 = CLOSED
  const isConnected = connectionStatus === 'connected';

  // WebSocket instance (ref prevents re-renders)
  const wsRef = useRef<WebSocket | null>(null);

  // Event subscribers (Set for O(1) add/remove)
  const eventHandlersRef = useRef<Set<EventHandler>>(new Set());

  // Reconnection state
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Configuration constants
  const MAX_RECONNECT_ATTEMPTS = 10;
  const RECONNECT_INTERVAL = 1000; // 1s
  const MAX_RECONNECT_INTERVAL = 30000; // 30s
  const CONNECTION_TIMEOUT = 30000; // 30s (allows for cold start)

  // Custom events to filter (not part of AG-UI Protocol)
  const CUSTOM_EVENTS = ['connection_established', 'processing_started'];

  /**
   * Get WebSocket URL from props or environment
   */
  const getWebSocketUrl = useCallback((): string => {
    if (url) {
      try {
        // Validate URL format
        const wsUrl = new URL(url);
        const apiUrl = new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

        // Security: Ensure same origin (prevent connection to malicious servers)
        if (wsUrl.hostname !== apiUrl.hostname) {
          throw new Error(
            `WebSocket URL origin (${wsUrl.hostname}) doesn't match API URL (${apiUrl.hostname})`
          );
        }

        return url;
      } catch (err) {
        console.error('[WebSocketProvider] Invalid WebSocket URL:', err);
        throw new Error('Invalid WebSocket URL');
      }
    }

    // Default: Construct from environment
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws'); // Convert http(s):// to ws(s)://
    return `${wsUrl}/api/v1/ws`;
  }, [url]);

  /**
   * Calculate reconnect delay with exponential backoff
   */
  const getReconnectDelay = useCallback((): number => {
    const delay = Math.min(
      RECONNECT_INTERVAL * Math.pow(2, reconnectAttemptRef.current),
      MAX_RECONNECT_INTERVAL
    );
    return delay;
  }, []);

  /**
   * Broadcast event to all subscribers
   * Filters out custom backend events before broadcasting
   */
  const broadcastEvent = useCallback((event: AGUIEvent) => {
    // Filter custom backend events (not part of AG-UI Protocol)
    if (CUSTOM_EVENTS.includes(event.event)) {
      if (DEBUG) {
        console.log('[WebSocketProvider] Filtered custom event:', event.event, event);
      }
      return; // Don't broadcast custom events
    }

    // Broadcast to all subscribers
    eventHandlersRef.current.forEach((handler) => {
      try {
        handler(event);
      } catch (err) {
        console.error('[WebSocketProvider] Error in event handler:', err);
      }
    });
  }, []);

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
      setReadyState(WebSocket.CONNECTING); // 0 = CONNECTING

      const wsUrl = getWebSocketUrl();
      const ws = new WebSocket(wsUrl);

      // Connection timeout protection (30s allows for cold start)
      const connectionTimeoutId = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          const timeoutError = new Error('WebSocket connection timeout (30s)');
          console.error('[WebSocketProvider]', timeoutError);
          setConnectionStatus('disconnected');
          ws.close();
        }
      }, CONNECTION_TIMEOUT);

      // Connection opened
      ws.onopen = () => {
        clearTimeout(connectionTimeoutId);
        if (DEBUG) {
          console.log('[WebSocketProvider] Connected to', wsUrl);
        }
        setConnectionStatus('connected');
        setReadyState(WebSocket.OPEN); // 1 = OPEN
        reconnectAttemptRef.current = 0; // Reset reconnect counter
      };

      // Message received
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as AGUIEvent;

          // Broadcast to all subscribers (filtering happens in broadcastEvent)
          broadcastEvent(data);
        } catch (err) {
          console.error('[WebSocketProvider] Failed to parse message:', err);
        }
      };

      // Connection error
      ws.onerror = (event) => {
        console.error('[WebSocketProvider] WebSocket error:', event);
      };

      // Connection closed
      ws.onclose = (event) => {
        if (DEBUG) {
          console.log('[WebSocketProvider] Disconnected:', event.code, event.reason);
        }
        setConnectionStatus('disconnected');
        setReadyState(WebSocket.CLOSED); // 3 = CLOSED
        wsRef.current = null;

        // Auto-reconnect if not a normal closure (code 1000)
        if (event.code !== 1000) {
          reconnectAttemptRef.current += 1;

          // Check max reconnection attempts
          if (reconnectAttemptRef.current > MAX_RECONNECT_ATTEMPTS) {
            console.error(
              `[WebSocketProvider] Max reconnection attempts (${MAX_RECONNECT_ATTEMPTS}) exceeded`
            );
            setConnectionStatus('disconnected');
            return; // Stop reconnecting
          }

          // Schedule reconnect with exponential backoff
          setConnectionStatus('reconnecting');
          const delay = getReconnectDelay();
          if (DEBUG) {
            console.log(
              `[WebSocketProvider] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current}/${MAX_RECONNECT_ATTEMPTS})`
            );
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WebSocketProvider] Connection error:', err);
      setConnectionStatus('disconnected');
    }
  }, [getWebSocketUrl, getReconnectDelay, broadcastEvent]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close connection (1000 = normal closure)
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
    setReadyState(WebSocket.CLOSED); // 3 = CLOSED
  }, []);

  /**
   * Send message to WebSocket
   * @param message - Message to send (will be JSON stringified)
   */
  const sendMessage = useCallback((message: any) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocketProvider] Cannot send message: not connected');
      return;
    }

    try {
      wsRef.current.send(JSON.stringify(message));
      if (DEBUG) {
        console.log('[WebSocketProvider] Sent message:', message);
      }
    } catch (err) {
      console.error('[WebSocketProvider] Send error:', err);
    }
  }, []);

  /**
   * Subscribe to WebSocket events
   * @param handler - Event handler function
   * @returns Unsubscribe function
   */
  const addEventListener = useCallback((handler: EventHandler): (() => void) => {
    eventHandlersRef.current.add(handler);

    // Return unsubscribe function
    return () => {
      eventHandlersRef.current.delete(handler);
    };
  }, []);

  /**
   * Auto-connect on mount
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
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

      // Clear all event handlers
      eventHandlersRef.current.clear();
    };
  }, [autoConnect, connect]);

  // Context value
  const value: WebSocketContextValue = {
    isConnected,
    connectionStatus,
    readyState,
    sendMessage,
    connect,
    disconnect,
    addEventListener,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
}
