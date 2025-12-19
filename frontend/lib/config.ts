/**
 * Frontend Configuration Management (Phase 0)
 *
 * Provides centralized access to backend configuration via the /api/v1/config/public endpoint.
 * Implements caching, deduplication, and SSR-safe fallbacks.
 *
 * Key Features:
 * - Fetches public config from backend API
 * - Caches result to minimize API calls
 * - Deduplicates concurrent requests
 * - SSR-safe (handles missing window object)
 * - Type-safe configuration interface
 * - Simplified WebSocket URL construction
 *
 * Usage:
 * ```typescript
 * // Async fetch (recommended)
 * const config = await fetchConfig();
 * const wsUrl = await getWebSocketUrl();
 *
 * // Synchronous access (uses cached or default)
 * const config = getConfig();
 * ```
 */

import { logger } from '@/lib/logger';

/**
 * Detect if running in Replit and get the base domain
 * @returns Replit domain or null if not in Replit
 */
export function detectReplitDomain(): string | null {
  if (typeof window === 'undefined' || !window) return null;
  if (!window.location || !window.location.hostname) return null;

  const hostname = window.location.hostname;

  // Check if hostname matches Replit pattern
  // Pattern: *.replit.dev or *.repl.co
  if (hostname.endsWith('.replit.dev') || hostname.endsWith('.repl.co')) {
    return hostname;
  }

  return null;
}

/**
 * Get the correct API URL for the current environment
 * Automatically detects Replit vs local development.
 *
 * @returns API URL (with protocol)
 */
export function getApiUrl(): string {
  // Check for explicit env var first
  if (process.env.NEXT_PUBLIC_API_URL) {
    // If localhost, return as-is (local development)
    if (process.env.NEXT_PUBLIC_API_URL.includes('localhost')) {
      return process.env.NEXT_PUBLIC_API_URL;
    }
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // SSR Guard: Can't detect Replit without window
  if (typeof window === 'undefined' || !window) {
    return 'http://localhost:8000';
  }

  // Auto-detect Replit
  const replitDomain = detectReplitDomain();
  if (replitDomain) {
    return `https://${replitDomain}`;
  }

  // Fallback to localhost
  return 'http://localhost:8000';
}

/**
 * Public configuration interface
 * Mirrors backend PublicConfigResponse schema
 */
export interface PublicConfig {
  env: string;
  debug: boolean;
  api_version: string;
  app_version: string;
  websocket_path: string;
  stream_timeout_seconds: number;
  heartbeat_interval_seconds: number;
  enable_hitl: boolean;
  enable_reasoning_ui: boolean;
  enable_cost_tracking: boolean;
  is_replit: boolean;
  replit_dev_domain: string | null;
}

/**
 * Default configuration (fallback when API unavailable)
 */
export const DEFAULT_CONFIG: PublicConfig = {
  env: 'development',
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
};

/**
 * Cached configuration (module-level singleton)
 */
let cachedConfig: PublicConfig | null = null;

/**
 * Pending fetch promise (for deduplication)
 */
let pendingFetch: Promise<PublicConfig> | null = null;

/**
 * Fetch public configuration from backend API
 *
 * Features:
 * - Caches result on successful fetch
 * - Deduplicates concurrent requests
 * - Falls back to DEFAULT_CONFIG on error
 * - SSR-safe (returns default during SSR)
 *
 * @returns Promise resolving to PublicConfig
 *
 * @example
 * ```typescript
 * const config = await fetchConfig();
 * console.log(config.enable_hitl); // true
 * ```
 */
export async function fetchConfig(): Promise<PublicConfig> {
  // SSR Guard: Return default config during server-side rendering
  // Check multiple conditions to handle different test/runtime environments
  if (typeof window === 'undefined' || !window || !window.location) {
    logger.debug('fetchConfig: SSR detected, returning default config');
    return DEFAULT_CONFIG;
  }

  // Return cached config if available
  if (cachedConfig) {
    logger.debug('fetchConfig: returning cached config');
    return cachedConfig;
  }

  // Deduplication: Return pending fetch if already in progress
  if (pendingFetch) {
    logger.debug('fetchConfig: deduplicating concurrent request');
    return pendingFetch;
  }

  // Start new fetch
  pendingFetch = (async () => {
    try {
      // Construct API URL (with Replit auto-detection)
      let apiUrl: string;
      if (process.env.NEXT_PUBLIC_API_URL) {
        apiUrl = process.env.NEXT_PUBLIC_API_URL;
      } else {
        // Auto-detect Replit domain
        const replitDomain = detectReplitDomain();
        apiUrl = replitDomain ? `https://${replitDomain}` : 'http://localhost:8000';
      }
      const endpoint = `${apiUrl}/api/v1/config/public`;

      logger.debug('fetchConfig: fetching from', { endpoint });

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Don't cache in browser (we handle caching ourselves)
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error(`Config fetch failed: ${response.status} ${response.statusText}`);
      }

      const config = (await response.json()) as PublicConfig;

      // Validate response has required fields
      if (!config.env || !config.api_version) {
        throw new Error('Invalid config response: missing required fields');
      }

      // Cache successful result
      cachedConfig = config;
      logger.info('fetchConfig: successfully fetched and cached config', { env: config.env });

      return config;
    } catch (error) {
      logger.error('fetchConfig: failed to fetch config, using defaults', {
        error: error instanceof Error ? error.message : String(error),
      });

      // Return default config on error (don't cache errors)
      return DEFAULT_CONFIG;
    } finally {
      // Clear pending fetch promise
      pendingFetch = null;
    }
  })();

  return pendingFetch;
}

/**
 * Get WebSocket URL from configuration
 *
 * Constructs WebSocket URL based on backend configuration, handling:
 * - Protocol conversion (http -> ws, https -> wss)
 * - Replit special case (direct port 8000 connection)
 * - Custom websocket_path from config
 *
 * @returns Promise resolving to WebSocket URL string
 *
 * @example
 * ```typescript
 * const wsUrl = await getWebSocketUrl();
 * // => "ws://localhost:8000/api/v1/ws"
 * // or "ws://abc123.replit.dev:8000/api/v1/ws" (Replit)
 * ```
 */
export async function getWebSocketUrl(): Promise<string> {
  const config = await fetchConfig();

  // SSR Guard: Can't construct WebSocket URL without window
  if (typeof window === 'undefined') {
    logger.warn('getWebSocketUrl: SSR detected, returning placeholder');
    return 'ws://localhost:8000/api/v1/ws';
  }

  // Determine protocol (ws or wss)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname;

  // Replit Special Case: Connect directly to backend on port 8000
  // Next.js rewrites() don't work for WebSocket upgrades
  if (config.is_replit) {
    logger.debug('getWebSocketUrl: Replit environment detected, using port 8000');

    // Priority 1: Use explicit API URL from environment
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (apiUrl && !apiUrl.includes('localhost')) {
      const wsUrl = apiUrl.replace(/^http/, 'ws');
      logger.debug('getWebSocketUrl: using NEXT_PUBLIC_API_URL', { wsUrl });
      return `${wsUrl}${config.websocket_path}`;
    }

    // Priority 2: Construct from current hostname + port 8000
    const wsUrl = `${protocol}//${hostname}:8000${config.websocket_path}`;
    logger.debug('getWebSocketUrl: constructed Replit URL', { wsUrl });
    return wsUrl;
  }

  // Standard case: Use same origin (may be proxied by Next.js)
  const wsUrl = `${protocol}//${window.location.host}${config.websocket_path}`;
  logger.debug('getWebSocketUrl: constructed standard URL', { wsUrl });
  return wsUrl;
}

/**
 * Get cached configuration synchronously
 *
 * Returns cached config if available, otherwise returns DEFAULT_CONFIG.
 * Useful when you need immediate access without async/await.
 *
 * @returns PublicConfig (cached or default)
 *
 * @example
 * ```typescript
 * const config = getConfig();
 * if (config.enable_hitl) {
 *   // Show HITL UI
 * }
 * ```
 */
export function getConfig(): PublicConfig {
  return cachedConfig || DEFAULT_CONFIG;
}

/**
 * Clear configuration cache
 *
 * Forces next fetchConfig() call to re-fetch from backend.
 * Useful for testing or manual refresh scenarios.
 *
 * @example
 * ```typescript
 * clearConfigCache();
 * const freshConfig = await fetchConfig();
 * ```
 */
export function clearConfigCache(): void {
  cachedConfig = null;
  pendingFetch = null;
  logger.debug('clearConfigCache: cache cleared');
}
