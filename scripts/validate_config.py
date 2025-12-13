#!/usr/bin/env python3
"""
Configuration validation script for Deep Agent AGI.

Validates configuration settings to prevent dangerous defaults, invalid relationships,
and missing required values. Run this before starting the application or in CI/CD.

Exit codes:
  0 - All checks passed
  1 - Critical errors found (deployment blocked)

Usage:
  python scripts/validate_config.py
  ./scripts/validate_config.py
"""

import re
import sys
import traceback
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from deep_agent.config import get_settings
except ImportError as e:
    print(f"❌ ERROR: Failed to import settings module: {e}")
    print("   Make sure you're running from the project root directory.")
    sys.exit(1)


def validate_config() -> bool:
    """
    Validate configuration settings.

    Returns:
        bool: True if all checks pass, False if critical errors found
    """
    settings = get_settings()
    errors = []
    warnings = []

    print("🔍 Validating Deep Agent AGI configuration...\n")

    # =========================================================================
    # CHECK 1: Environment consistency
    # =========================================================================
    print("✓ Checking environment consistency...")

    # ENV must not be prod with DEBUG enabled
    if settings.ENV == "prod" and settings.DEBUG:
        errors.append("ENV=prod but DEBUG=true (production must not have debug enabled)")

    # DEBUG should be false in staging/prod
    if settings.ENV in ["staging", "prod"] and settings.DEBUG:
        warnings.append(f"DEBUG=true in {settings.ENV} environment (should be false)")

    # API_RELOAD should be false in staging/prod
    if settings.ENV in ["staging", "prod"] and settings.API_RELOAD:
        warnings.append(f"API_RELOAD=true in {settings.ENV} environment (should be false)")

    # =========================================================================
    # CHECK 2: Timeout relationships
    # =========================================================================
    print("✓ Checking timeout relationships...")

    # Tool timeout must be less than stream timeout
    if settings.TOOL_EXECUTION_TIMEOUT >= settings.STREAM_TIMEOUT_SECONDS:
        errors.append(
            f"TOOL_EXECUTION_TIMEOUT ({settings.TOOL_EXECUTION_TIMEOUT}s) "
            f"must be < STREAM_TIMEOUT_SECONDS ({settings.STREAM_TIMEOUT_SECONDS}s) "
            "to prevent race conditions"
        )

    # Web search timeout should be reasonable
    if settings.WEB_SEARCH_TIMEOUT > settings.TOOL_EXECUTION_TIMEOUT:
        warnings.append(
            f"WEB_SEARCH_TIMEOUT ({settings.WEB_SEARCH_TIMEOUT}s) > "
            f"TOOL_EXECUTION_TIMEOUT ({settings.TOOL_EXECUTION_TIMEOUT}s) "
            "(web search may time out before tool limit)"
        )

    # Stream timeout should be reasonable
    if settings.STREAM_TIMEOUT_SECONDS < 60:
        warnings.append(
            f"STREAM_TIMEOUT_SECONDS ({settings.STREAM_TIMEOUT_SECONDS}s) "
            "is very short (< 60s) - may cause premature timeouts"
        )

    if settings.STREAM_TIMEOUT_SECONDS > 600:
        warnings.append(
            f"STREAM_TIMEOUT_SECONDS ({settings.STREAM_TIMEOUT_SECONDS}s) "
            "is very long (> 10 minutes) - users may experience long waits"
        )

    # =========================================================================
    # CHECK 3: Required API keys (unless mocking)
    # =========================================================================
    print("✓ Checking API keys...")

    if not settings.MOCK_EXTERNAL_APIS:
        # OpenAI API key is required
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_key_here":
            errors.append(
                "OPENAI_API_KEY not set or using placeholder. "
                "Set MOCK_EXTERNAL_APIS=true for testing or provide a valid key."
            )

        # Check for placeholder keys in production
        if settings.ENV in ["staging", "prod"]:
            if settings.PERPLEXITY_API_KEY == "your_perplexity_key_here":
                warnings.append("PERPLEXITY_API_KEY using placeholder in production environment")

            if settings.LANGSMITH_API_KEY == "your_langsmith_key_here":
                warnings.append("LANGSMITH_API_KEY using placeholder - monitoring will not work")

    # =========================================================================
    # CHECK 3.5: GPT Model Configuration
    # =========================================================================
    print("✓ Checking GPT model configuration...")

    # GPT_MODEL_NAME must be a valid OpenAI model
    if not settings.GPT_MODEL_NAME.startswith("gpt-"):
        errors.append(
            f"GPT_MODEL_NAME='{settings.GPT_MODEL_NAME}' does not start with 'gpt-'. "
            "Must be a valid OpenAI model name."
        )

    # Warn if not using dated release format (YYYY-MM-DD suffix)
    if settings.GPT_MODEL_NAME.startswith("gpt-5") and not re.search(
        r"\d{4}-\d{2}-\d{2}$", settings.GPT_MODEL_NAME
    ):
        warnings.append(
            f"GPT_MODEL_NAME='{settings.GPT_MODEL_NAME}' should use dated release format. "
            "Example: gpt-5.1-2025-11-13 (check OpenAI docs for latest releases)"
        )

    # =========================================================================
    # CHECK 4: Security settings
    # =========================================================================
    print("✓ Checking security settings...")

    # Production environments need proper secrets
    if settings.ENV in ["staging", "prod"]:
        # SECRET_KEY must be set and strong
        if not settings.SECRET_KEY:
            errors.append("SECRET_KEY not set in production environment")
        elif settings.SECRET_KEY == "your_secret_key_here":  # nosec B105 - placeholder check, not usage
            errors.append("SECRET_KEY using placeholder in production environment")
        elif len(settings.SECRET_KEY) < 32:
            errors.append(
                f"SECRET_KEY too short ({len(settings.SECRET_KEY)} chars) - "
                "must be at least 32 characters. Generate with: openssl rand -hex 32"
            )

        # JWT_SECRET must be set and strong
        if not settings.JWT_SECRET:
            errors.append("JWT_SECRET not set in production environment")
        elif settings.JWT_SECRET == "your_jwt_secret_here":  # nosec B105 - placeholder check, not usage
            errors.append("JWT_SECRET using placeholder in production environment")
        elif len(settings.JWT_SECRET) < 32:
            errors.append(
                f"JWT_SECRET too short ({len(settings.JWT_SECRET)} chars) - "
                "must be at least 32 characters"
            )

        # Bcrypt rounds should be reasonable
        if settings.BCRYPT_ROUNDS < 10:
            warnings.append(
                f"BCRYPT_ROUNDS ({settings.BCRYPT_ROUNDS}) is too low - "
                "recommended minimum is 10 for production"
            )
        elif settings.BCRYPT_ROUNDS > 14:
            warnings.append(
                f"BCRYPT_ROUNDS ({settings.BCRYPT_ROUNDS}) is very high - "
                "may cause performance issues"
            )

    # =========================================================================
    # CHECK 5: Dangerous production settings
    # =========================================================================
    print("✓ Checking production safety settings...")

    if settings.ENV in ["staging", "prod"]:
        # Debug tools must be disabled
        if settings.ENABLE_DEBUG_TOOLBAR:
            errors.append("ENABLE_DEBUG_TOOLBAR=true in production (security risk)")

        if settings.ENABLE_PROFILING:
            warnings.append("ENABLE_PROFILING=true in production (performance impact)")

        if settings.MOCK_EXTERNAL_APIS:
            errors.append("MOCK_EXTERNAL_APIS=true in production (non-functional APIs)")

        # Log level should be appropriate
        if settings.LOG_LEVEL == "DEBUG":
            warnings.append(
                "LOG_LEVEL=DEBUG in production (excessive logging, potential PII leaks)"
            )

    # =========================================================================
    # CHECK 6: Type and range validation
    # =========================================================================
    print("✓ Checking value ranges...")

    # Port must be valid
    if not (1 <= settings.API_PORT <= 65535):
        errors.append(f"API_PORT ({settings.API_PORT}) out of valid range (1-65535)")

    # Max tokens must be positive
    if settings.GPT_MAX_TOKENS <= 0:
        errors.append(f"GPT_MAX_TOKENS ({settings.GPT_MAX_TOKENS}) must be positive")

    # Temperature validation removed - deprecated for GPT-5+ models
    # GPT-5+ models use reasoning_effort parameter instead of temperature

    # Max tool calls must be reasonable
    if settings.MAX_TOOL_CALLS_PER_INVOCATION < 1:
        errors.append(
            f"MAX_TOOL_CALLS_PER_INVOCATION ({settings.MAX_TOOL_CALLS_PER_INVOCATION}) "
            "must be at least 1"
        )
    elif settings.MAX_TOOL_CALLS_PER_INVOCATION > 25:
        warnings.append(
            f"MAX_TOOL_CALLS_PER_INVOCATION ({settings.MAX_TOOL_CALLS_PER_INVOCATION}) "
            "is very high - may cause long execution times and high costs"
        )

    # Cleanup days must be positive
    if settings.CHECKPOINT_CLEANUP_DAYS < 1:
        errors.append(
            f"CHECKPOINT_CLEANUP_DAYS ({settings.CHECKPOINT_CLEANUP_DAYS}) " "must be at least 1"
        )

    # =========================================================================
    # CHECK 7: CORS configuration
    # =========================================================================
    print("✓ Checking CORS configuration...")

    # CORS origins should be set
    cors_origins = settings.cors_origins_list
    if not cors_origins:
        warnings.append("CORS_ORIGINS not set - API will reject all cross-origin requests")

    # Production should not allow localhost
    if settings.ENV == "prod":
        if any("localhost" in origin or "127.0.0.1" in origin for origin in cors_origins):
            warnings.append("CORS_ORIGINS includes localhost in production environment")

    # =========================================================================
    # CHECK 8: Feature flag consistency
    # =========================================================================
    print("✓ Checking feature flags...")

    # HITL should be enabled in production
    if settings.ENV == "prod" and not settings.ENABLE_HITL:
        warnings.append("ENABLE_HITL=false in production - human-in-the-loop disabled")

    # Cost tracking should be enabled
    if not settings.ENABLE_COST_TRACKING:
        warnings.append("ENABLE_COST_TRACKING=false - won't track API costs")

    # =========================================================================
    # CHECK 9: Rate limiting
    # =========================================================================
    print("✓ Checking rate limiting...")

    # Rate limits should be set
    if settings.RATE_LIMIT_REQUESTS < 1:
        warnings.append(f"RATE_LIMIT_REQUESTS ({settings.RATE_LIMIT_REQUESTS}) is zero or negative")

    if settings.RATE_LIMIT_PERIOD < 60:
        warnings.append(
            f"RATE_LIMIT_PERIOD ({settings.RATE_LIMIT_PERIOD}s) is very short (< 1 minute)"
        )

    # =========================================================================
    # CHECK 10: Logging configuration
    # =========================================================================
    print("✓ Checking logging configuration...")

    # Logging reasoning decisions in prod may leak PII
    if settings.ENV == "prod" and settings.LOG_REASONING_DECISIONS:
        warnings.append(
            "LOG_REASONING_DECISIONS=true in production - may log sensitive user queries"
        )

    # =========================================================================
    # REPORT RESULTS
    # =========================================================================
    print("\n" + "=" * 70)

    if errors:
        print("❌ Configuration validation FAILED\n")
        print("CRITICAL ERRORS (must fix before deployment):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

    if warnings:
        if errors:
            print()
        print("⚠️  WARNINGS (recommended to fix):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    if not errors and not warnings:
        print("✅ Configuration validation PASSED")
        print("   All checks passed - configuration is safe to use")

    print("=" * 70)

    # Return success only if no critical errors
    return len(errors) == 0


def main() -> None:
    """Main entry point."""
    try:
        success = validate_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        print("   Configuration validation encountered an unexpected error")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
