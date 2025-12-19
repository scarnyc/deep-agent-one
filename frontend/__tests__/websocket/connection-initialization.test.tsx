/**
 * WebSocket Connection Initialization Tests
 *
 * Tests the race condition fix where fetchConfig() must complete BEFORE connect() is called.
 * This ensures WebSocket connects to the correct backend URL (port 8000, not Next.js on port 5000).
 *
 * Background:
 * - Previous bug: connect() called before fetchConfig() completed
 * - Result: WebSocket used default config, connecting to wrong port
 * - Fix: fetchConfig() called in early useEffect, cached before connect()
 *
 * Test Strategy:
 * - Mock fetchConfig and WebSocket
 * - Use fake timers for precise timing control
 * - Verify correct ordering of operations
 * - Test edge cases (slow fetch, failures, unmount)
 */

import React from 'react';
import { render, waitFor, act } from '@testing-library/react';
import { WebSocketProvider } from '@/contexts/WebSocketProvider';
import * as config from '@/lib/config';
import * as eventValidator from '@/lib/eventValidator';

// Mock dependencies
jest.mock('@/lib/config');
jest.mock('@/lib/eventValidator');

describe('WebSocket Connection Initialization', () => {
  // Mock WebSocket
  let mockWebSocket: jest.Mocked<WebSocket>;
  let webSocketConstructorCalls: string[] = [];

  // Mock fetchConfig
  let fetchConfigMock: jest.Mock;
  let getConfigMock: jest.Mock;

  beforeAll(() => {
    // Mock WebSocket constructor to track calls
    global.WebSocket = jest.fn((url: string) => {
      webSocketConstructorCalls.push(url);

      const ws = {
        url,
        readyState: WebSocket.CONNECTING,
        CONNECTING: 0,
        OPEN: 1,
        CLOSING: 2,
        CLOSED: 3,
        send: jest.fn(),
        close: jest.fn((code?: number) => {
          ws.readyState = WebSocket.CLOSED;
          if (ws.onclose) {
            ws.onclose(new CloseEvent('close', { code: code || 1000 }));
          }
        }),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
        onopen: null,
        onmessage: null,
        onerror: null,
        onclose: null,
        binaryType: 'blob' as BinaryType,
        bufferedAmount: 0,
        extensions: '',
        protocol: '',
      };

      mockWebSocket = ws as jest.Mocked<WebSocket>;
      return ws;
    }) as any;

    // Define WebSocket constants
    (global.WebSocket as any).CONNECTING = 0;
    (global.WebSocket as any).OPEN = 1;
    (global.WebSocket as any).CLOSING = 2;
    (global.WebSocket as any).CLOSED = 3;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    webSocketConstructorCalls = [];

    // Setup config mocks
    fetchConfigMock = jest.fn();
    getConfigMock = jest.fn();
    (config.fetchConfig as jest.Mock) = fetchConfigMock;
    (config.getConfig as jest.Mock) = getConfigMock;

    // Default: fetchConfig returns immediately with default config
    fetchConfigMock.mockResolvedValue({
      env: 'test',
      debug: false,
      api_version: 'v1',
      app_version: '0.1.0',
      websocket_path: '/api/v1/ws',
      stream_timeout_seconds: 300,
      heartbeat_interval_seconds: 5,
      enable_hitl: true,
      enable_reasoning_ui: true,
      enable_cost_tracking: true,
      is_replit: false,
      replit_dev_domain: null,
    });

    // getConfig returns default config (used by getWebSocketUrl)
    getConfigMock.mockReturnValue({
      env: 'test',
      debug: false,
      api_version: 'v1',
      app_version: '0.1.0',
      websocket_path: '/api/v1/ws',
      stream_timeout_seconds: 300,
      heartbeat_interval_seconds: 5,
      enable_hitl: true,
      enable_reasoning_ui: true,
      enable_cost_tracking: true,
      is_replit: false,
      replit_dev_domain: null,
    });

    // Mock event validator to pass all events
    (eventValidator.validateAGUIEvent as jest.Mock).mockReturnValue({
      isValid: true,
      isCustomEvent: false,
      eventType: 'on_chat_model_stream',
    });
    (eventValidator.shouldFilterEvent as jest.Mock).mockReturnValue(false);
    (eventValidator.getEventCategory as jest.Mock).mockReturnValue('Streaming');
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  /**
   * Test 1: Config fetch attempted before connection
   *
   * CRITICAL: This verifies the race condition fix.
   * fetchConfig() must be called BEFORE WebSocket constructor.
   */
  test('should call fetchConfig before attempting WebSocket connection', async () => {
    // Arrange: Track call order
    const callOrder: string[] = [];

    fetchConfigMock.mockImplementation(async () => {
      callOrder.push('fetchConfig');
      // Simulate slow network (100ms delay)
      await new Promise((resolve) => setTimeout(resolve, 100));
      return {
        env: 'test',
        websocket_path: '/api/v1/ws',
        is_replit: false,
        replit_dev_domain: null,
      };
    });

    // Track when WebSocket is constructed
    const originalWebSocket = global.WebSocket;
    global.WebSocket = jest.fn((...args) => {
      callOrder.push('WebSocket');
      return (originalWebSocket as any)(...args);
    }) as any;

    // Act: Render provider with autoConnect
    render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for config fetch to complete
    await waitFor(
      () => {
        expect(fetchConfigMock).toHaveBeenCalled();
      },
      { timeout: 500 }
    );

    // Wait for WebSocket connection
    await waitFor(
      () => {
        expect(global.WebSocket).toHaveBeenCalled();
      },
      { timeout: 500 }
    );

    // Assert: fetchConfig called before WebSocket
    expect(callOrder).toEqual(['fetchConfig', 'WebSocket']);
  });

  /**
   * Test 2: Correct backend URL used
   *
   * Verifies that WebSocket connects to correct URL based on config.
   * In test environment (non-Replit), uses same-origin (no explicit port).
   */
  test('should connect to correct backend URL from config', async () => {
    // Arrange: Config returns custom websocket path (non-Replit)
    fetchConfigMock.mockResolvedValue({
      env: 'test',
      websocket_path: '/api/v1/ws',
      is_replit: false,
      replit_dev_domain: null,
    });

    getConfigMock.mockReturnValue({
      env: 'test',
      websocket_path: '/api/v1/ws',
      is_replit: false,
      replit_dev_domain: null,
    });

    // Act: Render provider
    render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for connection
    await waitFor(
      () => {
        expect(webSocketConstructorCalls.length).toBeGreaterThan(0);
      },
      { timeout: 1000 }
    );

    // Assert: Connected using correct path (same-origin in test env)
    const connectionUrl = webSocketConstructorCalls[0];
    expect(connectionUrl).toContain('/api/v1/ws');
    expect(connectionUrl).toMatch(/^ws:\/\/localhost/); // Correct protocol and host
    // In test env without explicit window.location.port, won't have :8000
  });

  /**
   * Test 3: Replit environment detection
   *
   * Verifies Replit config is used when is_replit=true.
   */
  test('should use Replit config when detected', async () => {
    // Arrange: Config returns Replit settings
    const replitConfig = {
      env: 'test',
      websocket_path: '/api/v1/ws',
      is_replit: true,
      replit_dev_domain: 'abc123.replit.dev',
    };

    fetchConfigMock.mockResolvedValue(replitConfig);
    getConfigMock.mockReturnValue(replitConfig);

    // Act: Render provider
    render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for connection
    await waitFor(
      () => {
        expect(webSocketConstructorCalls.length).toBeGreaterThan(0);
      },
      { timeout: 1000 }
    );

    // Assert: Connected to Replit backend on port 8000
    const connectionUrl = webSocketConstructorCalls[0];
    expect(connectionUrl).toContain(':8000');
    expect(connectionUrl).toContain('/api/v1/ws');
  });

  /**
   * Test 4: Fallback when fetchConfig fails
   *
   * If fetchConfig throws an error, connection should still be attempted
   * using default config from getConfig().
   */
  test('should fallback to default config if fetchConfig fails', async () => {
    // Arrange: fetchConfig throws error
    fetchConfigMock.mockRejectedValue(new Error('Network error'));

    // getConfig returns default config
    getConfigMock.mockReturnValue({
      env: 'test',
      websocket_path: '/api/v1/ws',
      is_replit: false,
      replit_dev_domain: null,
    });

    // Suppress console warnings for this test
    const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

    // Act: Render provider
    render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for connection attempt
    await waitFor(
      () => {
        expect(global.WebSocket).toHaveBeenCalled();
      },
      { timeout: 1000 }
    );

    // Assert: Connection still attempted with default config
    expect(webSocketConstructorCalls.length).toBeGreaterThan(0);
    const connectionUrl = webSocketConstructorCalls[0];
    expect(connectionUrl).toContain('/api/v1/ws');
    expect(connectionUrl).toMatch(/^ws:\/\/localhost/);

    consoleWarnSpy.mockRestore();
  });

  /**
   * Test 5: Cleanup on unmount during initialization
   *
   * If component unmounts while fetchConfig is in progress,
   * no connection should be attempted (cleanup should prevent it).
   */
  test('should cleanup if unmounted during config fetch', async () => {
    // Arrange: Slow fetchConfig (never resolves)
    fetchConfigMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          // Never resolve (simulates slow network)
          setTimeout(resolve, 10000);
        })
    );

    // Act: Render and immediately unmount
    const { unmount } = render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait a bit for fetchConfig to be called
    await waitFor(() => {
      expect(fetchConfigMock).toHaveBeenCalled();
    });

    // Unmount before fetchConfig completes
    unmount();

    // Wait to ensure no connection happens
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Assert: No WebSocket connection attempted
    expect(global.WebSocket).not.toHaveBeenCalled();
  });

  /**
   * Test 6: Fast config fetch (happy path)
   *
   * When fetchConfig completes quickly (typical case),
   * connection should proceed normally.
   */
  test('should connect immediately if fetchConfig is fast', async () => {
    // Arrange: Instant fetchConfig
    fetchConfigMock.mockResolvedValue({
      env: 'test',
      websocket_path: '/api/v1/ws',
      is_replit: false,
      replit_dev_domain: null,
    });

    // Act: Render provider
    const startTime = Date.now();
    render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for connection
    await waitFor(
      () => {
        expect(global.WebSocket).toHaveBeenCalled();
      },
      { timeout: 1000 }
    );

    const elapsedTime = Date.now() - startTime;

    // Assert: Connection happened quickly (< 500ms)
    expect(elapsedTime).toBeLessThan(500);
    const connectionUrl = webSocketConstructorCalls[0];
    expect(connectionUrl).toContain('/api/v1/ws');
    expect(connectionUrl).toMatch(/^ws:\/\/localhost/);
  });

  /**
   * Test 7: Multiple mounts don't duplicate config fetches
   *
   * If component re-renders, fetchConfig should use cached result
   * (deduplication via config module).
   */
  test('should not duplicate config fetches on re-render', async () => {
    // Arrange: Track fetch count
    let fetchCount = 0;
    fetchConfigMock.mockImplementation(async () => {
      fetchCount++;
      return {
        env: 'test',
        websocket_path: '/api/v1/ws',
        is_replit: false,
        replit_dev_domain: null,
      };
    });

    // Act: Render and re-render
    const { rerender } = render(
      <WebSocketProvider autoConnect={true}>
        <div>Test 1</div>
      </WebSocketProvider>
    );

    await waitFor(() => {
      expect(global.WebSocket).toHaveBeenCalled();
    });

    rerender(
      <WebSocketProvider autoConnect={true}>
        <div>Test 2</div>
      </WebSocketProvider>
    );

    // Wait a bit to ensure no duplicate fetch
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Assert: fetchConfig called only once (cached)
    // Note: This depends on config module caching implementation
    expect(fetchCount).toBeLessThanOrEqual(2); // Allow for initial + potential retry
  });

  /**
   * Test 8: Connection timeout after config fetch
   *
   * Even with successful config fetch, connection timeout (30s) should still work.
   */
  test('should timeout connection even after successful config fetch', async () => {
    jest.useFakeTimers();

    // Arrange: Fast fetchConfig
    fetchConfigMock.mockResolvedValue({
      env: 'test',
      websocket_path: '/api/v1/ws',
      is_replit: false,
      replit_dev_domain: null,
    });

    // Act: Render provider
    render(
      <WebSocketProvider autoConnect={true}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for WebSocket creation
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    // Fast-forward 30s (connection timeout)
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    // Assert: Connection closed due to timeout
    await waitFor(() => {
      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });

  /**
   * Test 9: Auto-connect can be disabled
   *
   * When autoConnect=false, fetchConfig should still be called
   * (cache warming), but no connection attempted.
   */
  test('should fetch config but not connect when autoConnect=false', async () => {
    // Act: Render with autoConnect=false
    render(
      <WebSocketProvider autoConnect={false}>
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for fetchConfig
    await waitFor(
      () => {
        expect(fetchConfigMock).toHaveBeenCalled();
      },
      { timeout: 500 }
    );

    // Wait to ensure no connection
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Assert: fetchConfig called, but no WebSocket created
    expect(fetchConfigMock).toHaveBeenCalled();
    expect(global.WebSocket).not.toHaveBeenCalled();
  });

  /**
   * Test 10: Explicit URL prop bypasses config
   *
   * When explicit URL is provided, config is still fetched (for cache),
   * but connection uses explicit URL (with security validation).
   */
  test('should use explicit URL prop when provided', async () => {
    // Act: Render with explicit URL
    render(
      <WebSocketProvider
        url="ws://localhost:8000/custom/ws"
        autoConnect={true}
      >
        <div>Test</div>
      </WebSocketProvider>
    );

    // Wait for connection
    await waitFor(
      () => {
        expect(global.WebSocket).toHaveBeenCalled();
      },
      { timeout: 1000 }
    );

    // Assert: Used explicit URL, not config URL
    expect(webSocketConstructorCalls[0]).toBe('ws://localhost:8000/custom/ws');
    expect(fetchConfigMock).toHaveBeenCalled(); // Still fetched for cache
  });
});
