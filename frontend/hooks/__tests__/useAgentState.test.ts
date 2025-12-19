/**
 * Comprehensive Test Suite for useAgentState Zustand Store
 *
 * Tests cover:
 * - Thread management (creation, deletion, activation)
 * - Message operations (add, update, retrieve)
 * - Tool call tracking (add, update, timestamps)
 * - Agent status management
 * - Step/subtask tracking
 * - HITL workflow state
 * - State immutability
 * - Edge cases and error handling
 *
 * Coverage target: 85%+
 */

import { renderHook, act } from '@testing-library/react';
import { useAgentState } from '../useAgentState';
import type { ToolCall, HITLRequest, AgentStep } from '@/types/agent';

// Mock crypto.randomUUID for consistent IDs in tests
let uuidCounter = 0;
const mockUUID = () => `test-id-${++uuidCounter}`;

// Mock Date for consistent timestamps
const mockDate = new Date('2025-01-01T00:00:00.000Z');
const mockISOString = mockDate.toISOString();

// Store original implementations
const originalCrypto = global.crypto;
const _originalDate = global.Date;

describe('useAgentState', () => {
  beforeEach(() => {
    // Reset counter before each test
    uuidCounter = 0;

    // Mock crypto.randomUUID
    global.crypto = {
      ...originalCrypto,
      randomUUID: jest.fn(mockUUID),
    } as any;

    // Mock Date
    jest.spyOn(global, 'Date').mockImplementation((() => mockDate) as any);
    (global.Date as any).now = jest.fn(() => mockDate.getTime());
    (Date.prototype as any).toISOString = jest.fn(() => mockISOString);

    // Reset Zustand store state between tests
    const { setState } = useAgentState;
    setState({ threads: {}, active_thread_id: null });
  });

  afterEach(() => {
    // Restore original implementations
    global.crypto = originalCrypto;
    jest.restoreAllMocks();
  });

  describe('Thread Management', () => {
    it('should initialize with empty state', () => {
      // Arrange & Act
      const { result } = renderHook(() => useAgentState());

      // Assert
      expect(result.current.threads).toEqual({});
      expect(result.current.active_thread_id).toBeNull();
    });

    it('should create thread with correct structure', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());

      // Act
      act(() => {
        result.current.createThread('test-thread-123');
      });

      // Assert
      const thread = result.current.threads['test-thread-123'];
      expect(thread).toBeDefined();
      expect(thread.thread_id).toBe('test-thread-123');
      expect(thread.messages).toEqual([]);
      expect(thread.tool_calls).toEqual([]);
      expect(thread.steps).toEqual([]);
      expect(thread.agent_status).toBe('idle');
      expect(thread.hitl_request).toBeUndefined();
      expect(thread.current_step).toBeUndefined();
      expect(thread.created_at).toBe(mockISOString);
      expect(thread.updated_at).toBe(mockISOString);
    });

    it('should set thread as active by default when created', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());

      // Act
      act(() => {
        result.current.createThread('test-thread-456');
      });

      // Assert
      expect(result.current.active_thread_id).toBe('test-thread-456');
    });

    it('should generate unique thread IDs when creating multiple threads', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());

      // Act
      act(() => {
        result.current.createThread('thread-1');
        result.current.createThread('thread-2');
        result.current.createThread('thread-3');
      });

      // Assert
      expect(Object.keys(result.current.threads)).toEqual(['thread-1', 'thread-2', 'thread-3']);
      expect(result.current.threads['thread-1']).toBeDefined();
      expect(result.current.threads['thread-2']).toBeDefined();
      expect(result.current.threads['thread-3']).toBeDefined();
    });

    it('should update active_thread_id when setActiveThread is called', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-1');
        result.current.createThread('thread-2');
      });

      // Act
      act(() => {
        result.current.setActiveThread('thread-1');
      });

      // Assert
      expect(result.current.active_thread_id).toBe('thread-1');
    });

    it('should return correct active thread via getActiveThread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-active');
      });

      // Act
      const activeThread = result.current.getActiveThread();

      // Assert
      expect(activeThread).toBeDefined();
      expect(activeThread?.thread_id).toBe('thread-active');
    });

    it('should return null from getActiveThread when no active thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());

      // Ensure no active thread is set
      act(() => {
        result.current.setActiveThread('');
      });

      // Reset to null
      const { setState } = useAgentState;
      setState({ active_thread_id: null });

      // Act
      const activeThread = result.current.getActiveThread();

      // Assert
      expect(activeThread).toBeNull();
    });

    it('should clear thread data while preserving thread ID', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-to-clear');
        result.current.addMessage('thread-to-clear', {
          role: 'user',
          content: 'Test message',
        });
        result.current.setAgentStatus('thread-to-clear', 'running');
      });

      // Act
      act(() => {
        result.current.clearThread('thread-to-clear');
      });

      // Assert
      const thread = result.current.threads['thread-to-clear'];
      expect(thread).toBeDefined();
      expect(thread.thread_id).toBe('thread-to-clear');
      expect(thread.messages).toEqual([]);
      expect(thread.agent_status).toBe('idle');
    });
  });

  describe('Message Operations', () => {
    it('should add message to correct thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-messages');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-messages', {
          role: 'user',
          content: 'Hello, agent!',
        });
      });

      // Assert
      const messages = result.current.threads['thread-messages'].messages;
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('Hello, agent!');
      expect(messages[0].role).toBe('user');
    });

    it('should generate unique ID for message', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-ids');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-ids', {
          role: 'user',
          content: 'Message 1',
        });
      });

      // Assert
      const messages = result.current.threads['thread-ids'].messages;
      expect(messages[0].id).toBeDefined();
      expect(typeof messages[0].id).toBe('string');
      expect(messages[0].id.length).toBeGreaterThan(0);

      // Verify uniqueness by adding another message
      act(() => {
        result.current.addMessage('thread-ids', {
          role: 'assistant',
          content: 'Message 2',
        });
      });

      const updatedMessages = result.current.threads['thread-ids'].messages;
      expect(updatedMessages[0].id).not.toBe(updatedMessages[1].id);
    });

    it('should return the generated message ID from addMessage', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-return-id');
      });

      // Act
      let returnedId: string = '';
      act(() => {
        returnedId = result.current.addMessage('thread-return-id', {
          role: 'assistant',
          content: 'Test message',
        });
      });

      // Assert
      expect(returnedId).toBeDefined();
      expect(typeof returnedId).toBe('string');
      expect(returnedId.length).toBeGreaterThan(0);

      // Verify the returned ID matches the message in the store
      const messages = result.current.threads['thread-return-id'].messages;
      expect(messages[0].id).toBe(returnedId);
    });

    it('should support streaming message updates using returned ID (regression test for bug)', () => {
      // Arrange - Simulates the bug where only first token rendered
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-streaming');
      });

      // Act - Simulate streaming tokens like AG-UI event handler does
      let messageId: string = '';

      // First token - create message and capture returned ID
      act(() => {
        messageId = result.current.addMessage('thread-streaming', {
          role: 'assistant',
          content: 'Hello',
          metadata: { streaming: true },
        });
      });

      // Verify first token rendered
      let messages = result.current.threads['thread-streaming'].messages;
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('Hello');
      expect(messages[0].id).toBe(messageId);

      // Subsequent tokens - update using returned ID
      act(() => {
        result.current.updateMessage('thread-streaming', messageId, {
          content: 'Hello!',
        });
      });

      messages = result.current.threads['thread-streaming'].messages;
      expect(messages[0].content).toBe('Hello!');

      act(() => {
        result.current.updateMessage('thread-streaming', messageId, {
          content: 'Hello! How',
        });
      });

      messages = result.current.threads['thread-streaming'].messages;
      expect(messages[0].content).toBe('Hello! How');

      act(() => {
        result.current.updateMessage('thread-streaming', messageId, {
          content: 'Hello! How can I help you today?',
        });
      });

      // Assert - Full message should be present
      messages = result.current.threads['thread-streaming'].messages;
      expect(messages).toHaveLength(1); // Still only one message
      expect(messages[0].content).toBe('Hello! How can I help you today?'); // Full content
      expect(messages[0].id).toBe(messageId); // Same ID throughout

      // Mark streaming complete
      act(() => {
        result.current.updateMessage('thread-streaming', messageId, {
          metadata: { streaming: false, completed: true },
        });
      });

      messages = result.current.threads['thread-streaming'].messages;
      expect(messages[0].metadata?.streaming).toBe(false);
      expect(messages[0].metadata?.completed).toBe(true);
    });

    it('should set ISO timestamp correctly on message', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-timestamp');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-timestamp', {
          role: 'assistant',
          content: 'Response',
        });
      });

      // Assert
      const messages = result.current.threads['thread-timestamp'].messages;
      expect(messages[0].timestamp).toBe(mockISOString);
    });

    it('should handle messages with tool_calls', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-tool-calls');
      });

      const toolCall: ToolCall = {
        id: 'tool-1',
        name: 'web_search',
        args: { query: 'test' },
        status: 'pending',
      };

      // Act
      act(() => {
        result.current.addMessage('thread-tool-calls', {
          role: 'assistant',
          content: 'Searching...',
          tool_calls: [toolCall],
        });
      });

      // Assert
      const messages = result.current.threads['thread-tool-calls'].messages;
      expect(messages[0].tool_calls).toHaveLength(1);
      expect(messages[0].tool_calls?.[0].name).toBe('web_search');
    });

    it('should update existing message', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-update');
        result.current.addMessage('thread-update', {
          role: 'assistant',
          content: 'Original content',
        });
      });

      const messageId = result.current.threads['thread-update'].messages[0].id;

      // Act
      act(() => {
        result.current.updateMessage('thread-update', messageId, {
          content: 'Updated content',
        });
      });

      // Assert
      const messages = result.current.threads['thread-update'].messages;
      expect(messages[0].content).toBe('Updated content');
      expect(messages[0].id).toBe(messageId); // ID should remain the same
    });

    it('should return correct messages via getMessagesByThread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-get-messages');
        result.current.addMessage('thread-get-messages', {
          role: 'user',
          content: 'Message 1',
        });
        result.current.addMessage('thread-get-messages', {
          role: 'assistant',
          content: 'Message 2',
        });
      });

      // Act
      const messages = result.current.getMessagesByThread('thread-get-messages');

      // Assert
      expect(messages).toHaveLength(2);
      expect(messages[0].content).toBe('Message 1');
      expect(messages[1].content).toBe('Message 2');
    });

    it('should return empty array for non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());

      // Act
      const messages = result.current.getMessagesByThread('non-existent');

      // Assert
      expect(messages).toEqual([]);
    });

    it('should not mutate state when adding message to non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.addMessage('non-existent', {
          role: 'user',
          content: 'Test',
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });

    it('should not mutate state when updating message in non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.updateMessage('non-existent', 'msg-id', {
          content: 'Updated',
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });
  });

  describe('Tool Call Tracking', () => {
    it('should add tool call to thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-tools');
      });

      const toolCall: ToolCall = {
        id: 'tool-call-1',
        name: 'file_read',
        args: { path: '/test.txt' },
        status: 'pending',
      };

      // Act
      act(() => {
        result.current.addToolCall('thread-tools', toolCall);
      });

      // Assert
      const tools = result.current.threads['thread-tools'].tool_calls;
      expect(tools).toHaveLength(1);
      expect(tools[0].name).toBe('file_read');
      expect(tools[0].args).toEqual({ path: '/test.txt' });
    });

    it('should update tool call status', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-tool-update');
        result.current.addToolCall('thread-tool-update', {
          id: 'tool-1',
          name: 'web_search',
          args: { query: 'test' },
          status: 'pending',
        });
      });

      // Act
      act(() => {
        result.current.updateToolCall('thread-tool-update', 'tool-1', {
          status: 'completed',
          result: { data: 'search results' },
        });
      });

      // Assert
      const tools = result.current.threads['thread-tool-update'].tool_calls;
      expect(tools[0].status).toBe('completed');
      expect(tools[0].result).toEqual({ data: 'search results' });
    });

    it('should track started_at timestamp for tool calls', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-tool-time');
      });

      const startTime = '2025-01-01T10:00:00.000Z';

      // Act
      act(() => {
        result.current.addToolCall('thread-tool-time', {
          id: 'tool-time-1',
          name: 'test_tool',
          args: {},
          status: 'running',
          started_at: startTime,
        });
      });

      // Assert
      const tools = result.current.threads['thread-tool-time'].tool_calls;
      expect(tools[0].started_at).toBe(startTime);
    });

    it('should track completed_at timestamp for tool calls', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-tool-complete');
        result.current.addToolCall('thread-tool-complete', {
          id: 'tool-complete-1',
          name: 'test_tool',
          args: {},
          status: 'running',
          started_at: '2025-01-01T10:00:00.000Z',
        });
      });

      const completeTime = '2025-01-01T10:00:05.000Z';

      // Act
      act(() => {
        result.current.updateToolCall('thread-tool-complete', 'tool-complete-1', {
          status: 'completed',
          completed_at: completeTime,
        });
      });

      // Assert
      const tools = result.current.threads['thread-tool-complete'].tool_calls;
      expect(tools[0].completed_at).toBe(completeTime);
      expect(tools[0].status).toBe('completed');
    });

    it('should not mutate state when adding tool call to non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.addToolCall('non-existent', {
          id: 'tool-1',
          name: 'test',
          args: {},
          status: 'pending',
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });

    it('should not mutate state when updating tool call in non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.updateToolCall('non-existent', 'tool-1', {
          status: 'completed',
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });
  });

  describe('Agent Status Management', () => {
    it('should set agent status for thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-status');
      });

      // Act
      act(() => {
        result.current.setAgentStatus('thread-status', 'running');
      });

      // Assert
      expect(result.current.threads['thread-status'].agent_status).toBe('running');
    });

    it('should update agent status correctly', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-status-update');
        result.current.setAgentStatus('thread-status-update', 'running');
      });

      // Act
      act(() => {
        result.current.setAgentStatus('thread-status-update', 'completed');
      });

      // Assert
      expect(result.current.threads['thread-status-update'].agent_status).toBe('completed');
    });

    it('should handle waiting_for_approval status (HITL)', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-hitl-status');
      });

      // Act
      act(() => {
        result.current.setAgentStatus('thread-hitl-status', 'waiting_for_approval');
      });

      // Assert
      expect(result.current.threads['thread-hitl-status'].agent_status).toBe('waiting_for_approval');
    });

    it('should not mutate state when setting status for non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.setAgentStatus('non-existent', 'running');
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });
  });

  describe('Step/Subtask Tracking', () => {
    it('should add step to thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-steps');
      });

      const step: AgentStep = {
        id: 'step-1',
        name: 'Planning phase',
        status: 'running',
        started_at: mockISOString,
      };

      // Act
      act(() => {
        result.current.addStep('thread-steps', step);
      });

      // Assert
      const steps = result.current.threads['thread-steps'].steps;
      expect(steps).toHaveLength(1);
      expect(steps[0].name).toBe('Planning phase');
      expect(result.current.threads['thread-steps'].current_step).toEqual(step);
    });

    it('should update existing step', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-step-update');
        result.current.addStep('thread-step-update', {
          id: 'step-1',
          name: 'Research',
          status: 'running',
        });
      });

      // Act
      act(() => {
        result.current.updateStep('thread-step-update', 'step-1', {
          status: 'completed',
          completed_at: '2025-01-01T10:05:00.000Z',
        });
      });

      // Assert
      const steps = result.current.threads['thread-step-update'].steps;
      expect(steps[0].status).toBe('completed');
      expect(steps[0].completed_at).toBe('2025-01-01T10:05:00.000Z');
    });

    it('should update current_step when updating active step', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-current-step');
        result.current.addStep('thread-current-step', {
          id: 'step-active',
          name: 'Active step',
          status: 'running',
        });
      });

      // Act
      act(() => {
        result.current.updateStep('thread-current-step', 'step-active', {
          status: 'completed',
        });
      });

      // Assert
      expect(result.current.threads['thread-current-step'].current_step?.status).toBe('completed');
    });

    it('should not mutate state when adding step to non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.addStep('non-existent', {
          id: 'step-1',
          name: 'Test',
          status: 'pending',
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });

    it('should not mutate state when updating step in non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.updateStep('non-existent', 'step-1', {
          status: 'completed',
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });
  });

  describe('HITL Workflow State', () => {
    it('should set HITL request for thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-hitl');
      });

      const hitlRequest: HITLRequest = {
        run_id: 'run-123',
        thread_id: 'thread-hitl',
        tool_name: 'file_delete',
        tool_args: { path: '/important.txt' },
        reason: 'Requires user approval for deletion',
        requested_at: mockISOString,
      };

      // Act
      act(() => {
        result.current.setHITLRequest('thread-hitl', hitlRequest);
      });

      // Assert
      expect(result.current.threads['thread-hitl'].hitl_request).toEqual(hitlRequest);
    });

    it('should clear HITL request when set to undefined', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-hitl-clear');
        result.current.setHITLRequest('thread-hitl-clear', {
          run_id: 'run-456',
          thread_id: 'thread-hitl-clear',
          tool_name: 'test_tool',
          tool_args: {},
          requested_at: mockISOString,
        });
      });

      // Act
      act(() => {
        result.current.setHITLRequest('thread-hitl-clear', undefined);
      });

      // Assert
      expect(result.current.threads['thread-hitl-clear'].hitl_request).toBeUndefined();
    });

    it('should return pending HITL via getPendingHITL', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-get-hitl');
        result.current.setHITLRequest('thread-get-hitl', {
          run_id: 'run-789',
          thread_id: 'thread-get-hitl',
          tool_name: 'test_tool',
          tool_args: {},
          requested_at: mockISOString,
        });
      });

      // Act
      const pendingHITL = result.current.getPendingHITL('thread-get-hitl');

      // Assert
      expect(pendingHITL).toBeDefined();
      expect(pendingHITL?.run_id).toBe('run-789');
    });

    it('should return undefined when no HITL request pending', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-no-hitl');
      });

      // Act
      const pendingHITL = result.current.getPendingHITL('thread-no-hitl');

      // Assert
      expect(pendingHITL).toBeUndefined();
    });

    it('should not mutate state when setting HITL for non-existent thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      const initialThreads = result.current.threads;

      // Act
      act(() => {
        result.current.setHITLRequest('non-existent', {
          run_id: 'run-1',
          thread_id: 'non-existent',
          tool_name: 'test',
          tool_args: {},
          requested_at: mockISOString,
        });
      });

      // Assert
      expect(result.current.threads).toEqual(initialThreads);
    });
  });

  describe('State Immutability', () => {
    it('should not mutate original state when creating thread', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-immut-1');
      });

      // Deep copy the threads to test immutability
      const originalThreadKeys = Object.keys(result.current.threads);
      const originalThreadCount = originalThreadKeys.length;

      // Act
      act(() => {
        result.current.createThread('thread-immut-2');
      });

      // Assert
      // Original key count should be less than current
      expect(originalThreadCount).toBe(1);
      expect(Object.keys(result.current.threads).length).toBe(2);
      expect(result.current.threads['thread-immut-2']).toBeDefined();
    });

    it('should not mutate original state when adding messages', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-immutable');
      });
      const originalMessages = [...result.current.threads['thread-immutable'].messages];

      // Act
      act(() => {
        result.current.addMessage('thread-immutable', {
          role: 'user',
          content: 'Test',
        });
      });

      // Assert
      expect(originalMessages).toHaveLength(0);
      expect(result.current.threads['thread-immutable'].messages).toHaveLength(1);
    });

    it('should not mutate original state when updating messages', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-update-immutable');
        result.current.addMessage('thread-update-immutable', {
          role: 'user',
          content: 'Original',
        });
      });
      const messageId = result.current.threads['thread-update-immutable'].messages[0].id;
      const originalContent = result.current.threads['thread-update-immutable'].messages[0].content;

      // Act
      act(() => {
        result.current.updateMessage('thread-update-immutable', messageId, {
          content: 'Updated',
        });
      });

      // Assert
      expect(originalContent).toBe('Original');
      expect(result.current.threads['thread-update-immutable'].messages[0].content).toBe('Updated');
    });

    it('should maintain updated_at timestamp when state changes', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-timestamp-check');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-timestamp-check', {
          role: 'user',
          content: 'Test',
        });
      });

      // Assert
      expect(result.current.threads['thread-timestamp-check'].updated_at).toBe(mockISOString);
    });
  });

  describe('UUID Generation', () => {
    it('should use crypto.randomUUID when available', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-uuid');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-uuid', {
          role: 'user',
          content: 'Test',
        });
      });

      // Assert
      const messages = result.current.threads['thread-uuid'].messages;
      expect(messages[0].id).toBeDefined();
      expect(typeof messages[0].id).toBe('string');
      // In mock environment, crypto.randomUUID is available and working
      expect(global.crypto.randomUUID).toBeDefined();
    });

    it('should fallback to timestamp+random when crypto.randomUUID unavailable', () => {
      // Arrange
      const originalCryptoRandomUUID = global.crypto.randomUUID;
      // @ts-ignore - intentionally remove randomUUID
      delete global.crypto.randomUUID;

      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-fallback');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-fallback', {
          role: 'user',
          content: 'Test',
        });
      });

      // Assert
      const messages = result.current.threads['thread-fallback'].messages;
      expect(messages[0].id).toBeDefined();
      expect(typeof messages[0].id).toBe('string');
      expect(messages[0].id).toContain('-'); // Timestamp-random format contains hyphen

      // Restore
      global.crypto.randomUUID = originalCryptoRandomUUID;
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty message content', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-empty-content');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-empty-content', {
          role: 'user',
          content: '',
        });
      });

      // Assert
      const messages = result.current.threads['thread-empty-content'].messages;
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('');
    });

    it('should handle updating non-existent message gracefully', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-no-msg');
      });

      // Act
      act(() => {
        result.current.updateMessage('thread-no-msg', 'non-existent-id', {
          content: 'Updated',
        });
      });

      // Assert
      expect(result.current.threads['thread-no-msg'].messages).toHaveLength(0);
    });

    it('should handle updating non-existent tool call gracefully', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-no-tool');
      });

      // Act
      act(() => {
        result.current.updateToolCall('thread-no-tool', 'non-existent-id', {
          status: 'completed',
        });
      });

      // Assert
      expect(result.current.threads['thread-no-tool'].tool_calls).toHaveLength(0);
    });

    it('should handle clearing non-existent thread gracefully', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());

      // Act
      act(() => {
        result.current.clearThread('non-existent');
      });

      // Assert
      expect(result.current.threads['non-existent']).toBeUndefined();
    });

    it('should handle multiple rapid state updates', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-rapid');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-rapid', { role: 'user', content: 'Msg 1' });
        result.current.addMessage('thread-rapid', { role: 'assistant', content: 'Msg 2' });
        result.current.addMessage('thread-rapid', { role: 'user', content: 'Msg 3' });
        result.current.setAgentStatus('thread-rapid', 'running');
        result.current.setAgentStatus('thread-rapid', 'completed');
      });

      // Assert
      const thread = result.current.threads['thread-rapid'];
      expect(thread.messages).toHaveLength(3);
      expect(thread.agent_status).toBe('completed');
    });

    it('should handle message metadata', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-metadata');
      });

      // Act
      act(() => {
        result.current.addMessage('thread-metadata', {
          role: 'user',
          content: 'Test',
          metadata: {
            custom_field: 'value',
            nested: { data: 123 },
          },
        });
      });

      // Assert
      const messages = result.current.threads['thread-metadata'].messages;
      expect(messages[0].metadata).toEqual({
        custom_field: 'value',
        nested: { data: 123 },
      });
    });

    it('should handle tool call errors', () => {
      // Arrange
      const { result } = renderHook(() => useAgentState());
      act(() => {
        result.current.createThread('thread-tool-error');
        result.current.addToolCall('thread-tool-error', {
          id: 'tool-error-1',
          name: 'failing_tool',
          args: {},
          status: 'running',
        });
      });

      // Act
      act(() => {
        result.current.updateToolCall('thread-tool-error', 'tool-error-1', {
          status: 'error',
          error: {
            message: 'Tool execution failed',
            type: 'ToolExecutionError',
          },
        });
      });

      // Assert
      const tools = result.current.threads['thread-tool-error'].tool_calls;
      expect(tools[0].status).toBe('error');
      expect(tools[0].error?.message).toBe('Tool execution failed');
    });
  });
});
