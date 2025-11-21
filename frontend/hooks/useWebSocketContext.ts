/**
 * useWebSocketContext Hook
 *
 * React hook for consuming WebSocket context from WebSocketProvider.
 * Provides type-safe access to WebSocket state and methods.
 *
 * @throws {Error} If used outside WebSocketProvider
 *
 * @example
 * ```tsx
 * function ChatComponent() {
 *   const { sendMessage, isConnected, addEventListener } = useWebSocketContext();
 *
 *   useEffect(() => {
 *     const unsubscribe = addEventListener((event) => {
 *       console.log('Received AG-UI event:', event);
 *     });
 *
 *     return unsubscribe; // Cleanup on unmount
 *   }, [addEventListener]);
 *
 *   if (!isConnected) {
 *     return <p>Connecting...</p>;
 *   }
 *
 *   return <ChatInterface onSend={sendMessage} />;
 * }
 * ```
 */

import { useContext } from 'react';
import { WebSocketContext } from '@/contexts/WebSocketProvider';
import type { WebSocketContextValue } from '@/contexts/WebSocketProvider';

/**
 * Hook to consume WebSocket context.
 *
 * Must be used within a WebSocketProvider component tree.
 *
 * @returns WebSocket context value with connection state and methods
 * @throws Error if used outside WebSocketProvider
 */
export function useWebSocketContext(): WebSocketContextValue {
  const context = useContext(WebSocketContext);

  if (!context) {
    throw new Error(
      'useWebSocketContext must be used within a <WebSocketProvider>. ' +
      'Wrap your component tree with <WebSocketProvider> in your layout or app root.'
    );
  }

  return context;
}
