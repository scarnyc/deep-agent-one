# WebSocket Integration Test Scripts

## Overview

These scripts test the Deep Agent AGI backend via WebSocket connections to validate agent behavior, tool execution, and streaming functionality.

## Scripts

### `test_trace_2bdaec5e_replay.py`
Reproduces the exact scenario from LangSmith trace `2bdaec5e-2c4a-4737-964e-2e89e2ddaa92`:
- Sends query: "latest trends in quantum"
- Validates parallel tool execution
- Ensures no CancelledError or timeout issues

### `test_explicit_tool_usage.py`
Tests agent tool usage with explicit instructions:
- Sends query requesting web search
- Validates tools are invoked when explicitly requested
- Confirms timeout fix effectiveness

### `fetch_langsmith_trace.py`
Utility to download LangSmith traces for analysis:
- Fetches trace data from LangSmith API
- Saves to JSON file for inspection
- Analyzes tool calls and error patterns

## Prerequisites

**CRITICAL: Backend Must Be Running**

These scripts connect to a live backend instance. They do NOT start the backend.

### Backend Startup

```bash
# Start backend with production settings (ENV=local)
cd /Users/scar_nyc/Documents/GitHub/deep-agent-agi
source .env  # Loads ENV=local
cd backend
source ../venv/bin/activate
uvicorn deep_agent.main:app --reload --port 8000
```

### Environment Requirements

**The backend MUST use `ENV=local` or `ENV=prod` (NOT `ENV=test`)**

Why? When `ENV=test`, the checkpointer is disabled in `backend/deep_agent/agents/deep_agent.py:109-128`:

```python
if settings.ENV != "test":
    checkpointer = await checkpointer_manager.create_checkpointer()
else:
    logger.info("Checkpointer disabled for test environment")
    checkpointer = None
```

Without the checkpointer, the agent may behave differently and skip tool execution.

### Verify Backend Settings

Before running tests, confirm:

```bash
# Check ENV in .env file
grep "^ENV=" .env
# Should show: ENV=local

# Check backend logs for checkpointer
tail -f logs/backend.log | grep -i checkpointer
# Should show: "Created AsyncSqliteSaver checkpointer"
```

## Running Tests

### Individual Test

```bash
source venv/bin/activate
python tests/scripts/test_trace_2bdaec5e_replay.py
```

### Both Tests

```bash
source venv/bin/activate
python tests/scripts/test_trace_2bdaec5e_replay.py
python tests/scripts/test_explicit_tool_usage.py
```

## Expected Results

### Successful Test Run

```
🧪 TRACE 2bdaec5e REPLAY TEST
================================================================================
✅ Connected to WebSocket
📤 Sending: latest trends in quantum

📥 Receiving events...
  🔧 Tool #1 started: web_search
  🔧 Tool #2 started: web_search
  ...
  ✅ Tool #1 completed
  ✅ Tool #2 completed
  ...
  🏁 LangGraph chain complete

📊 TEST RESULTS
⏱️  Execution Time: 98.22 seconds
🔧 Tool Calls Started: 7
✅ Tool Calls Completed: 7

✅ PASS: All validation checks passed
🎉 SUCCESS: Trace 2bdaec5e scenario passed!
```

### Failed Test (Wrong ENV)

If backend runs with `ENV=test`:

```
📊 TEST RESULTS
⏱️  Execution Time: 0.03 seconds
🔧 Tool Calls Started: 0
✅ Tool Calls Completed: 0

❌ FAIL: Tool calls executed
  Expected: >= 1 tool call
  Actual:   0 tool calls
```

**Solution:** Restart backend with `ENV=local` (see Backend Startup above).

## Test Script Implementation Details

### Bug Fix (2025-11-06)

**Original Issue:** Test scripts exited on the FIRST `on_chain_end` event from middleware chains, not waiting for the main LangGraph chain to complete.

**Fix:** Check event name before treating chain as complete:

```python
# Before (bug):
elif event_type == 'on_chain_end':
    complete = True  # ❌ Exits on ANY chain_end!

# After (fixed):
elif event_type == 'on_chain_end':
    event_name = event.get('name', '')
    if event_name == 'LangGraph':  # ✅ Only exit on main chain
        complete = True
```

**Impact:**
- Tests now wait for agent to complete full execution including tool calls
- Previously, tests exited after ~0.03s (middleware phase)
- Now, tests run for ~90-120s and properly validate tool execution

### Event Flow

The agent emits events in this order:

1. `on_chain_start - LangGraph` (main chain starts)
2. `on_chain_start - PatchToolCallsMiddleware.before_agent`
3. `on_chain_end - PatchToolCallsMiddleware.before_agent` ← **Old bug: exited here**
4. `on_chain_start - SummarizationMiddleware.before_model`
5. `on_chain_end - SummarizationMiddleware.before_model`
6. `on_chain_start - model` (GPT-5 invoked)
7. `on_chat_model_stream` (streaming response)
8. `on_tool_start - web_search` (tools executed)
9. `on_tool_end - web_search`
10. `on_chain_end - LangGraph` ← **Fixed: exit here**

## Troubleshooting

### Problem: No tools executed (0 tool calls)

**Symptoms:**
- Test completes in <1 second
- 0 tool calls started
- 4 events received

**Cause:** Backend running with `ENV=test` (checkpointer disabled)

**Solution:**
1. Stop backend (Ctrl+C)
2. Verify `.env` has `ENV=local`
3. Restart backend (see Backend Startup)
4. Re-run test

### Problem: Connection refused

**Symptoms:**
```
❌ WebSocket connection failed: [Errno 61] Connection refused
```

**Cause:** Backend not running

**Solution:** Start backend (see Backend Startup)

### Problem: Timeout after 300s

**Symptoms:**
- Test runs for exactly 300 seconds
- Shows "Timeout waiting for response"

**Cause:** Agent execution taking longer than timeout (rare)

**Solution:**
1. Check LangSmith trace for specific failure
2. Check backend logs for errors
3. Verify Perplexity API key is valid

### Problem: CancelledError received

**Symptoms:**
- Test shows "cancellation errors: 1"
- Events include on_error with CancelledError

**Cause:** Client disconnected before completion (network issue, script bug)

**Solution:**
1. Check network connectivity
2. Verify script isn't exiting early
3. Check backend logs for disconnect reason

## Test Validation Criteria

### test_trace_2bdaec5e_replay.py

1. ✅ Completed within 300s timeout
2. ✅ No CancelledError received
3. ✅ Tool calls executed (>= 1)
4. ✅ All tool calls completed
5. ✅ No duplicate error events

### test_explicit_tool_usage.py

1. ✅ Completed within 300s timeout
2. ✅ No cancellation errors
3. ⚠️  Tools used (nice-to-have, not required)
4. ✅ All started tools completed

## Related Documentation

- `docs/WEBSOCKET_CANCELLATION_FIX.md` - Root cause analysis of timeout issue
- `docs/TRACE_2bdaec5e_ANALYSIS.md` - Deep dive into user trace
- `docs/TEST_RESULTS_2025-11-06.md` - Test execution results

## Common Questions

### Q: Why do tests run against localhost:8000 instead of using mocks?

**A:** These are integration tests validating real WebSocket streaming, agent execution, and tool invocation. Mocking would miss critical issues with event streaming, timeouts, and LangGraph execution.

### Q: Why does the agent use different numbers of tools each time?

**A:** GPT-5 analyzes the query and decides how many tools to use based on reasoning. The specific number varies (7, 10, 27 tools observed), but what matters is that tools ARE used and complete successfully.

### Q: Can I run tests with ENV=test?

**A:** No. ENV=test disables the checkpointer, which affects agent behavior. Always use ENV=local for integration tests.

### Q: How long should tests take?

**A:**
- With tools: 60-120 seconds (depending on number of parallel searches)
- Without tools (bug/wrong ENV): <1 second
- Timeout failure: Exactly 300 seconds

---

**Last Updated:** 2025-11-06
**Status:** Tests validated and passing with tool execution
