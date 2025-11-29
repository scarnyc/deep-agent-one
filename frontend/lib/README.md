# Lib (Utilities)

## Purpose

Utility libraries and helper functions for Deep Agent One frontend.

This directory contains core utilities for AG-UI Protocol integration, WebSocket event handling, structured logging, and general UI helpers.

## Key Files

### Core Utilities

- **`utils.ts`** - General UI utilities (Tailwind CSS class merging)
- **`logger.ts`** - Structured logging with LangSmith integration
- **`eventValidator.ts`** - AG-UI Protocol event validation and type guards
- **`errorEventAdapter.ts`** - Multi-protocol error normalization

### Tests

- **`__tests__/utils.test.ts`** - Unit tests for utils.ts
- **`__tests__/logger.test.ts`** - Unit tests for logger.ts

## Usage

### Class Name Utilities (`utils.ts`)

Merge Tailwind CSS classes with conflict resolution:

```typescript
import { cn } from '@/lib/utils';

// Basic usage
const className = cn('px-4 py-2', 'bg-blue-500');
// => 'px-4 py-2 bg-blue-500'

// Conditional classes
const buttonClass = cn(
  'px-4 py-2',
  'rounded-md',
  isActive && 'bg-blue-500 text-white',
  isDisabled && 'opacity-50 cursor-not-allowed'
);

// Tailwind conflict resolution
const mergedClass = cn('px-4', 'px-8');
// => 'px-8' (later class wins)
```

### Structured Logging (`logger.ts`)

Environment-aware logging with LangSmith integration:

```typescript
import { logger, logError, logPerformance, logUserAction } from '@/lib/logger';

// Basic logging
logger.info('User logged in', { userId: '123', method: 'oauth' });
logger.warn('API latency high', { endpoint: '/api/chat', latency: 2500 });
logger.error('WebSocket disconnected', { reason: 'timeout', duration: 30 });
logger.debug('State updated', { component: 'ChatInterface', state: 'loading' });

// Error logging with stack traces
try {
  await fetchData();
} catch (error) {
  logError(error, { operation: 'fetchData', userId: '123' });
}

// Performance logging
const start = Date.now();
await processData();
logPerformance('Data processing', Date.now() - start, { rows: 1000 });

// User action tracking
logUserAction('Message sent', { messageLength: 250, hasAttachment: false });

// Child logger with default context
const chatLogger = logger.child({ component: 'ChatInterface' });
chatLogger.info('Message sent'); // Automatically includes component: 'ChatInterface'
```

**Output Formats:**

- **Development:** Pretty console logs with colors
  ```
  [INFO] User logged in { userId: '123', method: 'oauth' }
  ```

- **Production:** Structured JSON for monitoring services
  ```json
  {
    "timestamp": "2025-11-12T10:30:00.000Z",
    "level": "info",
    "message": "User logged in",
    "environment": "production",
    "context": { "userId": "123", "method": "oauth" }
  }
  ```

### AG-UI Event Validation (`eventValidator.ts`)

Validate WebSocket events against the AG-UI Protocol specification:

```typescript
import {
  validateAGUIEvent,
  isStandardAGUIEvent,
  isCustomEvent,
  shouldFilterEvent,
  getEventCategory,
  filterCustomEvents,
  // Event type guards
  isLifecycleEvent,
  isStreamingEvent,
  isToolEvent,
  isErrorEvent,
  isHITLEvent,
} from '@/lib/eventValidator';

// Validate single event
const result = validateAGUIEvent({ event: 'on_chat_model_stream', data: {...} });
if (!result.isValid) {
  console.error('Invalid event:', result.error);
}

// Check if standard AG-UI event
isStandardAGUIEvent('on_chat_model_stream') // true
isStandardAGUIEvent('processing_started')   // false

// Check if custom backend event
isCustomEvent('processing_started')       // true
isCustomEvent('on_chat_model_stream')     // false

// Filter custom events before passing to AG-UI handlers
const events = [
  { event: 'on_chat_model_stream', data: {...} },  // kept
  { event: 'processing_started', data: {...} },     // removed
];
const filtered = filterCustomEvents(events);

// Type guards for event categories
if (isStreamingEvent(event.event)) {
  // Handle streaming content
}
if (isToolEvent(event.event)) {
  // Handle tool execution
}
if (isErrorEvent(event.event)) {
  // Handle error
}

// Get event category
getEventCategory('on_chat_model_stream') // "Streaming"
getEventCategory('on_tool_start')        // "Tool"
getEventCategory('processing_started')   // "Custom"
```

**Standard AG-UI Events:**

- **Lifecycle:** `on_chain_start`, `on_chain_end`, `on_llm_start`, `on_llm_end`, `on_chat_model_start`, `on_chat_model_end`
- **Streaming:** `on_chat_model_stream`
- **Tools:** `on_tool_start`, `on_tool_end`
- **HITL:** `hitl_request`, `hitl_approval`
- **Errors:** `on_chain_error`, `on_llm_error`, `error`, `on_error`
- **Retriever:** `on_retriever_start`, `on_retriever_end`

**Custom Backend Events:**

- **Processing:** `processing_started` (cold start notification)
- **Deprecated:** `connection_established` (no longer sent)

### Error Event Normalization (`errorEventAdapter.ts`)

Normalize error events from multiple AI service protocols:

```typescript
import {
  normalizeErrorEvent,
  isErrorEvent,
  getErrorMessage,
  getErrorType,
} from '@/lib/errorEventAdapter';

// Normalize error from any protocol
const normalized = normalizeErrorEvent({
  event: "on_error",
  data: { error: "API timeout", error_type: "TimeoutError" }
});
// Returns: {
//   message: "API timeout",
//   type: "TimeoutError",
//   code: undefined,
//   stack: undefined,
//   run_id: undefined,
//   request_id: undefined
// }

// Check if event is an error
if (isErrorEvent(event)) {
  const message = getErrorMessage(event);
  const type = getErrorType(event);

  toast.error(message);
  logger.error('Agent error', { type, message });
}
```

**Supported Error Formats:**

1. **LangChain Convention:**
   ```json
   {
     "event": "on_error",
     "data": {
       "error": "Connection refused",
       "error_type": "ConnectionError"
     }
   }
   ```

2. **AG-UI Convention:**
   ```json
   {
     "event": "on_chain_error",
     "error": {
       "message": "API key invalid",
       "type": "AuthenticationError"
     }
   }
   ```

3. **Generic Error:**
   ```json
   {
     "event": "error",
     "error": {
       "message": "Rate limit exceeded",
       "type": "RateLimitError",
       "code": "429"
     }
   }
   ```

**Security Features:**

- Automatic HTML/script tag removal (XSS prevention)
- Secret redaction (API keys, tokens, passwords)
- Message length limiting (DoS prevention)
- Stack trace sanitization

## Utility Categories

### UI Utilities

**Class Name Merging:**
- Tailwind CSS class conflict resolution
- Conditional class application
- Type-safe class value handling

### Logging & Observability

**Structured Logging:**
- Environment-aware output format
- Child loggers with default context
- Error logging with stack traces
- Performance tracking
- User action tracking
- LangSmith integration (Phase 1)

### WebSocket & AG-UI Protocol

**Event Validation:**
- AG-UI Protocol compliance checking
- Custom event filtering
- Event category classification
- Type guards for all event types
- Batch validation

**Error Normalization:**
- Multi-protocol error handling
- Consistent error structure
- Security sanitization
- User-friendly error messages

## Architecture Patterns

### Event Filtering Pipeline

```typescript
// WebSocket receives raw events
const rawEvent = await websocket.receive();

// 1. Validate event structure
const validation = validateAGUIEvent(rawEvent);
if (!validation.isValid) {
  logger.error('Invalid event', { error: validation.error });
  return;
}

// 2. Filter custom backend events
if (shouldFilterEvent(rawEvent.event)) {
  // Handle custom event separately
  handleCustomEvent(rawEvent);
  return;
}

// 3. Pass to AG-UI handler
aguiHandler.handleEvent(rawEvent);
```

### Error Handling Flow

```typescript
// WebSocket receives error event
const errorEvent = await websocket.receive();

// 1. Check if error event
if (isErrorEvent(errorEvent)) {
  // 2. Normalize error format
  const normalized = normalizeErrorEvent(errorEvent);

  // 3. Log structured error
  logger.error('Agent error occurred', {
    type: normalized.type,
    message: normalized.message,
    run_id: normalized.run_id,
    request_id: normalized.request_id,
  });

  // 4. Display user-friendly message
  toast.error(normalized.message);

  // 5. Track for observability
  if (normalized.request_id) {
    trackError(normalized);
  }
}
```

### Logging Strategy

```typescript
// Component-level logging with child logger
const ChatInterface = () => {
  const logger = useMemo(() =>
    logger.child({ component: 'ChatInterface' }),
    []
  );

  const handleSendMessage = async (message: string) => {
    logger.info('Sending message', { length: message.length });

    const start = Date.now();
    try {
      await sendMessage(message);
      logPerformance('Send message', Date.now() - start);
      logUserAction('Message sent', { length: message.length });
    } catch (error) {
      logError(error, { operation: 'sendMessage' });
    }
  };
};
```

## Dependencies

### External Dependencies

- **clsx** (`^2.1.1`) - Conditional class name construction
- **tailwind-merge** (`^2.5.4`) - Tailwind CSS class conflict resolution

### Internal Dependencies

- `@/types/ag-ui` - AG-UI Protocol TypeScript types
- Node.js process.env - Environment variable access

## Related Documentation

- [Components Directory](../components/README.md) - UI components using these utilities
- [Backend API](../../backend/deep_agent/api/README.md) - WebSocket endpoint and AG-UI Protocol implementation
- [Frontend Root](../README.md) - Frontend architecture overview
- [AG-UI Protocol Documentation](https://docs.ag-ui.com/sdk/python/core/overview) - Official AG-UI specification

## Testing

### Test Coverage

- **utils.ts:** Unit tests in `__tests__/utils.test.ts`
  - Class name merging
  - Tailwind conflict resolution
  - Edge cases (empty, undefined, null)

- **logger.ts:** Unit tests in `__tests__/logger.test.ts`
  - All log levels (debug, info, warn, error)
  - Child logger context inheritance
  - Environment-specific formatting
  - Helper functions (logError, logPerformance, logUserAction)

- **eventValidator.ts:** Planned Phase 1
  - Event validation logic
  - Type guards
  - Batch validation
  - Custom event filtering

- **errorEventAdapter.ts:** Planned Phase 1
  - Multi-protocol error normalization
  - Security sanitization
  - Type guards

### Running Tests

```bash
# Run all lib tests
npm test -- lib/

# Run specific test file
npm test -- lib/__tests__/logger.test.ts

# Run with coverage
npm test -- lib/ --coverage
```

## Best Practices

### Logging Guidelines

1. **Use appropriate log levels:**
   - `debug` - Detailed diagnostic information (dev only)
   - `info` - General informational messages
   - `warn` - Warning messages for recoverable issues
   - `error` - Error messages for failures

2. **Include relevant context:**
   ```typescript
   // Good
   logger.error('API request failed', { endpoint, status, userId });

   // Bad
   logger.error('API request failed');
   ```

3. **Use child loggers for components:**
   ```typescript
   const componentLogger = logger.child({ component: 'ChatInterface' });
   ```

4. **Log performance for critical operations:**
   ```typescript
   const start = Date.now();
   await criticalOperation();
   logPerformance('Critical operation', Date.now() - start);
   ```

### Event Validation Guidelines

1. **Always validate WebSocket events:**
   ```typescript
   const validation = validateAGUIEvent(event);
   if (!validation.isValid) {
     // Handle invalid event
     return;
   }
   ```

2. **Filter custom events before AG-UI handlers:**
   ```typescript
   if (shouldFilterEvent(event.event)) {
     // Handle custom event separately
     return;
   }
   ```

3. **Use type guards for type safety:**
   ```typescript
   if (isStreamingEvent(event.event)) {
     // TypeScript knows this is a streaming event
   }
   ```

### Error Handling Guidelines

1. **Always normalize errors:**
   ```typescript
   const normalized = normalizeErrorEvent(errorEvent);
   ```

2. **Log errors with context:**
   ```typescript
   logger.error('Operation failed', {
     type: normalized.type,
     message: normalized.message,
     run_id: normalized.run_id,
   });
   ```

3. **Display user-friendly messages:**
   ```typescript
   toast.error(getErrorMessage(errorEvent));
   ```

## Security Considerations

### Error Message Sanitization

All error messages are automatically sanitized to prevent:
- **XSS attacks** - HTML/script tags removed
- **Secret leakage** - API keys/tokens redacted
- **DoS attacks** - Message length limited to 500 chars

### Logging Security

- **Never log secrets** - Use context objects carefully
- **Sanitize user input** - Especially in error messages
- **Limit log volume** - Prevent DoS via excessive logging

### WebSocket Security

- **Validate all events** - Prevent malformed event handling
- **Filter custom events** - Prevent protocol confusion attacks
- **Type guards** - Runtime type checking for safety

## Future Enhancements (Phase 1+)

### Logging Enhancements
- [ ] LangSmith integration for production logging
- [ ] Sentry integration for error tracking
- [ ] Log sampling for high-volume scenarios
- [ ] Log aggregation and search

### Event Validation Enhancements
- [ ] Schema validation using Zod
- [ ] Event replay for debugging
- [ ] Event metrics and analytics
- [ ] Custom event registry

### Error Handling Enhancements
- [ ] Error recovery strategies
- [ ] Retry logic for transient errors
- [ ] Error boundary integration
- [ ] User-facing error codes

## Contributing

When adding new utilities:

1. **Add JSDoc comments** - Document all functions with examples
2. **Write unit tests** - Minimum 80% coverage
3. **Update this README** - Add usage examples
4. **Follow TypeScript best practices** - Type safety first
5. **Consider security** - Sanitize inputs, validate outputs

### Adding a New Utility

```typescript
/**
 * Formats a date for display in the chat interface.
 *
 * @param date - Date to format (Date object or ISO string)
 * @param format - Format type ("relative" | "absolute")
 * @returns Formatted date string
 *
 * @example
 * ```typescript
 * formatChatDate(new Date(), "relative") // "2 minutes ago"
 * formatChatDate("2025-11-12T10:30:00Z", "absolute") // "Nov 12, 10:30 AM"
 * ```
 */
export function formatChatDate(
  date: Date | string,
  format: "relative" | "absolute" = "relative"
): string {
  // Implementation
}
```

## Troubleshooting

### Common Issues

**Issue:** Events not validating correctly
```typescript
// Solution: Check event structure matches AG-UI Protocol
const validation = validateAGUIEvent(event);
console.log(validation); // Shows detailed error
```

**Issue:** Errors not displaying properly
```typescript
// Solution: Ensure error normalization
const normalized = normalizeErrorEvent(errorEvent);
console.log(normalized); // Shows normalized error structure
```

**Issue:** Logs not appearing in development
```typescript
// Solution: Check NODE_ENV and log level
console.log(process.env.NODE_ENV); // Should be "development"
logger.debug('Test'); // Only shows in development
```

## Version History

- **v0.1.0** (Phase 0) - Initial utilities
  - utils.ts (class name merging)
  - logger.ts (structured logging)
  - eventValidator.ts (AG-UI Protocol validation)
  - errorEventAdapter.ts (multi-protocol error normalization)
  - Unit tests for utils and logger

- **v0.2.0** (Phase 1 - Planned) - Enhanced observability
  - LangSmith integration
  - Sentry error tracking
  - Event validation tests
  - Error adapter tests
  - Performance monitoring utilities

---

**Last Updated:** 2025-11-12
**Maintained By:** Deep Agent One Team
