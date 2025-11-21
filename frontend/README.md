# Frontend

## Purpose

Next.js 14 application providing the Deep Agent AGI user interface with AG-UI Protocol integration for real-time agent interactions.

The frontend serves as the presentation layer for the Deep Agent AGI system, handling:
- Real-time agent communication via WebSocket
- Streaming text responses from GPT-5
- Tool execution visualization
- Human-in-the-loop (HITL) approval workflows
- Responsive, accessible user experience

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3+
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: React hooks + Zustand
- **Real-time**: WebSocket (AG-UI Protocol)
- **Testing**: Jest (unit/integration) + Playwright (E2E)
- **Icons**: Lucide React
- **Validation**: Zod

## Directory Structure

```
frontend/
├── app/                    # Next.js App Router pages and layouts
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page (chat interface)
│   ├── globals.css        # Global styles and CSS variables
│   └── api/               # Next.js API routes (future)
│
├── components/            # Reusable UI components
│   ├── ui/                # shadcn/ui primitives (Button, Card, etc.)
│   ├── chat/              # Chat-specific components
│   ├── agent/             # Agent-related components (status, tools)
│   └── layout/            # Layout components (Header, Footer)
│
├── hooks/                 # Custom React hooks
│   ├── useWebSocket.ts    # WebSocket connection management
│   ├── useAgentState.ts   # Agent state tracking
│   └── useChat.ts         # Chat message handling
│
├── lib/                   # Utility libraries and helpers
│   ├── utils.ts           # General utilities (cn, formatters)
│   ├── agui.ts            # AG-UI Protocol event handling
│   ├── api.ts             # Backend API client
│   └── types.ts           # Shared TypeScript types
│
├── types/                 # TypeScript type definitions
│   ├── agent.ts           # Agent-related types
│   ├── chat.ts            # Chat message types
│   └── events.ts          # AG-UI event types
│
├── contexts/              # React context providers
│   └── WebSocketContext.tsx  # WebSocket provider
│
├── __tests__/             # Unit and integration tests
├── e2e/                   # Playwright E2E tests
├── public/                # Static assets (images, fonts)
│
├── next.config.js         # Next.js configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
├── jest.config.js         # Jest test configuration
├── playwright.config.ts   # Playwright E2E configuration
└── components.json        # shadcn/ui configuration
```

## Quick Start

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+
- Backend server running on http://localhost:8000 (see `../backend/README.md`)

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Copy `.env.local.example` to `.env.local` and configure:

```bash
cp .env.local.example .env.local
```

Key variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_ENV`: Environment (development, staging, production)

See `.env.local.example` for full configuration options.

### Development

```bash
npm run dev
```

Opens on http://localhost:3000 with hot module replacement.

### Production Build

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

Runs TypeScript compiler in no-emit mode to check for type errors.

### Linting

```bash
npm run lint          # Check for issues
npm run lint:fix      # Auto-fix issues
```

## Testing

### Unit and Integration Tests (Jest)

```bash
npm test                  # Run all tests
npm run test:watch        # Watch mode for development
npm run test:coverage     # Generate coverage report
```

**Coverage Requirements:** 80% minimum (statements, branches, functions, lines)

**Test Structure:**
- `__tests__/components/` - Component tests
- `__tests__/hooks/` - Hook tests
- `__tests__/lib/` - Utility function tests

### E2E Tests (Playwright)

```bash
npm run test:ui           # Run E2E tests (headless)
npm run test:ui:headed    # Run with browser visible
npm run test:ui:debug     # Debug mode with Playwright Inspector
```

**Test Structure:**
- `e2e/chat.spec.ts` - Chat interface tests
- `e2e/agent.spec.ts` - Agent interaction tests
- `e2e/hitl.spec.ts` - HITL workflow tests

**Browsers:** Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari

## Key Features

### Real-time Agent Communication

The frontend uses WebSocket connections to communicate with the backend agent service. The `useWebSocket` hook manages:
- Connection establishment and reconnection
- Event streaming (AG-UI Protocol)
- Error handling and recovery
- Connection state tracking

### AG-UI Protocol Events

The application handles the following AG-UI event types:

**Lifecycle Events:**
- `RunStarted` - Agent run begins
- `RunFinished` - Agent run completes
- `RunError` - Agent run fails
- `StepStarted` - Agent step begins
- `StepFinished` - Agent step completes

**Message Events:**
- `TextMessageStart` - Streaming text begins
- `TextMessageContent` - Text chunk received
- `TextMessageEnd` - Streaming text complete

**Tool Events:**
- `ToolCallStart` - Tool execution begins
- `ToolCallArgs` - Tool arguments received
- `ToolCallEnd` - Tool execution complete
- `ToolCallResult` - Tool result available

**HITL Events:**
- Custom events for human approval workflows

### Component Architecture

The application follows a component-based architecture:

1. **UI Primitives** (`components/ui/`): shadcn/ui components (Button, Card, etc.)
2. **Feature Components** (`components/chat/`, `components/agent/`): Domain-specific components
3. **Layout Components** (`components/layout/`): Page structure (Header, Footer)
4. **Hooks** (`hooks/`): Reusable logic (useWebSocket, useChat, useAgentState)
5. **Context Providers** (`contexts/`): Global state (WebSocket connection)

### Styling System

The application uses Tailwind CSS with shadcn/ui for consistent styling:

- **CSS Variables**: Defined in `app/globals.css` for theming
- **Dark Mode**: Planned for Phase 1 (infrastructure ready)
- **Responsive Design**: Mobile-first approach with Tailwind breakpoints
- **Animations**: Custom animations defined in `tailwind.config.js`

### Accessibility

The frontend follows WCAG 2.1 AA guidelines:

- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation support
- Focus management
- Screen reader compatibility

## Architecture

### Data Flow

```
User Input
    ↓
ChatInput Component
    ↓
useChat Hook
    ↓
WebSocket (send message)
    ↓
Backend Agent Service
    ↓
WebSocket (receive events)
    ↓
useWebSocket Hook
    ↓
AG-UI Event Handler
    ↓
State Updates (Zustand)
    ↓
React Re-render
    ↓
UI Update
```

### State Management

The application uses a combination of:

1. **React Context**: WebSocket connection (global)
2. **Zustand**: Chat messages, agent state (global)
3. **useState**: Local component state
4. **useReducer**: Complex component state

### Security

**Security Headers** (via `middleware.ts`):
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Restricted browser features
- Content-Security-Policy: Strict CSP for API routes

**Input Sanitization**:
- DOMPurify for HTML sanitization
- Zod validation for user inputs
- CSRF protection (planned Phase 1)

**WebSocket Security**:
- Authentication tokens (planned Phase 1)
- Message validation
- Rate limiting (backend)

## Configuration Files

### next.config.js

Configures Next.js with:
- WebSocket support (webpack externals)
- API request proxying
- Security headers
- Package import optimization

### tsconfig.json

TypeScript configuration with:
- Strict mode enabled
- Path aliases (@/ imports)
- Next.js plugin integration
- Strict linting rules

### tailwind.config.js

Tailwind CSS configuration with:
- shadcn/ui design tokens
- Custom animations
- Dark mode support (class strategy)
- Responsive container defaults

### jest.config.js

Jest configuration for unit/integration tests:
- jsdom test environment
- Path alias resolution
- Coverage thresholds (80%)
- Mock setup for Next.js

### playwright.config.ts

Playwright configuration for E2E tests:
- Multi-browser testing (Chromium, Firefox, WebKit)
- Mobile viewport testing (Chrome, Safari)
- Parallel execution
- Screenshot and video on failure
- Trace on retry

## Dependencies

### Core Dependencies

- **next** (^14.2.0): Next.js framework
- **react** (^18.3.1): React library
- **typescript** (^5.3.0): TypeScript compiler
- **@ag-ui/core** (^0.0.39): AG-UI Protocol SDK
- **zod** (^3.25.76): Schema validation
- **zustand** (^4.5.0): State management

### UI Dependencies

- **tailwindcss** (^3.4.0): Utility-first CSS
- **@radix-ui/react-*** (^1.x): Headless UI primitives
- **lucide-react** (^0.344.0): Icon library
- **class-variance-authority** (^0.7.1): Variant styling
- **tailwind-merge** (^2.6.0): Tailwind class merging
- **clsx** (^2.1.1): Class name utility

### Testing Dependencies

- **jest** (^30.2.0): Test runner
- **@testing-library/react** (^16.3.0): React testing utilities
- **@testing-library/jest-dom** (^6.9.1): Jest DOM matchers
- **@playwright/test** (^1.56.1): E2E testing framework

## Performance

### Optimizations

- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Next.js Font loading
- **Package Optimization**: Enabled for lucide-react, @radix-ui
- **Tree Shaking**: Automatic in production builds
- **Minification**: Automatic in production builds

### Metrics (Phase 0 Targets)

- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.0s
- **Cumulative Layout Shift (CLS)**: < 0.1

## Troubleshooting

### WebSocket Connection Issues

**Problem**: WebSocket fails to connect or disconnects frequently

**Solutions**:
1. Verify backend server is running: `curl http://localhost:8000/health`
2. Check NEXT_PUBLIC_API_URL in `.env.local`
3. Review browser console for WebSocket errors
4. Check backend logs for connection errors
5. Disable React Strict Mode temporarily (Phase 0 workaround)

### Build Errors

**Problem**: `npm run build` fails

**Solutions**:
1. Run `npm run type-check` to identify TypeScript errors
2. Clear Next.js cache: `rm -rf .next`
3. Reinstall dependencies: `rm -rf node_modules && npm install`
4. Check for syntax errors in configuration files

### Test Failures

**Problem**: Jest tests fail

**Solutions**:
1. Check mock setup in `jest.setup.js`
2. Verify environment variables in test environment
3. Clear Jest cache: `jest --clearCache`
4. Run tests individually: `npm test -- <test-file-name>`

## Phase 0 Status

### Completed Features ✓

- [x] Next.js 14 App Router setup
- [x] TypeScript strict mode configuration
- [x] Tailwind CSS + shadcn/ui integration
- [x] WebSocket connection management
- [x] AG-UI Protocol event handling
- [x] Basic chat interface
- [x] Tool execution visualization
- [x] HITL approval UI
- [x] Security headers (middleware)
- [x] Jest unit/integration testing
- [x] Playwright E2E testing
- [x] Test coverage reporting

### Planned for Phase 1

- [ ] Authentication UI (OAuth 2.0)
- [ ] Memory retrieval visualization
- [ ] Provenance source display
- [ ] Dark mode toggle
- [ ] Advanced HITL workflows
- [ ] Custom AG-UI components (TypeScript)
- [ ] Error boundary improvements
- [ ] Loading state enhancements
- [ ] Reconnection logic for WebSocket
- [ ] Progress indicators for long-running tools

## Related Documentation

- [App Router](app/README.md)
- [Components](components/README.md)
- [Hooks](hooks/README.md)
- [Utilities](lib/README.md)
- [Backend API](../backend/deep_agent/api/README.md)
- [AG-UI Protocol](https://docs.ag-ui.com/sdk/python/core/overview)
- [Next.js Documentation](https://nextjs.org/docs)

## Contributing

### Code Style

- Follow TypeScript best practices
- Use functional components with hooks
- Prefer composition over inheritance
- Write self-documenting code with clear naming
- Add JSDoc comments for exported functions
- Use Tailwind CSS utility classes (avoid inline styles)

### Testing Requirements

- Write tests for all new components and hooks
- Maintain 80%+ test coverage
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Test error states and edge cases

### Commit Guidelines

- Use semantic commit messages (feat, fix, test, refactor, docs, chore)
- Run `npm run type-check` before committing
- Run `npm test` before committing
- Keep commits atomic and focused

## Support

For issues, questions, or contributions:
- Review existing documentation in `docs/`
- Check GitHub Issues for known problems
- Contact the development team

---

**Last Updated**: 2025-11-12 (Phase 0)
**Version**: 0.1.0-phase0
