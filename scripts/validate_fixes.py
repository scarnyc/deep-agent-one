#!/usr/bin/env python3
"""
Validation script to verify the OpenAI timeout and streaming fixes.

This script checks:
1. OpenAI client timeout configuration is set to 120s
2. Event transformation for AG-UI format is implemented
3. Checkpoint race condition handling is in place
4. OpenAI response time monitoring is active
"""

import ast
import sys
from pathlib import Path

# Change to project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_llm_factory_timeout():
    """Verify OpenAI timeout is configured to 120s."""
    print("Checking LLM factory timeout configuration...")

    llm_factory_path = PROJECT_ROOT / "backend/deep_agent/services/llm_factory.py"

    if not llm_factory_path.exists():
        print(f"❌ FAIL: {llm_factory_path} not found")
        return False

    content = llm_factory_path.read_text()

    # Check for httpx.Timeout import
    if "from httpx import Timeout" not in content:
        print("❌ FAIL: Missing 'from httpx import Timeout' import")
        return False

    # Check for AsyncOpenAI import
    if "from openai import AsyncOpenAI" not in content:
        print("❌ FAIL: Missing 'from openai import AsyncOpenAI' import")
        return False

    # Check for read timeout of 120s
    if "read=120.0" not in content:
        print("❌ FAIL: Missing read=120.0 timeout configuration")
        return False

    # Check for request_timeout
    if "request_timeout" not in content:
        print("❌ FAIL: Missing request_timeout parameter")
        return False

    # Check for retry decorator
    if "@retry(" not in content:
        print("❌ FAIL: Missing @retry decorator")
        return False

    print("✅ PASS: LLM factory has 120s timeout with retry logic")
    return True


def check_event_transformation():
    """Verify event transformation to AG-UI format."""
    print("\nChecking event transformation...")

    agent_service_path = PROJECT_ROOT / "backend/deep_agent/services/agent_service.py"

    if not agent_service_path.exists():
        print(f"❌ FAIL: {agent_service_path} not found")
        return False

    content = agent_service_path.read_text()

    # Check for tool event transformation
    if "tool_execution_started" not in content:
        print("❌ FAIL: Missing 'tool_execution_started' event")
        return False

    if "tool_execution_completed" not in content:
        print("❌ FAIL: Missing 'tool_execution_completed' event")
        return False

    # Check for event metadata
    if '"timestamp": datetime.utcnow().isoformat()' not in content:
        print("❌ FAIL: Missing timestamp in event metadata")
        return False

    print("✅ PASS: Event transformation to AG-UI format implemented")
    return True


def check_checkpoint_handling():
    """Verify checkpoint race condition handling."""
    print("\nChecking checkpoint race condition handling...")

    agent_service_path = PROJECT_ROOT / "backend/deep_agent/services/agent_service.py"

    if not agent_service_path.exists():
        print(f"❌ FAIL: {agent_service_path} not found")
        return False

    content = agent_service_path.read_text()

    # Check for streaming_completed flag
    if "streaming_completed = False" not in content:
        print("❌ FAIL: Missing 'streaming_completed' flag")
        return False

    # Check for post-completion cancellation handling
    if "Post-completion cancellation" not in content:
        print("❌ FAIL: Missing post-completion cancellation handling")
        return False

    # Check for checkpoint finalization grace period
    if "checkpoint finalization" not in content:
        print("❌ FAIL: Missing checkpoint finalization grace period")
        return False

    print("✅ PASS: Checkpoint race condition handling implemented")
    return True


def check_monitoring():
    """Verify OpenAI response time monitoring."""
    print("\nChecking OpenAI response time monitoring...")

    agent_service_path = PROJECT_ROOT / "backend/deep_agent/services/agent_service.py"

    if not agent_service_path.exists():
        print(f"❌ FAIL: {agent_service_path} not found")
        return False

    content = agent_service_path.read_text()

    # Check for OpenAI call timing
    if "openai_call_start" not in content:
        print("❌ FAIL: Missing OpenAI call timing tracking")
        return False

    # Check for near-timeout warning
    if "near timeout threshold" not in content:
        print("❌ FAIL: Missing near-timeout warning logic")
        return False

    # Check for on_chat_model_start/end tracking
    if "on_chat_model_start" not in content or "on_chat_model_end" not in content:
        print("❌ FAIL: Missing on_chat_model_start/end event tracking")
        return False

    print("✅ PASS: OpenAI response time monitoring active")
    return True


def check_checkpoint_cleanup():
    """Verify checkpoint cleanup method exists."""
    print("\nChecking checkpoint cleanup method...")

    checkpointer_path = PROJECT_ROOT / "backend/deep_agent/agents/checkpointer.py"

    if not checkpointer_path.exists():
        print(f"❌ FAIL: {checkpointer_path} not found")
        return False

    content = checkpointer_path.read_text()

    # Check for cleanup_false_errors method
    if "async def cleanup_false_errors" not in content:
        print("❌ FAIL: Missing cleanup_false_errors method")
        return False

    # Check for false error detection SQL
    if "WHERE channel = '__error__'" not in content:
        print("❌ FAIL: Missing false error detection logic")
        return False

    print("✅ PASS: Checkpoint cleanup method implemented")
    return True


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("Validating OpenAI Timeout & Streaming Fixes")
    print("=" * 70)

    results = [
        check_llm_factory_timeout(),
        check_event_transformation(),
        check_checkpoint_handling(),
        check_monitoring(),
        check_checkpoint_cleanup(),
    ]

    print("\n" + "=" * 70)

    if all(results):
        print("🎉 ALL CHECKS PASSED")
        print("=" * 70)
        print("\nNext Steps:")
        print("1. Start backend: poetry run uvicorn deep_agent.main:app --reload --port 8000")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Test WebSocket streaming with parallel tool execution")
        print("4. Monitor logs for:")
        print("   - No BrokenResourceError")
        print("   - OpenAI API response times logged")
        print("   - Tool execution events sent to frontend")
        print("   - No false CancelledError checkpoints")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
