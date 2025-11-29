# Config

## Purpose

Application configuration management using Pydantic settings with environment variable support and validation.

The config module provides:
- Centralized configuration for all application components
- Type-safe environment variable loading and validation
- Default values with environment-specific overrides
- Singleton pattern for efficient settings access
- Comprehensive documentation of all settings

## Key Files

- `__init__.py` - Config module exports and initialization
- `settings.py` - Main Settings class with all configuration parameters

## Usage

### Basic Usage

```python
from deep_agent.config import get_settings

# Get singleton settings instance
settings = get_settings()

# Access settings
print(settings.OPENAI_API_KEY)
print(settings.ENV)
print(settings.DEBUG)

# Use parsed properties
cors_origins = settings.cors_origins_list
allowed_events = settings.stream_allowed_events_list
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required Settings
OPENAI_API_KEY=sk-proj-abc123...

# Optional Settings
LANGSMITH_API_KEY=ls-abc123...
PERPLEXITY_API_KEY=pplx-abc123...

# Environment Configuration
ENV=production
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Environment variables override defaults and are validated on startup.

### Testing with Custom Settings

For unit tests, create custom Settings instances instead of using the singleton:

```python
from deep_agent.config import Settings

def test_my_feature():
    # Create custom settings for this test
    test_settings = Settings(
        OPENAI_API_KEY="test-key",
        ENV="test",
        DEBUG=True,
        MOCK_EXTERNAL_APIS=True
    )

    # Use test_settings instead of get_settings()
    # ...
```

### Accessing Parsed Properties

Some settings are stored as comma-separated strings for environment variable compatibility but provide property accessors for easy usage:

```python
settings = get_settings()

# CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
cors_list = settings.cors_origins_list
# ["http://localhost:3000", "http://localhost:8000"]

# STREAM_ALLOWED_EVENTS="on_tool_start,on_tool_end,on_llm_start"
events = settings.stream_allowed_events_list
# ["on_tool_start", "on_tool_end", "on_llm_start"]
```

## Configuration Structure

### Required Settings

These settings must be provided via environment variables:

- `OPENAI_API_KEY` - OpenAI API key for GPT-5 access

### Core Settings

**Environment Configuration:**
- `ENV` - Environment name (local/dev/staging/prod/test) - Default: "local"
- `DEBUG` - Debug mode flag - Default: False

**GPT-5 Configuration:**
- `OPENAI_API_KEY` - OpenAI API key (required)
- `GPT5_MODEL_NAME` - Model identifier - Default: "gpt-5"
- `GPT5_DEFAULT_REASONING_EFFORT` - Default reasoning level - Default: "medium"
- `GPT5_DEFAULT_VERBOSITY` - Response verbosity - Default: "medium"
- `GPT5_MAX_TOKENS` - Max tokens per completion - Default: 4096
- `GPT5_TEMPERATURE` - Sampling temperature - Default: 0.7

**Reasoning System:**
- `ENABLE_DYNAMIC_REASONING` - Enable dynamic reasoning adjustment - Default: True
- `REASONING_MINIMAL_TIMEOUT` - Minimal reasoning timeout (seconds) - Default: 5
- `REASONING_LOW_TIMEOUT` - Low reasoning timeout (seconds) - Default: 15
- `REASONING_MEDIUM_TIMEOUT` - Medium reasoning timeout (seconds) - Default: 30
- `REASONING_HIGH_TIMEOUT` - High reasoning timeout (seconds) - Default: 60
- `TRIGGER_PHRASES` - Comma-separated trigger phrases - Default: "think harder,deep dive,analyze carefully,be thorough"
- `COMPLEXITY_THRESHOLD_HIGH` - High complexity threshold - Default: 0.8
- `COMPLEXITY_THRESHOLD_MEDIUM` - Medium complexity threshold - Default: 0.5

**Token Conservation:**
- `ENABLE_RESPONSE_CHAINING` - Enable multi-turn chaining - Default: True
- `MAX_CHAIN_LENGTH` - Max chained responses - Default: 3
- `ENABLE_CONTEXT_COMPRESSION` - Enable context compression - Default: True

### Optional Service Settings

**Perplexity (Web Search):**
- `PERPLEXITY_API_KEY` - Perplexity API key - Default: None

**LangSmith (Tracing):**
- `LANGSMITH_API_KEY` - LangSmith API key - Default: None
- `LANGSMITH_PROJECT` - Project name - Default: "deep-agent-one"
- `LANGSMITH_ENDPOINT` - API endpoint - Default: "https://api.smith.langchain.com"
- `LANGSMITH_TRACING_V2` - Enable v2 tracing - Default: True

**Opik (Prompt Optimization):**
- `OPIK_API_KEY` - Opik API key - Default: None
- `OPIK_WORKSPACE` - Workspace name - Default: None
- `OPIK_PROJECT` - Project name - Default: "deep-agent-reasoning"

### Database Settings (Phase 1)

**PostgreSQL:**
- `DATABASE_URL` - Connection URL - Default: None
- `POSTGRES_USER` - Username - Default: None
- `POSTGRES_PASSWORD` - Password - Default: None
- `POSTGRES_DB` - Database name - Default: None
- `ENABLE_PGVECTOR` - Enable pgvector extension - Default: True

**Checkpointer (LangGraph State):**
- `CHECKPOINT_DB_PATH` - SQLite checkpoint path - Default: "data/checkpoints.db"
- `CHECKPOINT_CLEANUP_DAYS` - Checkpoint retention days - Default: 30

### Streaming & WebSocket

- `STREAM_VERSION` - LangGraph version (v1/v2) - Default: "v2"
- `STREAM_TIMEOUT_SECONDS` - WebSocket timeout - Default: 300
- `STREAM_ALLOWED_EVENTS` - Comma-separated event names - Default: "on_chat_model_stream,on_tool_start,on_tool_end,..."

### FastAPI Configuration

- `API_HOST` - Bind host - Default: "0.0.0.0"
- `API_PORT` - Bind port - Default: 8000
- `API_RELOAD` - Auto-reload on changes - Default: False
- `CORS_ORIGINS` - Comma-separated origins - Default: "http://localhost:3000,http://localhost:8000"
- `API_VERSION` - API version string - Default: "v1"

### MCP Servers

- `PLAYWRIGHT_HEADLESS` - Headless mode - Default: True
- `PLAYWRIGHT_BROWSERS_PATH` - Browser path - Default: "~/.cache/ms-playwright"
- `MCP_PERPLEXITY_TIMEOUT` - Perplexity timeout (seconds) - Default: 30
- `MCP_PLAYWRIGHT_TIMEOUT` - Playwright timeout (seconds) - Default: 60

### Tool Execution

- `TOOL_EXECUTION_TIMEOUT` - Tool timeout (seconds) - Default: 45
- `WEB_SEARCH_TIMEOUT` - Search timeout (seconds) - Default: 30

### Security

- `SECRET_KEY` - Application secret - Default: None
- `JWT_SECRET` - JWT signing secret - Default: None
- `JWT_ALGORITHM` - JWT algorithm - Default: "HS256"
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration - Default: 30
- `BCRYPT_ROUNDS` - Hashing rounds - Default: 12

### Rate Limiting

- `RATE_LIMIT_REQUESTS` - Requests per period - Default: 100
- `RATE_LIMIT_PERIOD` - Period (seconds) - Default: 3600
- `RATE_LIMIT_REASONING_HIGH` - High reasoning limit - Default: 10
- `RATE_LIMIT_REASONING_PERIOD` - Period (seconds) - Default: 3600

### Security Scanning (TheAuditor)

- `AUDITOR_ENABLED` - Enable security scanning - Default: True
- `AUDITOR_AUTO_SCAN` - Auto-run scans - Default: False
- `AUDITOR_SCAN_ON_DEPLOY` - Scan on deployment - Default: True

### Logging

- `LOG_LEVEL` - Level (DEBUG/INFO/WARNING/ERROR/CRITICAL) - Default: "INFO"
- `LOG_FORMAT` - Format (json/standard) - Default: "json"
- `ENABLE_STRUCTURED_LOGGING` - Enable JSON logging - Default: True
- `LOG_REASONING_DECISIONS` - Log reasoning decisions - Default: True

### Performance

- `MAX_CONCURRENT_REQUESTS` - Max concurrent requests - Default: 50
- `REQUEST_TIMEOUT` - Request timeout (seconds) - Default: 300
- `REASONING_QUEUE_SIZE` - Queue size - Default: 10
- `ENABLE_ASYNC_PROCESSING` - Enable async processing - Default: True

### Feature Flags

- `ENABLE_HITL` - Human-in-the-loop workflows - Default: True
- `ENABLE_SUB_AGENTS` - Sub-agent delegation - Default: True
- `ENABLE_RESEARCH_MODE` - Deep research mode (Phase 2) - Default: False
- `ENABLE_COST_TRACKING` - Cost tracking - Default: True
- `ENABLE_MEMORY_SYSTEM` - Memory system (Phase 1) - Default: False

### Development Tools

- `ENABLE_DEBUG_TOOLBAR` - Debug toolbar - Default: False
- `ENABLE_PROFILING` - Performance profiling - Default: False
- `MOCK_EXTERNAL_APIS` - Mock APIs for testing - Default: False

### Replit Integration

- `REPL_SLUG` - Replit slug - Default: None
- `REPL_OWNER` - Replit owner - Default: None

## Environment-Specific Behavior

Settings affect application behavior based on the `ENV` value:

### local / dev
- Debug logging enabled
- Verbose error messages
- Auto-reload on code changes
- Relaxed validation
- Mock external APIs (if enabled)

### staging
- Production-like configuration
- Test data and credentials
- Moderate logging
- Full validation

### production
- Strict validation
- Minimal logging (INFO level)
- Performance optimization
- No debug features
- Required: All production API keys

### test
- Testing mode
- Mock external APIs
- Relaxed timeouts
- Debug logging

## Validation

Pydantic validates all settings on application startup:

### Type Checking
All settings are type-checked against their annotations:
```python
DEBUG: bool = False  # Must be boolean
API_PORT: int = 8000  # Must be integer
```

### Required Fields
Fields without defaults must be provided:
```python
OPENAI_API_KEY: str = Field(...)  # Required
PERPLEXITY_API_KEY: Optional[str] = None  # Optional
```

### Custom Validators
Custom validation logic ensures data integrity:
```python
@field_validator("LOG_LEVEL")
def validate_log_level(cls, v: str) -> str:
    return v.upper()  # Normalize to uppercase
```

### Validation Errors
Missing or invalid settings cause startup failure with clear error messages:
```
ValidationError: 1 validation error for Settings
OPENAI_API_KEY
  field required (type=value_error.missing)
```

## Dependencies

### External Libraries
- **pydantic-settings** - Settings management and validation
- **python-dotenv** - .env file loading

### Internal Dependencies
- Used by `deep_agent.core` - Core LLM and reasoning logic
- Used by `deep_agent.services` - Service initialization
- Used by `deep_agent.api` - FastAPI configuration

## Related Documentation

- [Core](../core/README.md) - Core LLM and reasoning components
- [Services](../services/README.md) - Service layer using configuration
- [API](../api/README.md) - FastAPI endpoints using configuration
- [Tools](../tools/README.md) - Tool configuration and timeouts

## Testing

### Unit Tests
```bash
# Test config loading and validation
pytest tests/unit/test_config/
```

### Test Files
- `tests/unit/test_config/test_settings.py` - Settings validation tests
- `tests/unit/test_config/test_env_loading.py` - Environment variable tests

### Example Test
```python
def test_settings_with_custom_values():
    """Test Settings instantiation with custom values."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        ENV="test",
        DEBUG=True
    )

    assert settings.OPENAI_API_KEY == "test-key"
    assert settings.ENV == "test"
    assert settings.DEBUG is True


def test_get_settings_singleton():
    """Test get_settings returns same instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
```

## Best Practices

### 1. Use get_settings() for Application Code
```python
# Good: Use singleton
from deep_agent.config import get_settings

settings = get_settings()
```

### 2. Use Settings() for Tests
```python
# Good: Custom settings per test
from deep_agent.config import Settings

test_settings = Settings(OPENAI_API_KEY="test")
```

### 3. Never Hardcode Secrets
```python
# Bad: Hardcoded secret
api_key = "sk-proj-abc123..."

# Good: Load from settings
api_key = settings.OPENAI_API_KEY
```

### 4. Use Type Hints
```python
from deep_agent.config import Settings

def process_request(settings: Settings) -> None:
    # Type hints enable IDE autocomplete
    api_key = settings.OPENAI_API_KEY
```

### 5. Document New Settings
When adding new settings:
1. Add type annotation and default value
2. Document in Settings class docstring
3. Add to this README under appropriate section
4. Update `.env.example` with example value
5. Add validation if needed

## Troubleshooting

### Missing Required Settings
```
ValidationError: OPENAI_API_KEY field required
```
**Solution:** Add `OPENAI_API_KEY=sk-...` to `.env` file

### Invalid Type
```
ValidationError: value is not a valid integer
```
**Solution:** Check environment variable type (e.g., `API_PORT=8000` not `API_PORT=8000.0`)

### Settings Not Loading
```python
# Check if .env file exists
import os
print(os.path.exists(".env"))  # Should be True

# Check environment variable
print(os.getenv("OPENAI_API_KEY"))  # Should show key
```

### Cache Issues in Tests
```python
# Clear singleton cache between tests
from deep_agent.config import get_settings

get_settings.cache_clear()
```

## Future Enhancements (Phase 1+)

- [ ] Secrets management integration (AWS Secrets Manager, HashiCorp Vault)
- [ ] Dynamic configuration reloading
- [ ] Configuration versioning and rollback
- [ ] Per-user settings override
- [ ] Environment-specific validation rules
- [ ] Configuration change audit logging
