/**
 * AG-UI Protocol Event Types
 *
 * Type definitions for WebSocket events following the AG-UI Protocol.
 * These types match the backend event streaming format.
 */

/**
 * Base event structure for all AG-UI events
 */
export interface BaseEvent {
  event: string;
  name?: string;
  run_id?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

/**
 * Lifecycle Events
 */

export interface RunStartedEvent extends BaseEvent {
  event: 'on_chain_start' | 'on_llm_start';
  name: string;
  run_id: string;
  parent_run_id?: string;
  tags: string[];
  metadata: Record<string, any>;
}

export interface RunFinishedEvent extends BaseEvent {
  event: 'on_chain_end' | 'on_llm_end';
  run_id: string;
  outputs?: Record<string, any>;
}

export interface RunErrorEvent extends BaseEvent {
  event: 'on_chain_error' | 'on_llm_error';
  run_id: string;
  error: {
    message: string;
    type: string;
    stack?: string;
  };
}

/**
 * LangChain Error Event (on_error)
 *
 * Emitted by LangChain when errors occur during agent execution.
 * Different structure from RunErrorEvent - error can be in data.error
 */
export interface OnErrorEvent extends BaseEvent {
  event: 'on_error';
  run_id?: string;
  data?: {
    error?: string | { message: string; type?: string; stack?: string };
    error_type?: string;
    request_id?: string;
  };
  metadata?: Record<string, any>;
}

export interface StepStartedEvent extends BaseEvent {
  event: 'on_tool_start' | 'on_retriever_start';
  name: string;
  run_id: string;
  parent_run_id: string;
  tags: string[];
  metadata: Record<string, any>;
  input?: string | Record<string, any>;
}

export interface StepFinishedEvent extends BaseEvent {
  event: 'on_tool_end' | 'on_retriever_end';
  run_id: string;
  output?: string | Record<string, any>;
}

/**
 * Message Streaming Events
 */

export interface TextMessageStartEvent extends BaseEvent {
  event: 'on_chat_model_start';
  name: string;
  run_id: string;
  parent_run_id?: string;
  tags: string[];
  metadata: Record<string, any>;
  messages?: Array<{
    role: string;
    content: string;
  }>;
}

export interface TextMessageContentEvent extends BaseEvent {
  event: 'on_chat_model_stream';
  run_id: string;
  data: {
    chunk: {
      content: string;
      type?: 'text' | 'tool_use';
      id?: string;
      name?: string;
    };
  };
}

export interface TextMessageEndEvent extends BaseEvent {
  event: 'on_chat_model_end';
  run_id: string;
  outputs?: {
    generations?: Array<{
      message: {
        role: string;
        content: string;
      };
    }>;
  };
}

/**
 * Tool Call Events
 */

export interface ToolCallStartEvent extends BaseEvent {
  event: 'on_tool_start';
  name: string;
  run_id: string;
  parent_run_id: string;
  tags: string[];
  metadata: Record<string, any>;
}

export interface ToolCallArgsEvent extends BaseEvent {
  event: 'on_tool_start';
  run_id: string;
  input: string | Record<string, any>;
  serialized?: {
    name: string;
    description?: string;
  };
}

export interface ToolCallEndEvent extends BaseEvent {
  event: 'on_tool_end';
  run_id: string;
  name?: string;
}

export interface ToolCallResultEvent extends BaseEvent {
  event: 'on_tool_end';
  run_id: string;
  output: string | Record<string, any>;
}

/**
 * HITL (Human-in-the-Loop) Events
 */

export interface HITLRequestEvent extends BaseEvent {
  event: 'hitl_request';
  run_id: string;
  thread_id: string;
  data: {
    tool_name: string;
    tool_args: Record<string, any>;
    reason?: string;
  };
}

export interface HITLApprovalEvent extends BaseEvent {
  event: 'hitl_approval';
  run_id: string;
  thread_id: string;
  action: 'accept' | 'respond' | 'edit';
  response_text?: string;
  tool_edits?: Record<string, any>;
}

/**
 * Error Events
 */

export interface ErrorEvent extends BaseEvent {
  event: 'error';
  error: {
    message: string;
    type: string;
    code?: string;
  };
}

/**
 * Transformed Events (EventTransformer)
 *
 * These events are created by the backend EventTransformer to decouple
 * the frontend from LangGraph's event schema. They map LangGraph events
 * to UI-friendly formats.
 *
 * See: backend/deep_agent/services/event_transformer.py
 */

export interface OnStepEvent extends BaseEvent {
  event: 'on_step';
  data: {
    id: string;
    name: string;
    status: 'running' | 'completed';
    started_at: string | null;
    completed_at: string | null;
    metadata: Record<string, any>;
  };
  metadata?: Record<string, any>;
}

export interface OnToolCallEvent extends BaseEvent {
  event: 'on_tool_call';
  data: {
    id: string;
    name: string;
    args: Record<string, any>;
    result: any;
    status: 'running' | 'completed';
    started_at: string | null;
    completed_at: string | null;
    error: string | null;
  };
  metadata?: Record<string, any>;
}

/**
 * Heartbeat Events
 *
 * Sent every 5 seconds during long-running agent operations to keep
 * the WebSocket connection alive and provide status updates.
 *
 * See: backend/deep_agent/services/agent_service.py
 */

export interface HeartbeatEvent extends BaseEvent {
  event: 'heartbeat';
  data: {
    status: string;
    message: string;
    heartbeat_number: number;
    elapsed_seconds: number;
  };
  metadata?: Record<string, any>;
}

/**
 * Union type of all AG-UI events
 */
export type AGUIEvent =
  | RunStartedEvent
  | RunFinishedEvent
  | RunErrorEvent
  | OnErrorEvent
  | StepStartedEvent
  | StepFinishedEvent
  | TextMessageStartEvent
  | TextMessageContentEvent
  | TextMessageEndEvent
  | ToolCallStartEvent
  | ToolCallArgsEvent
  | ToolCallEndEvent
  | ToolCallResultEvent
  | HITLRequestEvent
  | HITLApprovalEvent
  | ErrorEvent
  | OnStepEvent
  | OnToolCallEvent
  | HeartbeatEvent;

/**
 * WebSocket message types (client → server)
 */

export interface WebSocketMessage {
  type: 'chat';
  message: string;
  thread_id: string;
  metadata?: Record<string, any>;
}

/**
 * WebSocket connection status
 */
export type ConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'error';
