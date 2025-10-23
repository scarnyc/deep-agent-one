/**
 * Structured Logger for Frontend (Phase 0)
 *
 * Provides structured logging with consistent format across the frontend application.
 * In production, logs can be sent to monitoring services like LangSmith or Sentry.
 *
 * Features:
 * - Structured JSON logging
 * - Environment-aware (dev vs prod)
 * - Type-safe context objects
 * - Integration-ready for monitoring services
 *
 * Usage:
 * ```typescript
 * import { logger } from '@/lib/logger';
 *
 * logger.info('User action', { userId: '123', action: 'click' });
 * logger.error('API failure', { endpoint: '/api/chat', status: 500 });
 * ```
 */

/**
 * Log levels
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Log context - additional metadata for log entries
 */
export interface LogContext {
  [key: string]: any;
}

/**
 * Structured log entry
 */
interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  environment: string;
  context?: LogContext;
}

/**
 * Logger class for structured logging
 */
class Logger {
  /**
   * Internal logging method
   */
  private log(level: LogLevel, message: string, context?: LogContext): void {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      environment: process.env.NEXT_PUBLIC_ENV || 'development',
      ...(context && { context }),
    };

    // In production, send to monitoring service
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // TODO Phase 1: Send to LangSmith or Sentry
      // sendToMonitoringService(logEntry);
    }

    // Console output (pretty in dev, JSON in prod)
    const logMethod = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;

    if (process.env.NODE_ENV === 'development') {
      // Pretty logging for development
      logMethod(`[${level.toUpperCase()}] ${message}`, context || '');
    } else {
      // JSON logging for production
      logMethod(JSON.stringify(logEntry));
    }
  }

  /**
   * Log informational message
   */
  info(message: string, context?: LogContext): void {
    this.log('info', message, context);
  }

  /**
   * Log error message
   */
  error(message: string, context?: LogContext): void {
    this.log('error', message, context);
  }

  /**
   * Log warning message
   */
  warn(message: string, context?: LogContext): void {
    this.log('warn', message, context);
  }

  /**
   * Log debug message (only in development)
   */
  debug(message: string, context?: LogContext): void {
    if (process.env.NODE_ENV === 'development') {
      this.log('debug', message, context);
    }
  }

  /**
   * Create a child logger with default context
   * Useful for adding consistent context to all logs in a component
   */
  child(defaultContext: LogContext): Logger {
    const childLogger = new Logger();
    const originalLog = childLogger.log.bind(childLogger);

    childLogger.log = (level: LogLevel, message: string, context?: LogContext) => {
      originalLog(level, message, { ...defaultContext, ...context });
    };

    return childLogger;
  }
}

/**
 * Global logger instance
 */
export const logger = new Logger();

/**
 * Helper to log errors with stack traces
 */
export function logError(error: unknown, context?: LogContext): void {
  if (error instanceof Error) {
    logger.error(error.message, {
      ...context,
      stack: error.stack,
      name: error.name,
    });
  } else {
    logger.error('Unknown error', {
      ...context,
      error: String(error),
    });
  }
}

/**
 * Helper to create performance logs
 */
export function logPerformance(operation: string, durationMs: number, context?: LogContext): void {
  logger.info(`Performance: ${operation}`, {
    ...context,
    durationMs,
    operation,
  });
}

/**
 * Helper to create user interaction logs
 */
export function logUserAction(action: string, context?: LogContext): void {
  logger.info(`User action: ${action}`, {
    ...context,
    action,
    userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
  });
}
