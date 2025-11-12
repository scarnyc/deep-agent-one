# User Guides

## Purpose
End-user documentation and guides for using the Deep Agent AGI system.

## Contents

### Planned Documentation (Phase 1+)
- Getting started guide
- Chat interface guide
- Agent capabilities overview
- Tool usage examples
- Human-in-the-loop (HITL) workflow guide
- Troubleshooting common issues
- Best practices for interacting with agents
- FAQ

## Quick Start (Phase 0)

### Accessing the System
1. Open your browser to `http://localhost:3000` (development)
2. The chat interface will load automatically
3. Start typing your message in the input field
4. Press Enter or click Send to interact with the agent

### Basic Chat
```
User: Hello! What can you help me with?
Agent: I'm a general-purpose AI agent that can help you with various tasks...
```

### Using Tools
The agent has access to several tools:
- **File System Tools:** Read, write, and edit files
- **Planning Tool:** Create and track subtasks
- **Web Search:** Search the web using Perplexity
- **Sub-Agents:** Delegate tasks to specialized agents

### Human-in-the-Loop (HITL)
When the agent needs approval:
1. You'll see an approval request in the UI
2. Review the proposed action
3. Choose: Accept, Respond, or Edit
4. The agent will continue after your decision

## Advanced Features (Phase 1+)

### Deep Reasoning
- Complex queries trigger deeper reasoning
- Longer response times for better quality
- Reasoning process visible in UI

### Memory System
- Agent remembers context from previous conversations
- Semantic search for relevant past interactions
- Context retrieval for better responses

### Web Search Integration
- Real-time web search capabilities
- Citation tracking and provenance
- Confidence scores for search results

## Agent Capabilities

### Phase 0 Capabilities
- **Chat:** Conversational interactions
- **File Operations:** Read, write, edit files
- **Planning:** Create and track task plans
- **Web Search:** Search using Perplexity MCP
- **HITL:** Human approval workflows

### Phase 1+ Capabilities (Planned)
- **Variable Reasoning:** Automatic reasoning effort optimization
- **Memory:** Long-term memory with semantic search
- **Provenance:** Source tracking and citations
- **Authentication:** Secure user accounts
- **Research:** Deep research workflows

## Best Practices

### Writing Effective Prompts
- Be specific about what you want
- Provide context when needed
- Break complex tasks into steps
- Review agent plans before approval

### Working with HITL
- Review proposed actions carefully
- Provide feedback if the plan isn't right
- Use "Edit" to refine the agent's approach
- Trust the agent for straightforward tasks

### Managing Conversations
- Start new threads for different topics
- Reference previous context when needed
- Clear threads if context becomes too large

## Troubleshooting

### Common Issues

#### Agent Not Responding
- Check WebSocket connection status
- Refresh the page
- Check backend logs

#### Slow Responses
- Complex queries take longer
- Deep reasoning increases response time
- Check API rate limits

#### Tool Execution Errors
- Review tool permissions
- Check file paths are correct
- Verify external services are accessible

### Getting Help
- Check FAQ section (planned)
- Review error messages in UI
- Contact support (when available)

## FAQ (Planned)

### General Questions
- What is Deep Agent AGI?
- How does it work?
- What can it do?
- Is it free?

### Technical Questions
- What LLM does it use?
- How is data stored?
- Is my data private?
- Can I run it locally?

### Usage Questions
- How do I start a conversation?
- How do I approve agent actions?
- How do I use tools?
- How do I improve responses?

## Examples (Planned)

### Example Workflows
- Simple Q&A conversation
- File operations workflow
- Web research task
- Multi-step planning example
- HITL approval workflow

### Code Examples
- Python integration
- JavaScript integration
- API usage examples
- Custom tool creation

## Updates & Changelog

### Phase 0 (Current)
- Basic chat interface
- File system tools
- Planning tool
- Web search integration
- HITL approval workflow
- WebSocket streaming

### Phase 1 (Planned)
- Variable reasoning effort
- Memory system with pgvector
- Authentication & IAM
- Provenance tracking
- Enhanced UI components

### Phase 2 (Planned)
- Deep research capabilities
- Custom MCP servers
- Advanced security features
- Multi-user support

## Related Documentation
- [Development](../development/)
- [API](../api/)
- [Architecture](../architecture/)
- [Main README](../../README.md)

## Feedback

We welcome feedback on the documentation and the system:
- Report issues on GitHub
- Suggest improvements
- Share your use cases
- Contribute examples

## License & Legal

### License
See [LICENSE](../../LICENSE) file for details.

### Privacy
User privacy and data protection information (planned).

### Terms of Service
Terms of service (planned for production deployment).
