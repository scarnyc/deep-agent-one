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
import { validateAGUIEvent, shouldFilterEvent, getEventCategory } from '@/lib/eventValidator';
import { getConfig, fetchConfig } from '@/lib/config';

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

  /**
   * Get WebSocket URL from props or config
   *
   * Simplified: Uses centralized config from /api/v1/config/public endpoint.
   * Config is fetched on mount and cached for subsequent calls.
   *
   * Priority:
   * 1. Explicit URL prop (with security validation)
   * 2. Config from backend (handles Replit, env vars, etc.)
   */
  const getWebSocketUrl = useCallback((): string => {
    // Priority 1: Use explicit URL prop if provided
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

    // Priority 2: Use config from backend (fetched on mount via fetchConfig)
    const config = getConfig();

    // SSR guard
    if (typeof window === 'undefined') {
      return `ws://localhost:8000${config.websocket_path}`;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname;

    // Replit: Connect directly to backend on port 8000
    if (config.is_replit) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (apiUrl && !apiUrl.includes('localhost')) {
        const wsUrl = apiUrl.replace(/^http/, 'ws');
        const fullWsUrl = `${wsUrl}${config.websocket_path}`;
        console.log('[WebSocketProvider] Replit detected - connecting to:', fullWsUrl);
        if (DEBUG) {
          console.log('[WebSocketProvider] Replit: using config', wsUrl);
        }
        return fullWsUrl;
      }
      const portUrl = `${protocol}//${hostname}:8000${config.websocket_path}`;
      console.log('[WebSocketProvider] Replit detected - connecting to port 8000:', portUrl);
      return portUrl;
    }

    // Standard: Use same origin
    const standardUrl = `${protocol}//${window.location.host}${config.websocket_path}`;
    console.log('[WebSocketProvider] Standard mode - same origin connection:', standardUrl);
    return standardUrl;
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
   * Validates and filters events using comprehensive event validator
   */
  const broadcastEvent = useCallback((event: AGUIEvent) => {
    // Validate event structure and type
    const validation = validateAGUIEvent(event);

    if (!validation.isValid) {
      console.error('[WebSocketProvider] Invalid event received:', validation.error, event);
      return; // Don't broadcast invalid events
    }

    // Filter custom backend events (not part of AG-UI Protocol)
    if (shouldFilterEvent(event.event)) {
      if (DEBUG) {
        const category = getEventCategory(event.event);
        console.log(
          `[WebSocketProvider] Filtered ${category} event:`,
          event.event,
          validation.warning || 'Custom backend event'
        );
      }
      return; // Don't broadcast custom events
    }

    // Log standard AG-UI events in development
    if (DEBUG) {
      const category = getEventCategory(event.event);
      console.log(`[WebSocketProvider] Broadcasting ${category} event:`, event.event);
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
    // GUARD: Don't create new connection if one is already open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (DEBUG) {
        console.log('[WebSocketProvider] Connection already open, skipping reconnect');
      }
      return;
    }

    // GUARD: Don't create new connection if one is connecting
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      if (DEBUG) {
        console.log('[WebSocketProvider] Connection already connecting, skipping');
      }
      return;
    }

    // Clean up existing connection (only if CLOSING or CLOSED)
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

  // Fetch config and initialize WebSocket connection sequentially
  useEffect(() => {
    let mounted = true;
    let reconnectTimeoutId: NodeJS.Timeout | null = null;

    const initializeWebSocket = async () => {
      try {
        // STEP 1: Wait for config to load
        await fetchConfig();

        if (!mounted) return;

        // STEP 2: Only connect after config is ready
        if (autoConnect) {
          if (DEBUG) {
            console.log('[WebSocketProvider] Config loaded, connecting...');
          }
          connect();
        }
      } catch (err) {
        if (DEBUG) {
          console.warn('[WebSocketProvider] Failed to fetch config:', err);
        }

        // Fallback: Still attempt connection with defaults
        if (mounted && autoConnect) {
          if (DEBUG) {
            console.log('[WebSocketProvider] Connecting with default config...');
          }
          connect();
        }
      }
    };

    initializeWebSocket();

    return () => {
      mounted = false;
      if (reconnectTimeoutId) {
        clearTimeout(reconnectTimeoutId);
      }
      // Preserve existing cleanup logic from the original auto-connect useEffect
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
      // Clear all event handlers
      eventHandlersRef.current.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Only depend on autoConnect, connect is stable via useCallback

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
      if (DEBUG) {
        // DEBUG: Enhanced logging to understand what's being sent
        console.log('[DEBUG WebSocketProvider] sendMessage called with:');
        console.log('[DEBUG WebSocketProvider]   message type:', typeof message);
        console.log('[DEBUG WebSocketProvider]   message value:', message);
        console.log('[DEBUG WebSocketProvider]   arguments.length:', arguments.length);
        if (arguments.length > 1) {
          console.log('[DEBUG WebSocketProvider]   EXTRA ARGUMENTS:', Array.from(arguments).slice(1));
        }
      }

      const jsonString = JSON.stringify(message);

      if (DEBUG) {
        console.log('[DEBUG WebSocketProvider]   JSON string to send:', jsonString);
        console.log('[DEBUG WebSocketProvider]   WebSocket readyState:', wsRef.current.readyState);
      }

      wsRef.current.send(jsonString);

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
