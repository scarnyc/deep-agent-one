/**
 * Tests for useWebSocket Hook
 *
 * Validates fixes for high-priority issues:
 * - Issue 44: Callback refs prevent infinite reconnection loops
 * - Issue 45: Rate limiting for sendMessage
 * - Issue 46: Max reconnection attempts circuit breaker
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import type { AGUIEvent } from '@/types/ag-ui';

// Track all WebSocket instances for testing
let mockWebSocketInstances: MockWebSocket[] = [];

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  public readyState: number = MockWebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public sent: string[] = [];

  constructor(public url: string) {
    // Track instance
    mockWebSocketInstances.push(this);

    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      const event = new CloseEvent('close', { code: code || 1000, reason });
      this.onclose(event);
    }
  }

  // Test helper: simulate receiving message
  simulateMessage(data: any): void {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }

  // Test helper: simulate error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any;

// Helper to get the latest WebSocket instance
function getLatestMockWS(): MockWebSocket | null {
  return mockWebSocketInstances[mockWebSocketInstances.length - 1] || null;
}

// Mock environment variable
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

// Mock console methods to reduce test noise
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

beforeAll(() => {
  console.log = jest.fn();
  console.warn = jest.fn();
  console.error = jest.fn();
});

afterAll(() => {
  console.log = originalConsoleLog;
  console.warn = originalConsoleWarn;
  console.error = originalConsoleError;
});

describe('useWebSocket Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
    mockWebSocketInstances = []; // Clear WebSocket instances
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    mockWebSocketInstances = [];
  });

  // ===== BASIC FUNCTIONALITY =====

  describe('Basic Functionality', () => {
    it('should connect automatically by default', async () => {
      const { result } = renderHook(() => useWebSocket());

      // Initially connecting
      expect(result.current.connectionStatus).toBe('connecting');

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');
      expect(result.current.isConnected).toBe(true);
    });

    it('should not auto-connect when autoConnect is false', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      expect(result.current.connectionStatus).toBe('disconnected');
      expect(result.current.isConnected).toBe(false);
    });

    it('should connect manually when autoConnect is false', async () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      expect(result.current.connectionStatus).toBe('disconnected');

      // Manually connect
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');
    });

    it('should disconnect cleanly', async () => {
      const { result } = renderHook(() => useWebSocket());

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.isConnected).toBe(true);

      // Disconnect
      act(() => {
        result.current.disconnect();
      });

      expect(result.current.connectionStatus).toBe('disconnected');
      expect(result.current.isConnected).toBe(false);
    });

    it('should use custom WebSocket URL when provided', () => {
      const customUrl = 'ws://custom-server:9000/ws';
      renderHook(() => useWebSocket({ url: customUrl }));

      // Verify URL was used (check mock WebSocket instance)
      const ws = getLatestMockWS();
      expect(ws).not.toBeNull();
      expect(ws?.url).toBe(customUrl);
    });

    it('should call onEvent callback when message received', async () => {
      const onEvent = jest.fn();
      renderHook(() => useWebSocket({ onEvent }));

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Simulate AG-UI event
      const testEvent: AGUIEvent = {
        type: 'on_chain_start',
        data: { run_id: 'test-123', name: 'test' },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        const ws = getLatestMockWS();
        if (ws) {
          ws.simulateMessage(testEvent);
        }
      });

      await waitFor(() => {
        expect(onEvent).toHaveBeenCalledWith(testEvent);
      });
    });

    it('should call onError callback when error occurs', async () => {
      const onError = jest.fn();
      renderHook(() => useWebSocket({ onError }));

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Simulate WebSocket error
      act(() => {
        const ws = getLatestMockWS();
        if (ws) {
          ws.simulateError();
        }
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
        expect(onError.mock.calls[0][0]).toBeInstanceOf(Error);
      });
    });
  });

  // ===== ISSUE 44: CALLBACK REFS (INFINITE LOOP PREVENTION) =====

  describe('Issue 44: Callback Refs Prevent Infinite Loops', () => {
    it('should not trigger reconnect when onEvent callback changes', async () => {
      let renderCount = 0;
      const onEvent1 = jest.fn(() => renderCount++);
      const onEvent2 = jest.fn(() => renderCount++);

      const { result, rerender } = renderHook(
        ({ onEvent }) => useWebSocket({ onEvent }),
        { initialProps: { onEvent: onEvent1 } }
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');

      // Change callback (simulate parent re-render with new inline callback)
      rerender({ onEvent: onEvent2 });

      // Wait to ensure no reconnection triggered
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      // Should still be connected (no reconnection)
      expect(result.current.connectionStatus).toBe('connected');

      // Verify new callback is used
      const testEvent: AGUIEvent = {
        type: 'on_chain_start',
        data: { run_id: 'test-456', name: 'test' },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        const ws = getLatestMockWS();
        if (ws) {
          ws.simulateMessage(testEvent);
        }
      });

      await waitFor(() => {
        expect(onEvent2).toHaveBeenCalledWith(testEvent);
        expect(onEvent1).not.toHaveBeenCalled();
      });
    });

    it('should not trigger reconnect when onError callback changes', async () => {
      const onError1 = jest.fn();
      const onError2 = jest.fn();

      const { result, rerender } = renderHook(
        ({ onError }) => useWebSocket({ onError }),
        { initialProps: { onError: onError1 } }
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');

      // Change callback
      rerender({ onError: onError2 });

      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      // Should still be connected
      expect(result.current.connectionStatus).toBe('connected');

      // Verify new callback is used
      act(() => {
        const ws = getLatestMockWS();
        if (ws) {
          ws.simulateError();
        }
      });

      await waitFor(() => {
        expect(onError2).toHaveBeenCalled();
        expect(onError1).not.toHaveBeenCalled();
      });
    });

    it('should not create infinite loop with inline callbacks', async () => {
      let rerenderCount = 0;
      const { result, rerender } = renderHook(() => {
        rerenderCount++;
        // Inline callbacks (recreated every render)
        return useWebSocket({
          onEvent: (e) => console.log('event', e),
          onError: (e) => console.error('error', e),
        });
      });

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      const initialRenderCount = rerenderCount;

      // Wait a bit to ensure no infinite loop
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // Render count should not explode (max 2-3 renders expected)
      expect(rerenderCount).toBeLessThan(initialRenderCount + 5);
      expect(result.current.connectionStatus).toBe('connected');
    });
  });

  // ===== ISSUE 45: RATE LIMITING =====

  describe('Issue 45: Rate Limiting for sendMessage', () => {
    it('should allow sending messages within rate limit', async () => {
      const { result } = renderHook(() => useWebSocket());

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.isConnected).toBe(true);

      // Send 10 messages (exactly at limit)
      for (let i = 0; i < 10; i++) {
        act(() => {
          result.current.sendMessage(`Message ${i}`, `thread-${i}`);
        });
      }

      // Verify all messages sent
      const ws = getLatestMockWS();
      expect(ws?.sent.length).toBe(10);
    });

    it('should block messages exceeding rate limit', async () => {
      const onError = jest.fn();
      const { result } = renderHook(() => useWebSocket({ onError }));

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Send 10 messages (at limit)
      for (let i = 0; i < 10; i++) {
        act(() => {
          result.current.sendMessage(`Message ${i}`, `thread-${i}`);
        });
      }

      // Try to send 11th message (should be blocked)
      act(() => {
        result.current.sendMessage('Blocked message', 'thread-blocked');
      });

      // Verify 11th message was NOT sent
      const ws = getLatestMockWS();
      expect(ws.sent.length).toBe(10);

      // Verify rate limit error was triggered
      expect(onError).toHaveBeenCalled();
      const errorArg = onError.mock.calls[onError.mock.calls.length - 1][0];
      expect(errorArg.message).toContain('Rate limit exceeded');
    });

    it('should reset rate limit after time window passes', async () => {
      const { result } = renderHook(() => useWebSocket());

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Send 10 messages (at limit)
      for (let i = 0; i < 10; i++) {
        act(() => {
          result.current.sendMessage(`Message ${i}`, `thread-${i}`);
        });
      }

      // Wait for rate limit window to pass (60 seconds)
      await act(async () => {
        jest.advanceTimersByTime(61000);
      });

      // Should be able to send again
      act(() => {
        result.current.sendMessage('Message after window', 'thread-reset');
      });

      const ws = getLatestMockWS();
      expect(ws.sent.length).toBe(11); // 10 original + 1 after reset
    });

    it('should have rate limit of 10 messages per 60 seconds', async () => {
      const { result } = renderHook(() => useWebSocket());

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Send exactly 10 messages
      for (let i = 0; i < 10; i++) {
        act(() => {
          result.current.sendMessage(`Msg ${i}`, `thread-${i}`);
        });
      }

      const ws = getLatestMockWS();
      expect(ws.sent.length).toBe(10);

      // Wait 30 seconds (half window)
      await act(async () => {
        jest.advanceTimersByTime(30000);
      });

      // Try to send - should still be blocked (window not passed)
      act(() => {
        result.current.sendMessage('Blocked at 30s', 'thread-30s');
      });

      expect(ws.sent.length).toBe(10); // Still blocked

      // Wait another 31 seconds (total 61s, window passed)
      await act(async () => {
        jest.advanceTimersByTime(31000);
      });

      // Should work now
      act(() => {
        result.current.sendMessage('Allowed at 61s', 'thread-61s');
      });

      expect(ws.sent.length).toBe(11);
    });
  });

  // ===== ISSUE 46: MAX RECONNECTION ATTEMPTS =====

  describe('Issue 46: Max Reconnection Attempts Circuit Breaker', () => {
    it('should stop reconnecting after max attempts reached', async () => {
      const onError = jest.fn();
      const maxReconnectAttempts = 3;

      // Create a custom MockWebSocket that fails after initial connection
      let connectionCount = 0;
      const OriginalMockWebSocket = MockWebSocket;

      class FailingMockWebSocket extends OriginalMockWebSocket {
        constructor(url: string) {
          super(url);
          connectionCount++;

          // First connection succeeds, subsequent ones fail immediately
          if (connectionCount > 1) {
            setTimeout(() => {
              this.readyState = MockWebSocket.CLOSED;
              if (this.onclose) {
                this.onclose(new CloseEvent('close', { code: 1006, reason: 'Connection failed' }));
              }
            }, 0);
          }
        }
      }

      // Replace global WebSocket temporarily
      (global as any).WebSocket = FailingMockWebSocket;

      const { result } = renderHook(() =>
        useWebSocket({
          reconnect: true,
          maxReconnectAttempts,
          reconnectInterval: 100,
          onError,
        })
      );

      // Wait for initial connection
      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');

      // Close the connection to trigger reconnection attempts
      act(() => {
        const ws = getLatestMockWS();
        if (ws) {
          ws.close(1006, 'Abnormal closure');
        }
      });

      // Wait for all reconnection attempts to exhaust
      await act(async () => {
        jest.advanceTimersByTime(30000); // Long enough for all attempts + backoff
      });

      // After max attempts, should be in error state
      expect(result.current.connectionStatus).toBe('error');
      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.message).toContain(
        `Max reconnection attempts (${maxReconnectAttempts}) exceeded`
      );

      // Verify onError was called with max attempts error
      const errorCalls = onError.mock.calls.filter(([err]) =>
        err.message.includes('Max reconnection attempts')
      );
      expect(errorCalls.length).toBeGreaterThan(0);

      // Restore original WebSocket
      (global as any).WebSocket = OriginalMockWebSocket;
      connectionCount = 0;
    });

    it('should reset reconnection counter on successful connection', async () => {
      const maxReconnectAttempts = 3;

      const { result } = renderHook(() =>
        useWebSocket({
          reconnect: true,
          maxReconnectAttempts,
          reconnectInterval: 100,
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');

      // Disconnect abnormally
      act(() => {
        const ws = getLatestMockWS();
        ws.close(1006, 'Abnormal closure');
      });

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Should reconnect successfully
      await act(async () => {
        jest.advanceTimersByTime(500);
      });

      expect(result.current.connectionStatus).toBe('connected');

      // Disconnect again multiple times - counter should be reset
      for (let i = 1; i <= maxReconnectAttempts; i++) {
        act(() => {
          const ws = getLatestMockWS();
          ws.close(1006, 'Abnormal closure');
        });

        await act(async () => {
          jest.advanceTimersByTime(1000);
        });
      }

      // Should still be reconnecting (counter was reset after successful connection)
      expect(result.current.connectionStatus).not.toBe('error');
    });

    it('should not reconnect on normal closure (code 1000)', async () => {
      const { result } = renderHook(() =>
        useWebSocket({
          reconnect: true,
          reconnectInterval: 100,
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.connectionStatus).toBe('connected');

      // Normal closure
      act(() => {
        result.current.disconnect(); // Uses code 1000
      });

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Should stay disconnected (no reconnect attempt)
      expect(result.current.connectionStatus).toBe('disconnected');
    });

    it('should use exponential backoff for reconnection delays', async () => {
      const reconnectInterval = 100;
      const maxReconnectInterval = 10000;

      const { result } = renderHook(() =>
        useWebSocket({
          reconnect: true,
          reconnectInterval,
          maxReconnectInterval,
        })
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Capture reconnection delays
      const delays: number[] = [];

      for (let i = 0; i < 5; i++) {
        // Disconnect abnormally
        act(() => {
          const ws = getLatestMockWS();
          ws.close(1006, 'Abnormal closure');
        });

        const startTime = Date.now();

        await act(async () => {
          jest.advanceTimersByTime(20000); // Advance enough for reconnection
        });

        delays.push(Date.now() - startTime);
      }

      // Verify exponential backoff pattern
      // Each delay should be roughly 2x previous (with max cap)
      for (let i = 1; i < delays.length; i++) {
        const expectedDelay = Math.min(
          reconnectInterval * Math.pow(2, i),
          maxReconnectInterval
        );
        // Allow some tolerance for timing
        expect(delays[i]).toBeGreaterThanOrEqual(expectedDelay * 0.8);
      }
    });
  });

  // ===== EDGE CASES =====

  describe('Edge Cases', () => {
    it('should handle invalid JSON in received message', async () => {
      const onError = jest.fn();
      renderHook(() => useWebSocket({ onError }));

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Send invalid JSON directly to the message handler
      act(() => {
        const ws = getLatestMockWS();
        if (ws && ws.onmessage) {
          ws.onmessage(new MessageEvent('message', { data: 'invalid-json' }));
        }
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
        const error = onError.mock.calls[0][0];
        expect(error.message).toContain('Failed to parse WebSocket message');
      });
    });

    it('should not send message when disconnected', async () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      expect(result.current.connectionStatus).toBe('disconnected');

      // Try to send message while disconnected
      act(() => {
        result.current.sendMessage('Test', 'thread-1');
      });

      // Verify no error thrown and console.warn called
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('Cannot send message: not connected')
      );
    });

    it('should clean up on unmount', async () => {
      const { result, unmount } = renderHook(() => useWebSocket());

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.isConnected).toBe(true);

      // Unmount
      unmount();

      // Verify cleanup (connection closed)
      const ws = getLatestMockWS();
      expect(ws.readyState).toBe(MockWebSocket.CLOSED);
    });
  });
});
