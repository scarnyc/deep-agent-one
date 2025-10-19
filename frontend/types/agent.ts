/**
 * Agent State Types
 *
 * Type definitions for agent conversation state, tool calls,
 * and HITL (Human-in-the-Loop) workflows.
 */

/**
 * Message role types
 */
export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

/**
 * Agent execution status
 */
export type AgentStatus =
  | 'idle'
  | 'running'
  | 'waiting_for_approval' // HITL state
  | 'completed'
  | 'error';

/**
 * Message in conversation history
 */
export interface AgentMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  tool_calls?: ToolCall[];
  metadata?: Record<string, any>;
}

/**
 * Tool call status
 */
export type ToolCallStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'error';

/**
 * Tool call information
 */
export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, any>;
  result?: string | Record<string, any>;
  status: ToolCallStatus;
  started_at?: string;
  completed_at?: string;
  error?: {
    message: string;
    type: string;
  };
}

/**
 * HITL approval action types
 */
export type HITLAction = 'accept' | 'respond' | 'edit';

/**
 * HITL request awaiting user approval
 */
export interface HITLRequest {
  run_id: string;
  thread_id: string;
  tool_name: string;
  tool_args: Record<string, any>;
  reason?: string;
  requested_at: string;
}

/**
 * HITL approval response
 */
export interface HITLApprovalRequest {
  run_id: string;
  thread_id: string;
  action: HITLAction;
  response_text?: string; // For 'respond' action
  tool_edits?: Record<string, any>; // For 'edit' action
}

/**
 * Agent run information
 */
export interface AgentRunInfo {
  run_id: string;
  thread_id: string;
  status: 'running' | 'completed' | 'error';
  started_at: string;
  completed_at?: string | null;
  metadata?: Record<string, any>;
}

/**
 * Step/subtask in agent execution
 */
export interface AgentStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  started_at?: string;
  completed_at?: string;
  metadata?: Record<string, any>;
}

/**
 * Complete conversation thread state
 */
export interface ConversationThread {
  thread_id: string;
  messages: AgentMessage[];
  tool_calls: ToolCall[];
  hitl_request?: HITLRequest;
  agent_status: AgentStatus;
  current_step?: AgentStep;
  steps: AgentStep[];
  created_at: string;
  updated_at: string;
}

/**
 * Agent state store (Zustand)
 */
export interface AgentState {
  // Current conversation threads (keyed by thread_id)
  threads: Record<string, ConversationThread>;

  // Active thread ID
  active_thread_id: string | null;

  // Actions
  setActiveThread: (thread_id: string) => void;
  createThread: (thread_id: string) => void;
  addMessage: (thread_id: string, message: Omit<AgentMessage, 'id' | 'timestamp'>) => void;
  updateMessage: (thread_id: string, message_id: string, updates: Partial<AgentMessage>) => void;
  addToolCall: (thread_id: string, tool_call: ToolCall) => void;
  updateToolCall: (thread_id: string, tool_call_id: string, updates: Partial<ToolCall>) => void;
  setHITLRequest: (thread_id: string, request: HITLRequest | undefined) => void;
  setAgentStatus: (thread_id: string, status: AgentStatus) => void;
  addStep: (thread_id: string, step: AgentStep) => void;
  updateStep: (thread_id: string, step_id: string, updates: Partial<AgentStep>) => void;
  clearThread: (thread_id: string) => void;

  // Selectors (computed values)
  getActiveThread: () => ConversationThread | null;
  getPendingHITL: (thread_id: string) => HITLRequest | undefined;
  getMessagesByThread: (thread_id: string) => AgentMessage[];
}
