'use client';

/**
 * Chat Interface Component (AG-UI Protocol)
 *
 * Custom chat interface replacing CopilotChat with native AG-UI Protocol support.
 * Part of Phase 0 AG-UI Protocol implementation.
 *
 * Features:
 * - Message list with role-based styling
 * - Streaming message display (token-by-token)
 * - Message input with send button
 * - Auto-scroll to bottom on new messages
 * - Keyboard shortcuts (Enter to send, Shift+Enter for newline)
 * - Loading states and error handling
 */

import { useState, useRef, useEffect } from 'react';
import { useAgentState } from '@/hooks/useAgentState';
import { useWebSocketContext } from '@/hooks/useWebSocketContext';
import type { WebSocketMessage } from '@/types/websocket';
import { AgentMessage, MessageRole } from '@/types/agent';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Send, User, Bot, Loader2, AlertCircle } from 'lucide-react';

/**
 * Get avatar icon for message role
 */
function getRoleIcon(role: MessageRole): React.ReactNode {
  switch (role) {
    case 'user':
      return <User className="h-4 w-4" />;
    case 'assistant':
      return <Bot className="h-4 w-4" />;
    case 'system':
      return <AlertCircle className="h-4 w-4" />;
    case 'tool':
      return <Bot className="h-4 w-4" />;
    default:
      return <Bot className="h-4 w-4" />;
  }
}

/**
 * Get styling for message role
 */
function getRoleStyling(role: MessageRole): {
  containerClass: string;
  messageClass: string;
  avatarClass: string;
} {
  switch (role) {
    case 'user':
      return {
        containerClass: 'flex justify-end',
        messageClass: 'bg-primary text-primary-foreground',
        avatarClass: 'bg-primary text-primary-foreground',
      };
    case 'assistant':
      return {
        containerClass: 'flex justify-start',
        messageClass: 'bg-muted',
        avatarClass: 'bg-secondary text-secondary-foreground',
      };
    case 'system':
      return {
        containerClass: 'flex justify-center',
        messageClass: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border border-yellow-500/20',
        avatarClass: 'bg-yellow-500/20 text-yellow-700',
      };
    case 'tool':
      return {
        containerClass: 'flex justify-start',
        messageClass: 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20',
        avatarClass: 'bg-blue-500/20 text-blue-700',
      };
    default:
      return {
        containerClass: 'flex justify-start',
        messageClass: 'bg-muted',
        avatarClass: 'bg-secondary text-secondary-foreground',
      };
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
}

/**
 * Message Item Component
 */
function MessageItem({ message }: { message: AgentMessage }) {
  const { containerClass, messageClass, avatarClass } = getRoleStyling(message.role);
  const icon = getRoleIcon(message.role);

  return (
    <div className={`${containerClass} mb-4`}>
      <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
        {/* Avatar */}
        <Avatar className={`flex-shrink-0 ${avatarClass}`}>
          <div className="flex items-center justify-center w-full h-full">
            {icon}
          </div>
        </Avatar>

        {/* Message content */}
        <div className={`flex flex-col gap-1 ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
          {/* Role label */}
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {message.role}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {formatTimestamp(message.timestamp)}
            </span>
          </div>

          {/* Message text */}
          <div className={`${messageClass} rounded-lg px-4 py-2 whitespace-pre-wrap break-words`}>
            {message.content}
          </div>

          {/* Metadata (reasoning effort, tokens) */}
          {message.metadata && (
            <div className="flex gap-2 text-xs text-muted-foreground">
              {message.metadata.reasoning_effort && (
                <span>Effort: {message.metadata.reasoning_effort}</span>
              )}
              {message.metadata.tokens_used && (
                <span>Tokens: {message.metadata.tokens_used}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Chat Interface Component
 */
export default function ChatInterface() {
  const { active_thread_id, threads, addMessage } = useAgentState();
  const { sendMessage, isConnected, connectionStatus, readyState } = useWebSocketContext();

  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Get messages from active thread
  const thread = active_thread_id ? threads[active_thread_id] : null;
  const messages: AgentMessage[] = thread?.messages || [];
  const agentStatus = thread?.agent_status || 'idle';

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages]);

  // Handle send message
  const handleSend = async () => {
    if (!input.trim() || !active_thread_id || !isConnected || isSending) return;

    const messageText = input.trim();
    setInput('');
    setIsSending(true);

    try {
      // Add user message to store immediately
      addMessage(active_thread_id, {
        role: 'user',
        content: messageText,
      });

      // DEBUG: Log what we're about to send
      const messageObject: WebSocketMessage = {
        type: 'chat',
        message: messageText,
        thread_id: active_thread_id,
      };
      console.log('[DEBUG ChatInterface] About to call sendMessage with:');
      console.log('[DEBUG ChatInterface]   messageText:', messageText);
      console.log('[DEBUG ChatInterface]   active_thread_id:', active_thread_id);
      console.log('[DEBUG ChatInterface]   messageObject:', messageObject);
      console.log('[DEBUG ChatInterface]   readyState:', readyState);
      console.log('[DEBUG ChatInterface]   sendMessage type:', typeof sendMessage);

      // Send message via WebSocket (FIXED: pass complete message object)
      sendMessage(messageObject);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      // Reset sending state after a short delay
      setTimeout(() => setIsSending(false), 500);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Connection status indicator
  const getConnectionIndicator = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <Badge
            variant="outline"
            className="text-green-500 border-green-500/20"
            data-testid="ws-status"
            data-status={connectionStatus}
            data-ready-state={readyState}
          >
            Connected
          </Badge>
        );
      case 'connecting':
      case 'reconnecting':
        return (
          <Badge
            variant="outline"
            className="text-yellow-500 border-yellow-500/20"
            data-testid="ws-status"
            data-status={connectionStatus}
            data-ready-state={readyState}
          >
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            {connectionStatus === 'connecting' ? 'Connecting' : 'Reconnecting'}
          </Badge>
        );
      case 'disconnected':
      case 'error':
        return (
          <Badge
            variant="outline"
            className="text-destructive border-destructive/20"
            data-testid="ws-status"
            data-status={connectionStatus}
            data-ready-state={readyState}
          >
            <AlertCircle className="h-3 w-3 mr-1" />
            Disconnected
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <Card className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold">Deep Agent Chat</h2>
          <p className="text-xs text-muted-foreground">
            Ask me anything about web search, code execution, and file management
          </p>
        </div>
        {getConnectionIndicator()}
      </div>

      {/* Messages */}
      <CardContent className="flex-1 p-4 overflow-hidden">
        <ScrollArea ref={scrollAreaRef} className="h-full pr-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Hi! I'm Deep Agent. I can search the web, execute code, manage files, and more.
                How can I help you today?
              </p>
            </div>
          ) : (
            <div className="space-y-0">
              {messages.map((message) => (
                <MessageItem key={message.id} message={message} />
              ))}

              {/* Agent is typing indicator */}
              {agentStatus === 'running' && (
                <div className="flex justify-start mb-4">
                  <div className="flex gap-3 max-w-[80%]">
                    <Avatar className="flex-shrink-0 bg-secondary text-secondary-foreground">
                      <div className="flex items-center justify-center w-full h-full">
                        <Bot className="h-4 w-4" />
                      </div>
                    </Avatar>
                    <div className="bg-muted rounded-lg px-4 py-2 flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </ScrollArea>
      </CardContent>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything... (Enter to send, Shift+Enter for new line)"
            className="min-h-[60px] max-h-[200px] resize-none"
            disabled={!isConnected || isSending}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || !isConnected || isSending}
            className="px-4"
            size="lg"
          >
            {isSending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Helper text */}
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-muted-foreground">
            Press Enter to send, Shift+Enter for new line
          </p>
          {!isConnected && (
            <p className="text-xs text-destructive">
              Disconnected - attempting to reconnect...
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
