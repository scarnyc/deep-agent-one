/**
 * Unit Tests for Frontend Configuration Utility (Phase 0)
 *
 * Tests configuration fetching, caching, deduplication, and WebSocket URL
 * construction with mocked fetch and window object.
 *
 * Coverage target: 95%+
 * Test count: 12+ tests
 */

import {
  fetchConfig,
  getConfig,
  getWebSocketUrl,
  clearConfigCache,
  DEFAULT_CONFIG,
  type PublicConfig,
} from '../config';

// Mock logger to avoid console spam in tests
jest.mock('../logger', () => ({
  logger: {
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  },
}));

describe('fetchConfig()', () => {
  // Store original fetch and window
  const originalFetch = global.fetch;
  const originalWindow = global.window;

  beforeEach(() => {
    // Clear cache before each test
    clearConfigCache();

    // Mock successful fetch response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            env: 'test',
            debug: true,
            api_version: 'v1',
            app_version: '0.2.0',
            websocket_path: '/api/v1/ws',
            stream_timeout_seconds: 300,
            heartbeat_interval_seconds: 5,
            enable_hitl: true,
            enable_reasoning_ui: true,
            enable_cost_tracking: true,
            is_replit: false,
            replit_dev_domain: null,
          } as PublicConfig),
      } as Response)
    ) as jest.Mock;
  });

  afterEach(() => {
    // Restore original fetch and window
    global.fetch = originalFetch;
    global.window = originalWindow;

    // Clear cache after each test
    clearConfigCache();
  });

  it('should return default config during SSR (no window)', async () => {
    // Arrange: Remove window object
    delete (global as any).window;

    // Act
    const config = await fetchConfig();

    // Assert
    expect(config).toEqual(DEFAULT_CONFIG);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('should fetch config from API on first call', async () => {
    // Arrange: Mock window object
    (global as any).window = { location: { protocol: 'http:' } };

    // Act
    const config = await fetchConfig();

    // Assert
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/config/public',
      expect.objectContaining({
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      })
    );
    expect(config.env).toBe('test');
    expect(config.debug).toBe(true);
  });

  it('should cache result and not refetch on second call', async () => {
    // Arrange: Mock window object
    (global as any).window = { location: { protocol: 'http:' } };

    // Act: Call twice
    const config1 = await fetchConfig();
    const config2 = await fetchConfig();

    // Assert: Only one fetch call
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(config1).toBe(config2); // Same object reference
  });

  it('should deduplicate concurrent requests', async () => {
    // Arrange: Mock window object
    (global as any).window = { location: { protocol: 'http:' } };

    // Act: Call three times concurrently
    const [config1, config2, config3] = await Promise.all([
      fetchConfig(),
      fetchConfig(),
      fetchConfig(),
    ]);

    // Assert: Only one fetch call
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(config1).toBe(config2);
    expect(config2).toBe(config3);
  });

  it('should return default config on fetch failure', async () => {
    // Arrange: Mock window and failed fetch
    (global as any).window = { location: { protocol: 'http:' } };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response)
    ) as jest.Mock;

    // Act
    const config = await fetchConfig();

    // Assert
    expect(config).toEqual(DEFAULT_CONFIG);
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('should return default config on network error', async () => {
    // Arrange: Mock window and network error
    (global as any).window = { location: { protocol: 'http:' } };
    global.fetch = jest.fn(() => Promise.reject(new Error('Network error'))) as jest.Mock;

    // Act
    const config = await fetchConfig();

    // Assert
    expect(config).toEqual(DEFAULT_CONFIG);
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('should use NEXT_PUBLIC_API_URL environment variable if set', async () => {
    // Arrange: Mock window and env variable
    (global as any).window = { location: { protocol: 'http:' } };
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com';

    // Act
    await fetchConfig();

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.com/api/v1/config/public',
      expect.any(Object)
    );

    // Cleanup
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('should validate response has required fields', async () => {
    // Arrange: Mock window and invalid response
    (global as any).window = { location: { protocol: 'http:' } };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ invalid: 'response' }),
      } as Response)
    ) as jest.Mock;

    // Act
    const config = await fetchConfig();

    // Assert: Should return default config on validation failure
    expect(config).toEqual(DEFAULT_CONFIG);
  });
});

describe('getWebSocketUrl()', () => {
  const originalFetch = global.fetch;
  const originalWindow = global.window;

  beforeEach(() => {
    clearConfigCache();

    // Mock successful fetch with standard config
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
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
          } as PublicConfig),
      } as Response)
    ) as jest.Mock;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    global.window = originalWindow;
    clearConfigCache();
  });

  it('should construct correct WebSocket URL for standard environment', async () => {
    // Arrange: Mock window with http protocol
    (global as any).window = {
      location: {
        protocol: 'http:',
        hostname: 'localhost',
        host: 'localhost:3000',
      },
    };

    // Act
    const wsUrl = await getWebSocketUrl();

    // Assert
    expect(wsUrl).toBe('ws://localhost:3000/api/v1/ws');
  });

  it('should use wss:// protocol for https:// sites', async () => {
    // Arrange: Mock window with https protocol
    (global as any).window = {
      location: {
        protocol: 'https:',
        hostname: 'example.com',
        host: 'example.com',
      },
    };

    // Act
    const wsUrl = await getWebSocketUrl();

    // Assert
    expect(wsUrl).toBe('wss://example.com/api/v1/ws');
  });

  it('should handle Replit environment with port 8000', async () => {
    // Arrange: Mock Replit config
    clearConfigCache();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            env: 'prod',
            debug: false,
            api_version: 'v1',
            app_version: '0.1.0',
            websocket_path: '/api/v1/ws',
            stream_timeout_seconds: 300,
            heartbeat_interval_seconds: 5,
            enable_hitl: true,
            enable_reasoning_ui: true,
            enable_cost_tracking: true,
            is_replit: true,
            replit_dev_domain: 'abc123.replit.dev',
          } as PublicConfig),
      } as Response)
    ) as jest.Mock;

    (global as any).window = {
      location: {
        protocol: 'https:',
        hostname: 'abc123.replit.dev',
        host: 'abc123.replit.dev',
      },
    };

    // Act
    const wsUrl = await getWebSocketUrl();

    // Assert
    expect(wsUrl).toBe('wss://abc123.replit.dev:8000/api/v1/ws');
  });

  it('should use NEXT_PUBLIC_API_URL in Replit when available', async () => {
    // Arrange: Mock Replit config with API URL
    clearConfigCache();
    process.env.NEXT_PUBLIC_API_URL = 'https://backend.replit.dev';

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            env: 'prod',
            debug: false,
            api_version: 'v1',
            app_version: '0.1.0',
            websocket_path: '/api/v1/ws',
            stream_timeout_seconds: 300,
            heartbeat_interval_seconds: 5,
            enable_hitl: true,
            enable_reasoning_ui: true,
            enable_cost_tracking: true,
            is_replit: true,
            replit_dev_domain: 'abc123.replit.dev',
          } as PublicConfig),
      } as Response)
    ) as jest.Mock;

    (global as any).window = {
      location: {
        protocol: 'https:',
        hostname: 'abc123.replit.dev',
        host: 'abc123.replit.dev',
      },
    };

    // Act
    const wsUrl = await getWebSocketUrl();

    // Assert
    expect(wsUrl).toBe('wss://backend.replit.dev/api/v1/ws');

    // Cleanup
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('should return placeholder during SSR', async () => {
    // Arrange: Remove window object
    delete (global as any).window;

    // Act
    const wsUrl = await getWebSocketUrl();

    // Assert
    expect(wsUrl).toBe('ws://localhost:8000/api/v1/ws');
  });
});

describe('getConfig()', () => {
  const originalFetch = global.fetch;
  const originalWindow = global.window;

  beforeEach(() => {
    clearConfigCache();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    global.window = originalWindow;
    clearConfigCache();
  });

  it('should return default config when cache is empty', () => {
    // Act
    const config = getConfig();

    // Assert
    expect(config).toEqual(DEFAULT_CONFIG);
  });

  it('should return cached config after fetchConfig()', async () => {
    // Arrange: Mock window and fetch
    (global as any).window = { location: { protocol: 'http:' } };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            env: 'staging',
            debug: false,
            api_version: 'v2',
            app_version: '1.0.0',
            websocket_path: '/ws',
            stream_timeout_seconds: 600,
            heartbeat_interval_seconds: 10,
            enable_hitl: false,
            enable_reasoning_ui: false,
            enable_cost_tracking: false,
            is_replit: true,
            replit_dev_domain: 'test.replit.dev',
          } as PublicConfig),
      } as Response)
    ) as jest.Mock;

    // Act: Fetch then get
    await fetchConfig();
    const config = getConfig();

    // Assert
    expect(config.env).toBe('staging');
    expect(config.api_version).toBe('v2');
    expect(config.is_replit).toBe(true);
  });
});

describe('clearConfigCache()', () => {
  const originalFetch = global.fetch;
  const originalWindow = global.window;

  beforeEach(() => {
    clearConfigCache();

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            env: 'test',
            debug: true,
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
          } as PublicConfig),
      } as Response)
    ) as jest.Mock;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    global.window = originalWindow;
    clearConfigCache();
  });

  it('should force refetch after cache clear', async () => {
    // Arrange: Mock window
    (global as any).window = { location: { protocol: 'http:' } };

    // Act: Fetch, clear, fetch again
    await fetchConfig();
    expect(global.fetch).toHaveBeenCalledTimes(1);

    clearConfigCache();
    await fetchConfig();

    // Assert: Two fetch calls total
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('should reset getConfig() to default after clear', async () => {
    // Arrange: Mock window and fetch
    (global as any).window = { location: { protocol: 'http:' } };

    // Act: Fetch, clear, get
    await fetchConfig();
    const configBefore = getConfig();
    expect(configBefore.env).toBe('test');

    clearConfigCache();
    const configAfter = getConfig();

    // Assert: Back to default
    expect(configAfter).toEqual(DEFAULT_CONFIG);
  });
});
