/**
 * Chat Layout Component
 *
 * @fileoverview Wraps the chat route with WebSocketProvider context.
 * Required for useWebSocketContext and useAGUIEventHandler hooks.
 *
 * @see @/contexts/WebSocketProvider - WebSocket connection management
 * @see ./page.tsx - Chat page using this layout
 */

'use client';

import { WebSocketProvider } from '@/contexts/WebSocketProvider';

/**
 * Chat route layout with WebSocket context
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Page content (chat page)
 * @returns {JSX.Element} Children wrapped in WebSocketProvider
 */
export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <WebSocketProvider>{children}</WebSocketProvider>;
}
