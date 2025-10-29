# WebSocket Architecture Guide

Deep Agent AGI uses WebSocket for real-time bidirectional communication between frontend and backend, implementing the AG-UI Protocol for agent event streaming.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Event Types](#event-types)
4. [Usage Guide](#usage-guide)
5. [Troubleshooting](#troubleshooting)
6. [Testing](#testing)
7. [Best Practices](#best-practices)

---

## Overview

### What is the WebSocket Architecture?

The WebSocket system provides:
- **Real-time bidirectional communication** between client and server
- **Token-level streaming** for LLM responses (streaming one token at a time)
- **Agent event visibility** (chain starts, tool calls, errors, etc.)
- **Human-in-the-Loop (HITL)** approval workflows
- **Automatic reconnection** with exponential backoff
- **Connection status tracking** and error handling

### Key Features

- **Singleton Frontend Hook** (`useWebSocket`) - Single connection per app instance
- **AG-UI Protocol Compliance** - Standard event format for agent communication
- **Custom Events** - Backend-specific events for UX feedback (filtered from standard events)
- **Streaming Optimization** - Token-level granularity using `astream_events()`
- **Security** - Input validation, secret redaction, rate limiting, same-origin checks
- **Observability** - LangSmith tracing integrated with WebSocket events

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React Components (Chat, HITL Approval, etc.)       │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │ useAGUIEventHandler                     │
│                   │ (processes events)                      │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Zustand Store (useAgentState)                      │  │
│  │  - Messages                                          │  │
│  │  - Tool Calls                                        │  │
│  │  - HITL Requests                                     │  │
│  │  - Agent Status                                      │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  useWebSocket Hook (Singleton)                      │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │ - Connection management                        │ │  │
│  │  │ - Auto-reconnect with exponential backoff     │ │  │
│  │  │ - Message validation                          │ │  │
│  │  │ - Rate limiting                               │ │  │
│  │  │ - Event filtering (custom events removed)     │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│                   │ WebSocket Frame                         │
│                   │ (JSON: events and messages)             │
│                   ▼                                         │
└─────────────────────────────────────────────────────────────┘
                     ║ ws://localhost:8000/api/v1/ws
                     ║
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebSocket Endpoint (/api/v1/ws)                    │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │ - Accept connection                            │ │  │
│  │  │ - Validate incoming messages                   │ │  │
│  │  │ - Generate request IDs                         │ │  │
│  │  │ - Stream agent events                          │ │  │
│  │  │ - Error handling & secret redaction            │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AgentService.stream()                              │  │
│  │  - LangGraph DeepAgent execution                     │  │
│  │  - astream_events() for token-level streaming       │  │
│  │  - LangSmith tracing                                │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│                   ▼                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AG-UI Event Stream                                 │  │
│  │  - on_chat_model_stream (tokens)                     │  │
│  │  - on_chain_start / on_chain_end                     │  │
│  │  - on_tool_start / on_tool_end                       │  │
│  │  - hitl_request / error                              │  │
│  │  - processing_started (custom)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Connection Lifecycle

```
Client                                    Server
  │                                          │
  ├─── WebSocket.connect() ─────────────────>│
  │                                          │
  │                                  Connection accepted
  │<────────── ws.onopen() ──────────────────┤
  │                                          │
  │                                 Status: "connected"
  │                                          │
  ├─── Send message (chat) ──────────────────>│
  │    {type, message, thread_id}           │
  │                                          │
  │                                  Validate & process
  │                                          │
  │<─── processing_started (custom) ────────┤
  │     {event, data, request_id}           │
  │                                          │
  │<─── on_chain_start ────────────────────┤
  │     {event, run_id, name, ...}          │
  │                                          │
  │<─── on_chat_model_stream (tokens) ────┤
  │     {event, data: {chunk: {...}}}      │
  │                                          │
  │<─── on_chat_model_stream (token) ─────┤
  │     (repeated for each token)           │
  │                                          │
  │<─── on_chat_model_end ─────────────────┤
  │     {event, outputs: {...}}             │
  │                                          │
  │<─── on_chain_end ──────────────────────┤
  │     {event, run_id}                     │
  │                                          │
  │                                    Streaming complete
  │                                          │
  │ (connection stays open for next message)│
  │                                          │
  └─ ws.close() ──────────────────────────>│ (normal closure)
                                            │
                                    ws.onclose()
```

### Design Patterns

#### 1. Singleton Provider Pattern

The `useWebSocket` hook follows a singleton pattern:
- Single WebSocket connection per app instance
- Used by multiple components through custom hooks
- Connection persists across component re-renders
- State updates don't trigger reconnection

```typescript
// ✅ Correct: Single hook usage
const useAgentChat = () => {
  const { sendMessage, isConnected } = useWebSocket({
    onEvent: handleEvent,
  });
  return { sendMessage, isConnected };
};

// ❌ Incorrect: Multiple hook instances (creates multiple connections)
const Component1 = () => useWebSocket();  // Connection 1
const Component2 = () => useWebSocket();  // Connection 2
```

#### 2. Event Filtering Strategy

Custom backend events are filtered before passing to AG-UI handler:

```typescript
const customEvents = ['connection_established', 'processing_started'];

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Filter custom events (not AG-UI Protocol standard)
  if (customEvents.includes(data.event)) {
    console.log('Custom event:', data.event);  // Log for UX feedback
    return;  // Don't pass to AG-UI handler
  }

  // Only standard AG-UI events pass through
  if (onEvent) onEvent(data);
};
```

**Why:** AG-UI handlers only expect standard protocol events. Custom events cause "unknown event" errors if not filtered.

#### 3. AG-UI Protocol Compliance

All standard events follow the AG-UI Protocol format:

```typescript
interface BaseEvent {
  event: string;           // Event type (e.g., 'on_chat_model_stream')
  run_id?: string;         // Unique run identifier
  name?: string;           // Component name
  tags?: string[];         // Event tags
  metadata?: Record<string, any>;  // Custom metadata
}
```

---

## Event Types

### Standard AG-UI Protocol Events

These are standard events that follow the AG-UI Protocol specification.

#### Lifecycle Events

**`on_chain_start` / `on_llm_start`**
- Fired when a chain or LLM component starts execution
- Includes component name, run_id, and metadata
- Used to show "agent is thinking" status

```json
{
  "event": "on_chain_start",
  "run_id": "abc-123",
  "name": "agent",
  "tags": ["langchain", "agent"],
  "metadata": {"model": "gpt-5"}
}
```

**`on_chain_end` / `on_llm_end`**
- Fired when a chain or LLM component finishes execution
- Includes run_id and outputs
- Used to mark completion

```json
{
  "event": "on_chain_end",
  "run_id": "abc-123",
  "outputs": {"result": "..."}
}
```

**`on_chain_error` / `on_llm_error`**
- Fired when an error occurs during execution
- Includes error message, type, and stack trace
- Used to display error messages to user

```json
{
  "event": "on_chain_error",
  "run_id": "abc-123",
  "error": {
    "message": "API rate limit exceeded",
    "type": "RateLimitError",
    "stack": "..."
  }
}
```

#### Message Streaming Events

**`on_chat_model_start`**
- Fired when the LLM starts generating
- Includes messages sent to LLM

```json
{
  "event": "on_chat_model_start",
  "run_id": "llm-456",
  "name": "gpt-5",
  "messages": [
    {"role": "user", "content": "Tell me a joke"}
  ]
}
```

**`on_chat_model_stream`**
- Fired for each token generated by the LLM
- Core event for real-time streaming experience
- Includes the token chunk

```json
{
  "event": "on_chat_model_stream",
  "run_id": "llm-456",
  "data": {
    "chunk": {
      "content": "Why",
      "type": "text",
      "id": "msg-123"
    }
  }
}
```

**`on_chat_model_end`**
- Fired when LLM finishes generating
- Includes full response in outputs

```json
{
  "event": "on_chat_model_end",
  "run_id": "llm-456",
  "outputs": {
    "generations": [
      {
        "message": {
          "role": "assistant",
          "content": "Why did the scarecrow win an award?..."
        }
      }
    ]
  }
}
```

#### Tool Execution Events

**`on_tool_start`**
- Fired when a tool is about to be executed
- Includes tool name and arguments

```json
{
  "event": "on_tool_start",
  "run_id": "tool-789",
  "name": "read_file",
  "parent_run_id": "llm-456",
  "input": {"path": "/data/file.txt"}
}
```

**`on_tool_end`**
- Fired when tool execution completes
- Includes tool output/result

```json
{
  "event": "on_tool_end",
  "run_id": "tool-789",
  "output": "File contents here..."
}
```

#### HITL Events

**`hitl_request`**
- Fired when tool requires human approval before execution
- Blocks agent execution until approved

```json
{
  "event": "hitl_request",
  "run_id": "tool-789",
  "thread_id": "user-123",
  "data": {
    "tool_name": "write_file",
    "tool_args": {"path": "/data/config.json", "content": "..."},
    "reason": "Would modify system configuration"
  }
}
```

**`hitl_approval`**
- Sent FROM client TO server when user approves/rejects
- Not received by client (client sends it)

```json
{
  "event": "hitl_approval",
  "run_id": "tool-789",
  "thread_id": "user-123",
  "action": "accept" | "respond" | "edit",
  "response_text": "Proceed with execution",
  "tool_edits": {"path": "/different/path.json"}
}
```

#### Error Events

**`error`**
- Generic error event from backend
- Includes error message and type

```json
{
  "event": "error",
  "error": {
    "message": "WebSocket message validation failed",
    "type": "ValidationError",
    "code": "INVALID_MESSAGE"
  }
}
```

### Custom Backend Events

These are NOT part of AG-UI Protocol. Frontend **must filter** them before passing to AG-UI handler.

#### `processing_started`

**Purpose:** UX feedback during agent cold starts (8-10 seconds)

**When Sent:** Immediately after receiving chat message from client

**Format:**
```json
{
  "event": "processing_started",
  "data": {
    "message": "Agent initializing...",
    "request_id": "req-123",
    "timestamp": "2025-10-29T12:34:56Z"
  }
}
```

**Why Custom:**
- Not defined in AG-UI Protocol
- Helps users see feedback during agent startup
- Prevents blank screen during initialization
- Must be filtered from standard event handler

**Frontend Handling:**
```typescript
const customEvents = ['connection_established', 'processing_started'];

if (customEvents.includes(data.event)) {
  // Log for visibility, but don't pass to AG-UI handler
  console.log('Processing started...', data.data);
  return;  // Critical: Don't pass to AG-UI handler
}
```

#### Future Custom Events

Template for adding new custom events:

```python
# Backend: Send custom event
await websocket.send_json({
    "event": "my_custom_event",
    "data": {...},
    "request_id": request_id,
})

# Frontend: Filter and handle
const customEvents = ['processing_started', 'my_custom_event'];

if (customEvents.includes(data.event)) {
    // Handle custom event
    switch(data.event) {
        case 'my_custom_event':
            handleMyCustomEvent(data);
            break;
    }
    return;  // Don't pass to AG-UI handler
}
```

---

## Usage Guide

### Basic Setup

#### 1. Initialize useWebSocket in Root Component

```typescript
// app/chat/page.tsx
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAGUIEventHandler } from '@/hooks/useAGUIEventHandler';

export default function ChatPage() {
  const threadId = useThreadId();  // Get or generate thread ID

  // Initialize AG-UI event handler (includes WebSocket setup)
  const { handleEvent } = useAGUIEventHandler(threadId);

  return (
    <div>
      <ChatInterface threadId={threadId} />
      <MessageList threadId={threadId} />
      <ToolCallsList threadId={threadId} />
      <HITLApprovalDialog threadId={threadId} />
    </div>
  );
}
```

#### 2. Send Messages

```typescript
// components/ChatInput.tsx
import { useAgentState } from '@/hooks/useAgentState';
import { useWebSocket } from '@/hooks/useWebSocket';

export function ChatInput({ threadId }: { threadId: string }) {
  const { sendMessage } = useWebSocket();
  const [input, setInput] = useState('');

  const handleSend = () => {
    // Send message through WebSocket
    sendMessage(input, threadId, {
      user_id: 'user-123',
      timestamp: new Date().toISOString(),
    });

    setInput('');
  };

  return (
    <div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask me anything..."
      />
      <button onClick={handleSend}>Send</button>
    </div>
  );
}
```

#### 3. Handle Events

```typescript
// hooks/useAGUIEventHandler.ts - Already implemented!
export function useAGUIEventHandler(threadId: string) {
  const {
    addMessage,
    updateMessage,
    addToolCall,
    updateToolCall,
    setAgentStatus,
    setHITLRequest,
  } = useAgentState();

  // Handles all AG-UI event types
  // Updates Zustand store based on events
  // Automatically registers with WebSocket

  return { handleEvent };
}
```

#### 4. Display Messages

```typescript
// components/MessageList.tsx
import { useAgentState } from '@/hooks/useAgentState';

export function MessageList({ threadId }: { threadId: string }) {
  const thread = useAgentState(
    (state) => state.threads[threadId]
  );

  return (
    <div>
      {thread?.messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.role}`}>
          {msg.content}
          {msg.metadata?.streaming && <Spinner />}
        </div>
      ))}
    </div>
  );
}
```

#### 5. Display Tool Calls

```typescript
// components/ToolCallsList.tsx
export function ToolCallsList({ threadId }: { threadId: string }) {
  const toolCalls = useAgentState(
    (state) => state.threads[threadId]?.tool_calls || []
  );

  return (
    <div>
      {toolCalls.map((call) => (
        <div key={call.id} className={`tool-call ${call.status}`}>
          <strong>{call.name}</strong>
          <pre>{JSON.stringify(call.args, null, 2)}</pre>
          {call.result && (
            <div className="result">
              {typeof call.result === 'string'
                ? call.result
                : JSON.stringify(call.result, null, 2)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

#### 6. Handle HITL Approval

```typescript
// components/HITLApprovalDialog.tsx
export function HITLApprovalDialog({ threadId }: { threadId: string }) {
  const hitlRequest = useAgentState(
    (state) => state.threads[threadId]?.hitl_request
  );
  const { sendMessage } = useWebSocket();

  if (!hitlRequest) return null;

  const handleApprove = () => {
    // Send approval back to server
    sendMessage(
      JSON.stringify({
        event: 'hitl_approval',
        run_id: hitlRequest.run_id,
        thread_id: threadId,
        action: 'accept',
      }),
      threadId
    );
  };

  return (
    <dialog open>
      <h3>Approve Tool Execution</h3>
      <p>Tool: <strong>{hitlRequest.tool_name}</strong></p>
      <pre>{JSON.stringify(hitlRequest.tool_args, null, 2)}</pre>
      <button onClick={handleApprove}>Approve</button>
      <button onClick={() => /* reject */}>Reject</button>
    </dialog>
  );
}
```

### Advanced Patterns

#### A. Custom Event Handlers

```typescript
// Extend useAGUIEventHandler for custom logic
export function useCustomEventHandler(threadId: string) {
  const { handleEvent } = useAGUIEventHandler(threadId);

  // Wrapper for additional processing
  const handleCustomEvent = (event: AGUIEvent) => {
    // Pre-processing
    if (event.event === 'on_chat_model_stream') {
      recordTokenTiming();  // Track token rate
    }

    // Call standard handler
    handleEvent(event);

    // Post-processing
    if (event.event === 'on_chat_model_stream') {
      updateStreamingUI();
    }
  };

  // Override WebSocket event handler
  useWebSocket({ onEvent: handleCustomEvent });

  return { handleCustomEvent };
}
```

#### B. Connection Status UI

```typescript
// components/ConnectionStatus.tsx
export function ConnectionStatus() {
  const { connectionStatus, error } = useWebSocket();

  const statusIcon = {
    connecting: '⏳',
    connected: '✅',
    disconnected: '⏹️',
    reconnecting: '🔄',
    error: '❌',
  };

  return (
    <div className={`status ${connectionStatus}`}>
      {statusIcon[connectionStatus]} {connectionStatus}
      {error && <span className="error">{error.message}</span>}
    </div>
  );
}
```

#### C. Retry Logic

```typescript
// Send message with automatic retry
export function useSendWithRetry() {
  const { sendMessage, isConnected } = useWebSocket();

  const sendWithRetry = async (
    message: string,
    threadId: string,
    maxRetries = 3
  ) => {
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        if (!isConnected) {
          await delay(1000 * Math.pow(2, attempt));  // Backoff
        }

        sendMessage(message, threadId);
        return;
      } catch (error) {
        attempt++;
        if (attempt >= maxRetries) throw error;
      }
    }
  };

  return { sendWithRetry };
}
```

---

## Troubleshooting

### Connection Issues

#### Problem: "WebSocket connection failed"

**Symptoms:**
- `connection error` status
- No events received
- Browser console: `WebSocket connection error`

**Checklist:**
1. Backend running: `curl http://localhost:8000/health`
2. WebSocket endpoint accessible: Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. CORS headers: Backend allows WebSocket origin
4. Firewall: Port 8000 not blocked
5. Network: Not behind restrictive proxy

**Solutions:**
```typescript
// 1. Check API URL
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
console.log('Using API:', apiUrl);

// 2. Validate WebSocket URL conversion
const wsUrl = apiUrl.replace(/^http/, 'ws');
console.log('WebSocket URL:', wsUrl);

// 3. Check connection error
const { error } = useWebSocket();
if (error) {
  console.error('WebSocket error:', error.message);
}
```

#### Problem: "Connection timeout after 30s"

**Symptoms:**
- Connection hangs for 30 seconds then fails
- Agent is processing but no response

**Root Cause:** Agent initialization takes >30s (cold start)

**Solution:** Increase timeout in `useWebSocket.ts`:

```typescript
// Issue 49 fix: Connection timeout increased to 30s
const CONNECTION_TIMEOUT = 30000;  // 30 seconds
```

This allows for:
- Cold start: 8-10 seconds
- Agent initialization: 5-10 seconds
- Buffer: 10-12 seconds

For longer operations, adjust or monitor progress with `processing_started` event.

#### Problem: "Connection established but no events"

**Symptoms:**
- WebSocket shows `connected`
- Send message but no response
- No errors in console

**Checklist:**
1. Message format valid: Must have `type`, `message`, `thread_id`
2. Thread ID exists: Use consistent thread ID
3. Backend logs: Check server for errors
4. Message not empty: Validation requires min 1 character

**Solution:**
```typescript
// Validate message before sending
if (!message.trim()) {
  console.error('Message cannot be empty');
  return;
}

if (!threadId.trim()) {
  console.error('Thread ID required');
  return;
}

sendMessage(message, threadId);
```

### Event Handling Issues

#### Problem: "Unknown event type" errors

**Symptoms:**
- Console errors: `Unknown event type: X`
- UI doesn't update
- Events not processed

**Root Cause:** Custom backend events not filtered before AG-UI handler

**Solution:** Ensure filtering in `useWebSocket.ts`:

```typescript
// Filter custom backend events
const customEvents = ['connection_established', 'processing_started'];

if (customEvents.includes(data.event)) {
  console.log('Custom event:', data.event);
  return;  // Don't pass to AG-UI handler
}

// Only pass standard AG-UI events
if (onEventRef.current) {
  onEventRef.current(data);
}
```

**To Add New Custom Events:**
1. Define in backend (send via WebSocket)
2. Add event name to `customEvents` array
3. Log for debugging (optional)
4. Never pass to AG-UI handler

#### Problem: "Messages not appearing in real-time"

**Symptoms:**
- All tokens arrive at once after response complete
- UI doesn't stream tokens incrementally

**Root Cause:** Not using `on_chat_model_stream` events

**Solution:** Ensure `useAGUIEventHandler` processes stream events:

```typescript
// handleChatModelStream handles on_chat_model_stream events
const handleChatModelStream = (event: TextMessageContentEvent) => {
  const token = event.data.chunk.content || '';

  // Update message with accumulated content
  streamingContentRef.current += token;
  updateMessage(threadId, messageId, {
    content: streamingContentRef.current,
  });
};
```

**Verify:**
- Backend using `astream_events()` not `astream()`
- Events being sent per-token from backend
- Frontend consuming `on_chat_model_stream` events

#### Problem: "Tool calls not showing"

**Symptoms:**
- Tool execution happening but not visible in UI
- No tool call list appears

**Root Cause:** Missing tool call event handling

**Solution:** Check `useAGUIEventHandler` processes tool events:

```typescript
// Handle on_tool_start
case 'on_tool_start':
  addToolCall(threadId, {
    id: event.run_id,
    name: event.name || 'unknown',
    args: typeof event.input === 'object' ? event.input : {},
    status: 'running',
  });
  break;

// Handle on_tool_end
case 'on_tool_end':
  updateToolCall(threadId, event.run_id, {
    status: 'completed',
    result: event.output,
  });
  break;
```

### State Management Issues

#### Problem: "State updates not reflecting in UI"

**Symptoms:**
- Events received but UI doesn't update
- Messages appear but don't update
- Zustand devtools show state changes but UI frozen

**Root Cause:** Component not subscribed to state slice

**Solution:** Use Zustand selector hooks:

```typescript
// ✅ Correct: Subscribe to specific slice
const messages = useAgentState(
  (state) => state.threads[threadId]?.messages || []
);

// ✅ Correct: Subscribe to thread
const thread = useAgentState(
  (state) => state.threads[threadId]
);

// ❌ Incorrect: Subscribes to entire store (causes extra re-renders)
const entireState = useAgentState();
const messages = entireState.threads[threadId]?.messages;
```

#### Problem: "Too many re-renders"

**Symptoms:**
- React warning: "Too many re-renders"
- UI becomes sluggish
- Browser tab CPU usage high

**Root Cause:** useWebSocket callbacks in dependency arrays

**Solution:** Use refs for callbacks (already implemented):

```typescript
// HIGH-1 fix: Callback refs prevent infinite loops
const onEventRef = useRef(onEvent);
const onErrorRef = useRef(onError);

useEffect(() => {
  onEventRef.current = onEvent;
  onErrorRef.current = onError;
}, [onEvent, onError]);

// Use refs in callbacks (don't include in deps)
const handleMessage = () => {
  if (onEventRef.current) {
    onEventRef.current(data);  // Use ref, not callback
  }
};
```

### Performance Issues

#### Problem: "Slow token streaming (< 3 tokens/sec)"

**Symptoms:**
- Tokens appear slowly (>333ms per token)
- UI feels laggy
- Network tab shows no latency

**Root Cause:**
- Agent processing slow
- Serialization overhead
- UI rendering lag

**Investigation Steps:**
1. Check backend performance: Enable debug logging
2. Monitor WebSocket traffic: DevTools → Network
3. Profile React rendering: React DevTools Profiler
4. Check LangSmith for bottlenecks

**Metrics to Track:**
```
Time to First Token (TTFT):  < 5s (target), 8s (acceptable cold start)
Token Rate:                   > 5 tokens/sec
Connection Latency:          < 100ms
Total Response Time:         < 30s
```

#### Problem: "Memory leaks during long sessions"

**Symptoms:**
- Browser memory usage grows over time
- UI becomes sluggish after many exchanges
- Chrome DevTools shows growing heap size

**Root Cause:** Message history accumulating without limit

**Solution:** Implement message cleanup:

```typescript
// Limit messages per thread
const maxMessages = 100;

const addMessage = (threadId: string, message: Message) => {
  set((state) => {
    const thread = state.threads[threadId];
    const messages = [
      ...thread.messages,
      message,
    ].slice(-maxMessages);  // Keep last 100 messages

    return {
      threads: {
        ...state.threads,
        [threadId]: { ...thread, messages },
      },
    };
  });
};

// Or implement pagination
const older = useRef<Message[]>([]);
const loadOlderMessages = () => {
  // Load messages from session storage
};
```

---

## Testing

### Manual Testing Checklist

#### 1. Connection Tests

```bash
# Start backend
poetry run uvicorn backend.deep_agent.api.app:app --reload

# Open browser to http://localhost:3000/chat
# Check Connection Status indicator

# ✅ Status should show "connected"
# ✅ No errors in browser console
# ✅ DevTools Network tab shows ws connection
```

#### 2. Message Sending

```bash
# In browser console
# (assumes useWebSocket hook is active)

const { sendMessage } = useWebSocket();
sendMessage('Hello agent!', 'test-thread-1');

# ✅ Message accepted (no error)
# ✅ Server logs show message received
# ✅ processing_started event appears (check console)
```

#### 3. Token Streaming

```bash
# Send message that generates response
sendMessage('Tell me a short joke', 'test-thread-1');

# Observe tokens appearing in real-time:
# "Why" → "Why did" → "Why did the" → ...

# ✅ Tokens appear incrementally (not all at once)
# ✅ Each on_chat_model_stream event is separate
# ✅ Response completes within 30 seconds
```

#### 4. Event Processing

```bash
# In browser console, add debugging
useAGUIEventHandler = (threadId) => {
  const handleEvent = (event) => {
    console.log('Event:', event.event, event);
    // Original handler logic
  };
  return { handleEvent };
};

# ✅ Events logged to console
# ✅ on_chat_model_stream events for tokens
# ✅ on_chain_start / on_chain_end logged
# ✅ Messages update in UI as they stream
```

#### 5. Error Handling

```bash
# Test various error conditions

# Empty message
sendMessage('', 'test-thread-1');
# ✅ Error: "Message cannot be empty"

# Invalid thread ID
sendMessage('Hello', '');
# ✅ Error: "Thread ID is required"

# Very long message (>10000 chars)
sendMessage('A'.repeat(10001), 'test-thread-1');
# ✅ Error: "Message too long"

# Disconnect backend
# ✅ Error: "WebSocket connection error"
# ✅ Auto-reconnect attempts with backoff
# ✅ Reconnect succeeds when backend restarts
```

#### 6. HITL Workflow

```bash
# Send message that triggers HITL
sendMessage('Create a file at /etc/passwd', 'test-thread-1');

# ✅ hitl_request event received
# ✅ HITL approval dialog appears
# ✅ Can approve, reject, or edit
# ✅ Approval sent back to server
# ✅ Agent continues or halts based on response
```

### Automated Testing

#### Unit Tests: useWebSocket Hook

```typescript
// frontend/hooks/__tests__/useWebSocket.test.ts
describe('useWebSocket', () => {
  it('connects on mount', () => {
    const { result } = renderHook(() => useWebSocket());
    expect(result.current.connectionStatus).toBe('connecting');
    // Wait for connection
    expect(result.current.connectionStatus).toBe('connected');
  });

  it('sends message with validation', () => {
    const { result } = renderHook(() => useWebSocket());

    // Valid message
    result.current.sendMessage('Hello', 'thread-1');

    // Empty message error
    expect(() => {
      result.current.sendMessage('', 'thread-1');
    }).toThrow('Message cannot be empty');
  });

  it('reconnects on disconnection', async () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.connectionStatus).toBe('connected');

    // Simulate disconnection
    result.current.connectionStatus = 'disconnected';

    // Wait for reconnection
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    });
  });
});
```

#### Integration Tests: Event Handling

```typescript
// frontend/hooks/__tests__/useAGUIEventHandler.test.ts
describe('useAGUIEventHandler', () => {
  it('adds message on on_chat_model_stream', () => {
    const { result } = renderHook(() => {
      useAGUIEventHandler('thread-1');
      return useAgentState((s) => s.threads['thread-1']?.messages);
    });

    // Simulate event
    act(() => {
      const event: TextMessageContentEvent = {
        event: 'on_chat_model_stream',
        run_id: 'run-1',
        data: { chunk: { content: 'Hello' } },
      };
      result.current.handleEvent(event);
    });

    // Verify message added
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('Hello');
  });

  it('updates message on subsequent tokens', () => {
    // Simulate multiple stream events
    // Verify message content accumulates correctly
  });

  it('handles on_tool_start events', () => {
    // Verify tool call added to store
  });

  it('handles hitl_request events', () => {
    // Verify HITL approval dialog shown
  });
});
```

#### E2E Tests: Full Workflow

```bash
# tests/e2e/test_websocket_streaming.py
def test_complete_chat_workflow():
    """Test complete chat → response → HITL workflow"""

    # 1. Connect client
    ws = create_test_websocket()
    assert ws.connected

    # 2. Send message
    ws.send_json({
        'type': 'chat',
        'message': 'List my files',
        'thread_id': 'e2e-test-1'
    })

    # 3. Receive processing_started (custom event)
    event = ws.receive_json(timeout=1)
    assert event['event'] == 'processing_started'

    # 4. Receive on_chain_start
    event = ws.receive_json(timeout=1)
    assert event['event'] == 'on_chain_start'

    # 5. Receive token stream events
    tokens = []
    while True:
        event = ws.receive_json(timeout=1)
        if event['event'] == 'on_chat_model_stream':
            tokens.append(event['data']['chunk']['content'])
        elif event['event'] == 'on_chat_model_end':
            break

    assert len(tokens) > 0

    # 6. Verify complete response
    response = ''.join(tokens)
    assert len(response) > 0

    ws.close()
```

---

## Best Practices

### 1. Always Filter Custom Events

```typescript
// ✅ CORRECT
const customEvents = ['processing_started', 'connection_established'];
if (customEvents.includes(data.event)) {
  handleCustomEvent(data);
  return;  // Don't pass to AG-UI handler
}

// ❌ WRONG
// Passing custom events to AG-UI handler causes "unknown event" errors
if (onEvent) onEvent(data);
```

### 2. Use Selector Hooks for State

```typescript
// ✅ CORRECT - Subscribes to specific slice
const messages = useAgentState(state =>
  state.threads[threadId]?.messages || []
);

// ❌ WRONG - Subscribes to entire store
const { threads } = useAgentState();
const messages = threads[threadId]?.messages;
```

### 3. Handle Connection Status

```typescript
// ✅ CORRECT - Check status before sending
const { sendMessage, isConnected } = useWebSocket();

if (!isConnected) {
  console.warn('Not connected');
  return;
}

sendMessage(message, threadId);

// ❌ WRONG - Send without checking
sendMessage(message, threadId);  // May fail silently
```

### 4. Validate Input Before Sending

```typescript
// ✅ CORRECT - Validate before send
if (!message?.trim()) {
  setError('Message cannot be empty');
  return;
}

if (!threadId?.trim()) {
  setError('Thread ID required');
  return;
}

if (message.length > 10000) {
  setError('Message too long');
  return;
}

sendMessage(message, threadId);

// ❌ WRONG - Let server reject
sendMessage(userInput, userThreadId);
```

### 5. Handle Errors Gracefully

```typescript
// ✅ CORRECT - Show error to user
const { error } = useWebSocket();

useEffect(() => {
  if (error) {
    showNotification('Connection error: ' + error.message);
  }
}, [error]);

// ❌ WRONG - Silent failures
// Error exists but user doesn't know about it
```

### 6. Clean Up on Unmount

```typescript
// ✅ CORRECT - useWebSocket handles cleanup
useEffect(() => {
  return () => {
    disconnect();  // Clean up connection
  };
}, []);

// ❌ WRONG - Connection hangs
// Component unmounts but WebSocket stays open
```

### 7. Avoid Creating Multiple Connections

```typescript
// ✅ CORRECT - Single hook in root component
export function App() {
  const { handleEvent } = useAGUIEventHandler(threadId);
  return <ChatUI />;
}

// ❌ WRONG - Multiple instances create multiple connections
function Component1() {
  const { sendMessage: send1 } = useWebSocket();  // Connection 1
}

function Component2() {
  const { sendMessage: send2 } = useWebSocket();  // Connection 2
}
```

### 8. Log Events for Debugging

```typescript
// ✅ CORRECT - Conditional logging
const DEBUG = process.env.NODE_ENV === 'development';

const handleEvent = (event: AGUIEvent) => {
  if (DEBUG) {
    console.log('[AG-UI]', event.event, event);
  }
  // Handle event
};

// ❌ WRONG - Logs in production
console.log('Event:', event);  // Performance impact
```

### 9. Handle Rate Limiting

```typescript
// ✅ CORRECT - Client-side rate limiting
const SEND_RATE_LIMIT = 10;  // messages
const SEND_RATE_WINDOW = 60000;  // 60 seconds

const sendMessage = (message: string) => {
  if (isRateLimited()) {
    showError('Too many messages, please wait');
    return;
  }
  // Send message
};

// ❌ WRONG - Spam the server
for (let i = 0; i < 100; i++) {
  sendMessage('test');
}
```

### 10. Monitor Connection Health

```typescript
// ✅ CORRECT - Display connection status
<ConnectionStatus />

// ✅ CORRECT - Track metrics
const trackMetric = (metric: string, value: number) => {
  // Send to analytics
};

trackMetric('ttft_ms', timeToFirstToken);
trackMetric('token_rate', tokensPerSecond);

// ❌ WRONG - Ignore connection issues
// Silent failures lead to poor UX
```

---

## Reference

### Files

- **Backend:** `/backend/deep_agent/api/v1/websocket.py` - WebSocket endpoint implementation
- **Frontend Hook:** `/frontend/hooks/useWebSocket.ts` - Connection management
- **Event Handler:** `/frontend/hooks/useAGUIEventHandler.ts` - Event processing
- **State Store:** `/frontend/hooks/useAgentState.ts` - Zustand state management
- **Types:** `/frontend/types/ag-ui.ts` - Event type definitions

### Key Commits

- `abd5df3` - Fix streaming with `astream_events()`
- `f34ab29` - Configure stream_mode in LangGraph config
- `95caa3b` - WebSocket investigation and cleanup

### Related Documentation

- AG-UI Protocol: https://docs.ag-ui.com/sdk/python/core/overview
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- Zustand State Management: https://github.com/pmndrs/zustand
- React Hooks: https://react.dev/reference/react

### Testing Resources

- Manual test script: `/scripts/test_websocket_streaming.py`
- Test results: `/docs/manual_websocket_test_results.md`
- Test files: `/tests/integration/test_api_endpoints/test_websocket.py`
- UI tests: `/tests/ui/test_websocket_connection.py`

---

## Quick Troubleshooting Summary

| Issue | Solution |
|-------|----------|
| No connection | Check API URL, backend running, firewall |
| No events | Verify message format, check server logs |
| Unknown event errors | Filter custom events before AG-UI handler |
| Slow streaming | Check TTFT, token rate, browser profiling |
| State not updating | Use Zustand selector hooks |
| Too many re-renders | Use refs for callbacks in useWebSocket |
| HITL not working | Verify hitl_request events received |
| Memory leaks | Implement message cleanup, pagination |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial WebSocket architecture documentation |

Last updated: 2025-10-29
