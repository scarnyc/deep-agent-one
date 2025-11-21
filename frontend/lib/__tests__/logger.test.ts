/**
 * Unit Tests for Structured Logger (Phase 0)
 *
 * Tests structured logging functionality with mocked console methods,
 * environment variables, and timestamps for deterministic testing.
 *
 * Coverage target: 95%+
 * Test count: 15+ tests
 */

import { logger, logError, logPerformance, logUserAction } from '../logger';

describe('Logger', () => {
  // Spy on console methods
  let consoleLogSpy: jest.SpyInstance;
  let consoleErrorSpy: jest.SpyInstance;
  let consoleWarnSpy: jest.SpyInstance;

  // Store original environment
  const originalEnv = process.env.NODE_ENV;
  const originalPublicEnv = process.env.NEXT_PUBLIC_ENV;

  beforeEach(() => {
    // Mock console methods
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

    // Mock fixed timestamp for deterministic tests
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-01T00:00:00.000Z'));

    // Set default development environment (for pretty logging)
    process.env.NODE_ENV = 'development';
    process.env.NEXT_PUBLIC_ENV = 'development';
  });

  afterEach(() => {
    // Restore mocks
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
    jest.useRealTimers();

    // Restore environment
    process.env.NODE_ENV = originalEnv;
    process.env.NEXT_PUBLIC_ENV = originalPublicEnv;
  });

  describe('info()', () => {
    it('should log with info level', () => {
      // Arrange
      const message = 'Test info message';
      const context = { userId: '123' };

      // Act
      logger.info(message, context);

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[INFO] Test info message',
        context
      );
    });

    it('should log without context', () => {
      // Arrange
      const message = 'Simple info message';

      // Act
      logger.info(message);

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      expect(consoleLogSpy).toHaveBeenCalledWith('[INFO] Simple info message', '');
    });
  });

  describe('error()', () => {
    it('should log with error level', () => {
      // Arrange
      const message = 'Test error message';
      const context = { errorCode: 500 };

      // Act
      logger.error(message, context);

      // Assert
      expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ERROR] Test error message',
        context
      );
    });
  });

  describe('warn()', () => {
    it('should log with warn level', () => {
      // Arrange
      const message = 'Test warning message';
      const context = { warning: 'deprecated' };

      // Act
      logger.warn(message, context);

      // Assert
      expect(consoleWarnSpy).toHaveBeenCalledTimes(1);
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[WARN] Test warning message',
        context
      );
    });
  });

  describe('debug()', () => {
    it('should log in development environment', () => {
      // Arrange
      process.env.NODE_ENV = 'development';
      const message = 'Debug message';
      const context = { debugInfo: 'test' };

      // Act
      logger.debug(message, context);

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[DEBUG] Debug message',
        context
      );
    });

    it('should NOT log in production environment', () => {
      // Arrange
      process.env.NODE_ENV = 'production';
      const message = 'Debug message';

      // Act
      logger.debug(message);

      // Assert
      expect(consoleLogSpy).not.toHaveBeenCalled();
      expect(consoleErrorSpy).not.toHaveBeenCalled();
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });

    it('should NOT log in non-development environment', () => {
      // Arrange
      process.env.NODE_ENV = 'staging';
      const message = 'Debug message';

      // Act
      logger.debug(message);

      // Assert
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });
  });

  describe('Production logging', () => {
    beforeEach(() => {
      process.env.NODE_ENV = 'production';
      process.env.NEXT_PUBLIC_ENV = 'production';
    });

    it('should log JSON in production', () => {
      // Arrange
      const message = 'Production log';
      const context = { key: 'value' };

      // Act
      logger.info(message, context);

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      const loggedData = consoleLogSpy.mock.calls[0][0];
      const parsed = JSON.parse(loggedData);

      expect(parsed).toEqual({
        timestamp: '2025-01-01T00:00:00.000Z',
        level: 'info',
        message: 'Production log',
        environment: 'production',
        context: { key: 'value' },
      });
    });

    it('should log JSON without context in production', () => {
      // Arrange
      const message = 'Production log no context';

      // Act
      logger.info(message);

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      const loggedData = consoleLogSpy.mock.calls[0][0];
      const parsed = JSON.parse(loggedData);

      expect(parsed).toEqual({
        timestamp: '2025-01-01T00:00:00.000Z',
        level: 'info',
        message: 'Production log no context',
        environment: 'production',
      });
      expect(parsed).not.toHaveProperty('context');
    });
  });

  describe('child()', () => {
    it('should create logger with default context', () => {
      // Arrange
      const defaultContext = { component: 'ChatInterface' };
      const childLogger = logger.child(defaultContext);

      // Act
      childLogger.info('Child log', { action: 'click' });

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[INFO] Child log',
        {
          component: 'ChatInterface',
          action: 'click',
        }
      );
    });

    it('should merge contexts when both default and call context provided', () => {
      // Arrange
      const defaultContext = { component: 'ChatInterface', version: '1.0' };
      const childLogger = logger.child(defaultContext);

      // Act
      childLogger.error('Child error', { error: 'timeout', version: '2.0' });

      // Assert
      expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ERROR] Child error',
        {
          component: 'ChatInterface',
          version: '2.0', // Call context overwrites default
          error: 'timeout',
        }
      );
    });

    it('should work without additional context in child logger', () => {
      // Arrange
      const defaultContext = { component: 'ToolDisplay' };
      const childLogger = logger.child(defaultContext);

      // Act
      childLogger.info('No additional context');

      // Assert
      expect(consoleLogSpy).toHaveBeenCalledTimes(1);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[INFO] No additional context',
        defaultContext
      );
    });
  });
});

describe('logError()', () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-01T00:00:00.000Z'));
    process.env.NODE_ENV = 'development';
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    jest.useRealTimers();
  });

  it('should handle Error objects with stack traces', () => {
    // Arrange
    const error = new Error('Test error');
    const context = { userId: '123' };

    // Act
    logError(error, context);

    // Assert
    expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
    const loggedCall = consoleErrorSpy.mock.calls[0];

    expect(loggedCall[0]).toBe('[ERROR] Test error');
    expect(loggedCall[1]).toMatchObject({
      userId: '123',
      name: 'Error',
    });
    expect(loggedCall[1]).toHaveProperty('stack');
    expect(loggedCall[1].stack).toContain('Error: Test error');
  });

  it('should handle non-Error values', () => {
    // Arrange
    const error = 'String error message';
    const context = { source: 'api' };

    // Act
    logError(error, context);

    // Assert
    expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      '[ERROR] Unknown error',
      {
        source: 'api',
        error: 'String error message',
      }
    );
  });

  it('should handle null/undefined errors', () => {
    // Arrange
    const error = null;

    // Act
    logError(error);

    // Assert
    expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      '[ERROR] Unknown error',
      {
        error: 'null',
      }
    );
  });

  it('should handle errors without context', () => {
    // Arrange
    const error = new Error('No context error');

    // Act
    logError(error);

    // Assert
    expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
    const loggedCall = consoleErrorSpy.mock.calls[0];

    expect(loggedCall[0]).toBe('[ERROR] No context error');
    expect(loggedCall[1]).toHaveProperty('stack');
    expect(loggedCall[1]).toHaveProperty('name', 'Error');
  });
});

describe('logPerformance()', () => {
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-01T00:00:00.000Z'));
    process.env.NODE_ENV = 'development';
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    jest.useRealTimers();
  });

  it('should log with durationMs', () => {
    // Arrange
    const operation = 'API call';
    const durationMs = 1234;
    const context = { endpoint: '/api/chat' };

    // Act
    logPerformance(operation, durationMs, context);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    expect(consoleLogSpy).toHaveBeenCalledWith(
      '[INFO] Performance: API call',
      {
        endpoint: '/api/chat',
        durationMs: 1234,
        operation: 'API call',
      }
    );
  });

  it('should log without additional context', () => {
    // Arrange
    const operation = 'Component render';
    const durationMs = 45;

    // Act
    logPerformance(operation, durationMs);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    expect(consoleLogSpy).toHaveBeenCalledWith(
      '[INFO] Performance: Component render',
      {
        durationMs: 45,
        operation: 'Component render',
      }
    );
  });
});

describe('logUserAction()', () => {
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-01T00:00:00.000Z'));
    process.env.NODE_ENV = 'development';
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    jest.useRealTimers();
  });

  it('should include userAgent from window.navigator', () => {
    // Arrange
    const mockUserAgent = 'Mozilla/5.0 (Test Browser)';
    Object.defineProperty(window.navigator, 'userAgent', {
      value: mockUserAgent,
      writable: true,
      configurable: true,
    });

    const action = 'button_click';
    const context = { buttonId: 'submit' };

    // Act
    logUserAction(action, context);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    expect(consoleLogSpy).toHaveBeenCalledWith(
      '[INFO] User action: button_click',
      {
        buttonId: 'submit',
        action: 'button_click',
        userAgent: mockUserAgent,
      }
    );
  });

  it('should log without additional context', () => {
    // Arrange
    const action = 'page_view';

    // Act
    logUserAction(action);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    const loggedCall = consoleLogSpy.mock.calls[0];

    expect(loggedCall[0]).toBe('[INFO] User action: page_view');
    expect(loggedCall[1]).toHaveProperty('action', 'page_view');
    expect(loggedCall[1]).toHaveProperty('userAgent');
  });
});

describe('Edge Cases', () => {
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-01T00:00:00.000Z'));
    process.env.NODE_ENV = 'development';
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    jest.useRealTimers();
  });

  it('should handle empty string message', () => {
    // Arrange
    const message = '';

    // Act
    logger.info(message);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    expect(consoleLogSpy).toHaveBeenCalledWith('[INFO] ', '');
  });

  it('should handle context with nested objects', () => {
    // Arrange
    const message = 'Complex context';
    const context = {
      user: { id: '123', name: 'Test' },
      metadata: { timestamp: 1234567890 },
    };

    // Act
    logger.info(message, context);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    expect(consoleLogSpy).toHaveBeenCalledWith('[INFO] Complex context', context);
  });

  it('should handle missing NEXT_PUBLIC_ENV variable', () => {
    // Arrange
    delete process.env.NEXT_PUBLIC_ENV;
    process.env.NODE_ENV = 'production';
    const message = 'No public env';

    // Act
    logger.info(message);

    // Assert
    expect(consoleLogSpy).toHaveBeenCalledTimes(1);
    const loggedData = consoleLogSpy.mock.calls[0][0];
    const parsed = JSON.parse(loggedData);

    expect(parsed.environment).toBe('development'); // Fallback
  });
});
