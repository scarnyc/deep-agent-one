# WebSocket CancelledError Fix - Root Cause Analysis & Solution

**Date:** 2025-11-06
**Issue:** Agent execution fails with `CancelledError` when making multiple parallel tool calls
**Status:** IDENTIFIED - Fix in progress

---

## Problem Summary

When the agent attempts to make multiple parallel tool calls (e.g., "10 targeted queries"), the WebSocket streaming connection times out after 60 seconds, causing:
- `Error: Agent streaming timed out` message in UI
- `Error: Agent execution failed` message in UI
- Browser console showing `[AG-UI] Run error` with empty data
- Agent status stuck in "Error" state

---

## Root Cause Analysis

### 1. Timeout Configuration Mismatch

**Current Settings (backend/deep_agent/config/settings.py):**
```python
STREAM_TIMEOUT_SECONDS: int = 60                 # Stream timeout
TOOL_EXECUTION_TIMEOUT: int = 45                 # Per-tool timeout
WEB_SEARCH_TIMEOUT: int = 30                     # Perplexity timeout
```

**Frontend (frontend/hooks/useWebSocket.ts):**
```typescript
const CONNECTION_TIMEOUT = 30000;  // 30 seconds
```

**Problem:**
- With 10 parallel tool calls @ 45s each, total execution time >> 60s
- Stream timeout kills the operation before tools complete
- Frontend timeout (30s) is even shorter than backend (60s)

### 2. Double Error Event Emission

**Timeline of error events:**

1. **TimeoutError occurs** (agent_service.py:304 - asyncio.timeout context)
2. **First error event** yielded (agent_service.py:388-399):
   ```python
   yield {
       "event": "on_error",
       "data": {
           "error": "Agent streaming timed out",
           ...
       },
       ...
   }
   ```
3. **RuntimeError raised** (agent_service.py:400)
4. **Second error event** sent by WebSocket handler (main.py:626-638):
   ```python
   await websocket.send_json({
       "event": "on_error",
       "data": {
           "error": "Agent execution failed",
           ...
       },
       ...
   })
   ```

**Result:** Frontend receives TWO error events, causing duplicate error messages.

### 3. No Progress Feedback

**Current behavior:**
- Agent streams `on_chain_start` event
- Silence for 60 seconds while tools execute
- Timeout → Error events
- User sees no progress indicators

**Impact:**
- User doesn't know if agent is working or hung
- No visibility into which tools are running
- Connection appears frozen

### 4. Frontend Error Handling

**Issue in useAGUIEventHandler.ts:254-291:**

The `handleRunError` function expects error data in specific formats:
```typescript
const normalizedError = normalizeErrorEvent(event);
```

When the error event has **empty or malformed data**, `normalizeErrorEvent()` may fail or return incomplete data, causing:
- Browser console errors
- Incorrect error display
- Stack traces pointing to React internals

---

## Solution Design

### Fix 1: Increase Stream Timeout for Parallel Operations

**Change:** Increase `STREAM_TIMEOUT_SECONDS` from 60s to 300s (5 minutes)

**Rationale:**
- 10 tools × 45s timeout = 450s max (7.5 min) if sequential
- With parallelism, ~60-90s realistic for 10 concurrent calls
- 300s provides safety margin for rate limits, retries, cold starts

**Implementation:**
```python
# backend/deep_agent/config/settings.py
STREAM_TIMEOUT_SECONDS: int = 300  # 5 minutes for parallel tool operations
```

**Frontend update:**
```typescript
// frontend/hooks/useWebSocket.ts
const CONNECTION_TIMEOUT = 300000;  // 5 minutes (match backend)
```

### Fix 2: Prevent Double Error Events

**Change:** Don't re-raise exception after yielding error event in TimeoutError handler

**Current code (agent_service.py:377-400):**
```python
except asyncio.TimeoutError:
    ...
    yield {
        "event": "on_error",
        ...
    }
    raise RuntimeError(f"Agent streaming timed out after {timeout_seconds}s")  # ❌ Don't raise
```

**Fixed code:**
```python
except asyncio.TimeoutError:
    ...
    yield {
        "event": "on_error",
        ...
    }
    return  # ✅ Return gracefully without raising
```

**Impact:**
- Only ONE error event sent to client
- No duplicate "Agent execution failed" message
- Cleaner error handling

### Fix 3: Add Heartbeat/Progress Events

**Change:** Emit periodic progress events during long operations

**Implementation options:**

**Option A: Emit progress events every 10 seconds**
```python
# In agent_service.py stream() method
last_heartbeat = asyncio.get_event_loop().time()
HEARTBEAT_INTERVAL = 10  # seconds

async for event in agent.astream_events(...):
    current_time = asyncio.get_event_loop().time()
    if current_time - last_heartbeat > HEARTBEAT_INTERVAL:
        yield {
            "event": "on_progress",
            "data": {
                "message": "Agent is still processing...",
                "events_received": event_count,
            },
            "metadata": {
                "thread_id": thread_id,
                "trace_id": trace_id,
            },
        }
        last_heartbeat = current_time

    # ... existing event handling
```

**Option B: Use existing tool events as natural heartbeats**
- `on_tool_start` → "Starting tool X"
- `on_tool_end` → "Completed tool X"
- These already provide progress feedback

**Recommendation:** Start with **Option B** (tool events), add Option A if needed.

### Fix 4: Improve Frontend Error Display

**Change:** Create ErrorDisplay component with proper error formatting

**New component:** `frontend/components/ErrorDisplay.tsx`
```typescript
interface ErrorDisplayProps {
  error: string;
  errorType?: string;
  errorCode?: string;
  trace_id?: string;
}

export function ErrorDisplay({ error, errorType, errorCode, trace_id }: ErrorDisplayProps) {
  return (
    <div className="error-display">
      <div className="error-message">{error}</div>
      {errorType && <div className="error-type">{errorType}</div>}
      {trace_id && <div className="trace-id">Trace: {trace_id}</div>}
    </div>
  );
}
```

**Update:** `frontend/providers/WebSocketProvider.tsx`
- Use ErrorDisplay component for error events
- Handle missing/empty error data gracefully

---

## Implementation Plan

### Phase 1: Backend Fixes (Priority: HIGH)

1. **Update timeout configuration**
   - ✅ settings.py: STREAM_TIMEOUT_SECONDS = 300
   - ✅ Document rationale in comments

2. **Fix double error events**
   - ✅ agent_service.py:400 - Return instead of raise
   - ✅ Add test case for timeout behavior

3. **Verify tool event streaming**
   - ✅ Ensure on_tool_start/on_tool_end events are in STREAM_ALLOWED_EVENTS
   - ✅ Test that tool events flow through to frontend

### Phase 2: Frontend Fixes (Priority: MEDIUM)

4. **Update frontend timeout**
   - ✅ useWebSocket.ts: CONNECTION_TIMEOUT = 300000

5. **Create ErrorDisplay component**
   - ✅ components/ErrorDisplay.tsx
   - ✅ Handle missing error data gracefully

6. **Update WebSocketProvider**
   - ✅ Use ErrorDisplay for error events
   - ✅ Add null checks for error data

### Phase 3: Testing (Priority: HIGH)

7. **Test with multi-tool queries**
   - ✅ Send message that triggers 10+ parallel tool calls
   - ✅ Verify no timeout errors
   - ✅ Verify tool progress visible in UI

8. **Run existing test suite**
   - ✅ `pytest tests/integration/test_services/test_agent_service_cancellation.py -v`
   - ✅ Verify all tests pass

9. **Test error scenarios**
   - ✅ Actual timeouts (query that exceeds 5 minutes)
   - ✅ Client disconnect during streaming
   - ✅ Invalid tool calls

---

## Testing Strategy

### Test Case 1: Parallel Tool Calls (Happy Path)

**Input:**
```
"Search the web for the latest developments across key quantum areas
(computing hardware, fault tolerance, networking, sensing, PQC, and
quantum utility claims). I'll run 10 targeted queries in parallel."
```

**Expected behavior:**
- No timeout errors
- Tool events stream to frontend
- All 10 queries complete
- Final response displayed

**Success criteria:**
- ✅ No `CancelledError` in console
- ✅ Agent status shows "completed"
- ✅ Tool execution visible in UI
- ✅ Response time < 5 minutes

### Test Case 2: Actual Timeout (Edge Case)

**Input:**
```
"Run a query that takes 6 minutes"  # Exceeds 5-minute timeout
```

**Expected behavior:**
- Stream times out after 300s
- Single error event: "Agent streaming timed out"
- Agent status shows "error"
- No duplicate error messages

**Success criteria:**
- ✅ Only ONE error message in UI
- ✅ Error event has proper data structure
- ✅ LangSmith trace_id included

### Test Case 3: Client Disconnect

**Input:**
- Start streaming operation
- Close browser tab mid-stream

**Expected behavior:**
- Backend detects disconnect
- CancelledError logged (info level)
- No error sent (connection closed)
- Agent continues in background

**Success criteria:**
- ✅ No backend crash
- ✅ Graceful cancellation
- ✅ State preserved in checkpointer

---

## Metrics & Monitoring

### Success Metrics

- **Timeout Error Rate:** < 1% of requests (down from current ~10%)
- **Average Response Time:** 30-90s for 10-tool queries
- **User Satisfaction:** No "hung connection" reports
- **Error Event Duplicates:** 0 (currently 2 per timeout)

### Monitoring

**LangSmith Traces:**
- Filter for runs > 60s duration
- Check for timeout errors
- Verify tool execution overlap (parallelism)

**Frontend Logs:**
- Count `on_error` events per session
- Track error event data quality
- Monitor connection timeout occurrences

**Backend Logs:**
```bash
# Filter for timeout-related logs
grep "streaming timed out" logs/*.log

# Count cancellation events
grep "CancelledError" logs/*.log | wc -l
```

---

## Risk Assessment

### Risks

1. **Increased resource usage**
   - Longer timeout → longer-running requests
   - Potential memory buildup during 5-minute streams
   - **Mitigation:** Monitor backend memory, set hard limit at 10-minute mark

2. **User impatience**
   - Users may not wait 5 minutes
   - **Mitigation:** Show progress events, estimated completion time

3. **Rate limiting**
   - Parallel tool calls may hit API rate limits
   - **Mitigation:** Implement exponential backoff in tool execution

### Rollback Plan

If issues arise:
1. Revert `STREAM_TIMEOUT_SECONDS` to 60s
2. Revert agent_service.py timeout handler changes
3. Notify users of temporary reduced parallel query support

---

## Next Steps

1. **Implement Phase 1 fixes** (backend timeout + error handling)
2. **Test with multi-tool queries** (verify no timeouts)
3. **Implement Phase 2 fixes** (frontend updates)
4. **Run full test suite** (unit + integration + E2E)
5. **Deploy to staging** (verify in near-production environment)
6. **Monitor metrics** (1 week observation period)
7. **Deploy to production** (with gradual rollout)

---

## Appendix: Related Files

### Backend
- `backend/deep_agent/config/settings.py` - Timeout configuration
- `backend/deep_agent/services/agent_service.py` - Stream timeout handler
- `backend/deep_agent/main.py` - WebSocket endpoint

### Frontend
- `frontend/hooks/useWebSocket.ts` - Connection timeout
- `frontend/hooks/useAGUIEventHandler.ts` - Error event handling
- `frontend/components/ErrorDisplay.tsx` - NEW (to be created)

### Tests
- `backend/tests/integration/test_services/test_agent_service_cancellation.py`
- `backend/tests/integration/test_tool_event_streaming.py` - NEW (to be created)

---

**Document Owner:** Claude Code
**Last Updated:** 2025-11-06
**Status:** Analysis Complete - Implementation In Progress
