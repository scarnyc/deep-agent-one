/**
 * ConfigProvider React Context
 *
 * Provides application-wide access to backend configuration via React Context.
 * Fetches config on mount and makes it available to all child components.
 *
 * Key Features:
 * - Automatic config fetch on mount
 * - Loading state management
 * - Error state management
 * - Manual refetch capability
 * - Type-safe context access via useConfig hook
 *
 * Usage:
 * ```tsx
 * <ConfigProvider>
 *   <App />
 * </ConfigProvider>
 * ```
 *
 * In components:
 * ```tsx
 * const { config, isLoading, error, refetch } = useConfig();
 * ```
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { PublicConfig } from '@/lib/config';
import { fetchConfig, DEFAULT_CONFIG } from '@/lib/config';
import { logger } from '@/lib/logger';

/**
 * Config context value
 */
export interface ConfigContextValue {
  /**
   * Current configuration (defaults to DEFAULT_CONFIG until loaded)
   */
  config: PublicConfig;

  /**
   * Loading state (true during initial fetch)
   */
  isLoading: boolean;

  /**
   * Error from last fetch attempt (null if successful)
   */
  error: Error | null;

  /**
   * Manually refetch configuration from backend
   */
  refetch: () => Promise<void>;
}

/**
 * Config context (undefined = not initialized)
 * Exported for use in custom hooks or testing
 */
export const ConfigContext = createContext<ConfigContextValue | undefined>(undefined);

/**
 * Hook to access config context
 *
 * @throws Error if used outside ConfigProvider
 *
 * @example
 * ```tsx
 * const { config, isLoading } = useConfig();
 *
 * if (isLoading) return <div>Loading config...</div>;
 *
 * return <div>Environment: {config.env}</div>;
 * ```
 */
export function useConfig(): ConfigContextValue {
  const context = useContext(ConfigContext);

  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }

  return context;
}

/**
 * ConfigProvider props
 */
export interface ConfigProviderProps {
  children: React.ReactNode;
}

/**
 * ConfigProvider Component
 *
 * Fetches backend configuration on mount and provides it to all child components
 * via React Context. Manages loading and error states.
 *
 * @example
 * ```tsx
 * // In app root (e.g., app/layout.tsx)
 * export default function RootLayout({ children }: { children: React.ReactNode }) {
 *   return (
 *     <html>
 *       <body>
 *         <ConfigProvider>
 *           {children}
 *         </ConfigProvider>
 *       </body>
 *     </html>
 *   );
 * }
 * ```
 */
export function ConfigProvider({ children }: ConfigProviderProps) {
  // State management
  const [config, setConfig] = useState<PublicConfig>(DEFAULT_CONFIG);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Fetch configuration from backend
   * Exported as refetch() in context for manual refresh
   */
  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      logger.debug('ConfigProvider: fetching config');

      const fetchedConfig = await fetchConfig();

      setConfig(fetchedConfig);
      setError(null);

      logger.info('ConfigProvider: config loaded successfully', {
        env: fetchedConfig.env,
        isReplit: fetchedConfig.is_replit,
      });
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));

      setError(error);
      // Keep DEFAULT_CONFIG on error
      setConfig(DEFAULT_CONFIG);

      logger.error('ConfigProvider: failed to load config', {
        error: error.message,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch config on mount
   */
  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // Context value
  const value: ConfigContextValue = {
    config,
    isLoading,
    error,
    refetch: loadConfig,
  };

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
}
