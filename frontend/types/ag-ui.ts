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
 * Union type of all AG-UI events
 */
export type AGUIEvent =
  | RunStartedEvent
  | RunFinishedEvent
  | RunErrorEvent
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
  | ErrorEvent;

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
