# Components

## Purpose

Reusable UI components for Deep Agent One frontend built with React, TypeScript, and Tailwind CSS.

This directory contains all React components organized by category:
- **AG-UI Components**: Agent-specific UI implementing the AG-UI Protocol
- **Common Components**: Shared components used across the app
- **UI Components**: shadcn/ui primitive components built on Radix UI

## Component Categories

### AG-UI Components (`ag-ui/`)

Agent-specific components implementing the AG-UI Protocol for Phase 0 MVP.

#### `AgentStatus.tsx`
**Purpose:** Displays comprehensive agent execution status.

**Features:**
- Current execution state (idle, running, waiting_for_approval, completed, error)
- WebSocket connection status indicator
- GPT-5 reasoning effort level (low/medium/high)
- Model information display
- Token usage statistics
- Active thread ID (for debugging)
- Real-time updates via WebSocket events
- Color-coded status badges with animations

**Usage:**
```tsx
import AgentStatus from '@/components/ag-ui/AgentStatus';

<AgentStatus />
```

**Dependencies:**
- `@/hooks/useAgentState` - Access to agent state
- `@/hooks/useWebSocketContext` - WebSocket connection status
- `@/types/agent` - Type definitions
- Card, Badge, Separator UI components
- lucide-react icons

---

#### `ProgressTracker.tsx`
**Purpose:** Displays real-time agent execution progress with ordered list of steps.

**Features:**
- Visual timeline with status icons
- Step status indicators (pending, running, completed, error)
- Timestamps (started_at, completed_at)
- Execution duration calculation
- Step counters (completed, running, errors)
- Metadata display for each step
- Scrollable step list (max 400px height)
- Animated progress indicator for current step
- Empty state when no steps

**Usage:**
```tsx
import ProgressTracker from '@/components/ag-ui/ProgressTracker';

<ProgressTracker />
```

**Dependencies:**
- `@/hooks/useAgentState` - Access to agent steps
- `@/types/agent` - Type definitions
- Card, Badge, ScrollArea, Separator UI components
- lucide-react icons

---

#### `ToolCallDisplay.tsx`
**Purpose:** Displays tool calls with full transparency ("inspect source" view).

**Features:**
- Collapsible accordion for each tool call
- Syntax-highlighted JSON for arguments and results
- Copy-to-clipboard functionality
- Status indicators (pending, running, completed, error)
- Error details with type and message
- Execution timing display
- Scrollable tool call list (max 600px height)
- Empty state when no tool calls

**Usage:**
```tsx
import ToolCallDisplay from '@/components/ag-ui/ToolCallDisplay';

<ToolCallDisplay />
```

**Dependencies:**
- `@/hooks/useAgentState` - Access to tool calls
- `@/types/agent` - Type definitions
- Card, Accordion, Badge, Button, ScrollArea UI components
- lucide-react icons

---

### Common Components (`common/`)

Shared components used across the application.

#### `ErrorDisplay.tsx`
**Purpose:** Displays error messages from AG-UI Protocol error events.

**Features:**
- Normalized error display using errorEventAdapter
- Error type, code, and message display
- Run ID and Request ID (shown in development mode only)
- Consistent error formatting
- Destructive alert styling

**Usage:**
```tsx
import { ErrorDisplay, ErrorDisplayFromEvent } from '@/components/common/ErrorDisplay';

// Direct usage with normalized error
<ErrorDisplay
  message="Connection failed"
  type="WebSocketError"
  code="WS_CLOSED"
/>

// Convenience wrapper that normalizes AG-UI event
<ErrorDisplayFromEvent event={errorEvent} />
```

**Dependencies:**
- `@/lib/errorEventAdapter` - Error normalization utility
- `@/types/ag-ui` - AG-UI event types
- Alert UI components
- lucide-react icons

---

### UI Components (`ui/`)

shadcn/ui primitive components built on Radix UI and Tailwind CSS.

These are low-level, reusable components following shadcn/ui conventions.

#### Core Components

**`button.tsx`** - Flexible button with variants (default, destructive, outline, secondary, ghost, link) and sizes (default, sm, lg, icon)

**`card.tsx`** - Container component with Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter

**`input.tsx`** - Text input field

**`textarea.tsx`** - Multi-line text input

**`badge.tsx`** - Small status indicator

**`avatar.tsx`** - User profile image placeholder

**`alert.tsx`** - Alert message container

**`separator.tsx`** - Visual divider line

**`tooltip.tsx`** - Hover tooltip

**`dropdown-menu.tsx`** - Dropdown menu with Radix UI

**`accordion.tsx`** - Collapsible content sections

**`scroll-area.tsx`** - Scrollable container with custom scrollbar styling

#### Usage Example

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        <Badge variant="secondary">Status</Badge>
        <Button variant="default">Click me</Button>
      </CardContent>
    </Card>
  );
}
```

---

## Importing Components

### AG-UI Components
```tsx
import AgentStatus from '@/components/ag-ui/AgentStatus';
import ProgressTracker from '@/components/ag-ui/ProgressTracker';
import ToolCallDisplay from '@/components/ag-ui/ToolCallDisplay';
```

### Common Components
```tsx
import { ErrorDisplay } from '@/components/common/ErrorDisplay';
```

### UI Components (shadcn/ui)
```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
```

---

## Component Patterns

### Server vs Client Components

**Server Components (default in Next.js 13+ App Router):**
- Static UI, no interactivity
- Rendered on the server
- Cannot use hooks or browser APIs
- Better performance (smaller bundle size)

**Client Components (marked with `'use client'`):**
- Interactive UI with state management
- Access to React hooks (useState, useEffect, useContext)
- Access to browser APIs (localStorage, WebSocket)
- Event handlers (onClick, onChange, etc.)

**Examples:**
```tsx
// Server Component (no directive needed)
export default function StaticCard() {
  return <Card><CardContent>Static content</CardContent></Card>;
}

// Client Component (needs 'use client' directive)
'use client';

export default function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <Button onClick={() => setCount(count + 1)}>Count: {count}</Button>;
}
```

### State Management

**Local State (useState):**
```tsx
const [isOpen, setIsOpen] = useState(false);
```

**Context State:**
```tsx
const { active_thread_id, threads } = useAgentState();
const { connectionStatus } = useWebSocketContext();
```

**AG-UI Protocol Hooks:**
- `useAgentState()` - Access agent threads, steps, messages, tool calls
- `useWebSocketContext()` - WebSocket connection status and management

### Styling

**Tailwind CSS Utility Classes:**
```tsx
<div className="flex items-center gap-2 p-4 rounded-lg bg-muted">
  {/* Content */}
</div>
```

**shadcn/ui Variants (CVA):**
```tsx
<Button variant="destructive" size="lg">Delete</Button>
<Badge variant="outline">Status</Badge>
```

**Conditional Classes:**
```tsx
<div className={cn(
  "base-classes",
  isActive && "active-classes",
  className // Prop-based override
)}>
  {/* Content */}
</div>
```

---

## Dependencies

### Core React
- `react` - React library
- `react-dom` - React DOM rendering

### UI Libraries
- `@radix-ui/*` - Headless UI primitives (Slot, Accordion, DropdownMenu, etc.)
- `class-variance-authority` - CVA for component variants
- `tailwindcss` - Utility-first CSS framework
- `lucide-react` - Icon library

### Type System
- `typescript` - Type checking
- `@types/react` - React type definitions

### Custom Utilities
- `@/lib/utils` - cn() function for className merging
- `@/lib/errorEventAdapter` - Error normalization
- `@/hooks/useAgentState` - Agent state management
- `@/hooks/useWebSocketContext` - WebSocket context

---

## Related Documentation

- [App Router](../app/README.md) - Next.js pages and layouts
- [Hooks](../hooks/README.md) - Custom React hooks
- [Utilities](../lib/README.md) - Utility functions
- [Frontend Root](../README.md) - Frontend overview

---

## Testing

### Unit Tests
**Location:** `tests/unit/frontend/components/`

Test individual component rendering, props, and behavior.

### Integration Tests
**Location:** `tests/integration/frontend/`

Test component interactions with hooks and context providers.

### UI Tests
**Location:** `tests/ui/`

Automated browser testing with Playwright MCP.

**Status:** Component tests planned for Phase 1.

---

## Contributing

### Creating New Components

1. **Determine component type:**
   - AG-UI component (agent-specific) → `ag-ui/`
   - Shared/common component → `common/`
   - UI primitive (shadcn/ui) → `ui/`

2. **Add JSDoc comments:**
   - File-level doc comment explaining purpose
   - Function/interface doc comments with `@param`, `@returns`, `@example`
   - Inline comments for complex logic

3. **Follow naming conventions:**
   - PascalCase for component files and names
   - Use descriptive names (e.g., `AgentStatus`, not `Status`)

4. **Use TypeScript:**
   - Define prop interfaces with JSDoc
   - Use React.forwardRef for ref forwarding
   - Export types for external use

5. **Add examples:**
   - Include usage examples in JSDoc
   - Show common patterns and edge cases

### Code Quality Standards

- **Type Safety:** All props and state fully typed
- **Accessibility:** WCAG AA compliance
- **Responsive:** Mobile-first design
- **Performance:** Memoization for expensive operations
- **Testing:** 80%+ test coverage requirement (Phase 1)

### Example Component Structure

```tsx
/**
 * MyComponent Component
 *
 * Description of what this component does and when to use it.
 *
 * Features:
 * - Feature 1
 * - Feature 2
 */

'use client'; // Only if needed (interactivity)

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import type { MyType } from '@/types/my-types';

/**
 * Props for MyComponent.
 */
export interface MyComponentProps {
  /** Description of prop */
  title: string;
  /** Optional prop with default */
  variant?: 'default' | 'outline';
}

/**
 * MyComponent implementation.
 *
 * @param props - Component props
 * @param props.title - Title to display
 * @param props.variant - Visual variant
 *
 * @example
 * ```tsx
 * <MyComponent title="Hello" variant="outline" />
 * ```
 */
export default function MyComponent({
  title,
  variant = 'default'
}: MyComponentProps) {
  return (
    <div>
      <h1>{title}</h1>
      <Button variant={variant}>Click me</Button>
    </div>
  );
}
```

---

## Architecture Notes

### AG-UI Protocol Implementation

The `ag-ui/` components implement the AG-UI Protocol specification:

**Event Types:**
- **Lifecycle:** RunStarted, RunFinished, RunError
- **Steps:** StepStarted, StepFinished
- **Messages:** TextMessageStart, TextMessageContent, TextMessageEnd
- **Tools:** ToolCallStart, ToolCallArgs, ToolCallEnd, ToolCallResult

**Data Flow:**
1. WebSocket receives AG-UI events from backend
2. Events update global agent state via useAgentState hook
3. Components subscribe to state changes via hook
4. Components re-render with updated data

**State Management:**
- Global state: `AgentStateContext` (threads, steps, messages, tool calls)
- WebSocket state: `WebSocketContext` (connection status, send/disconnect)
- Local state: Component-specific UI state (collapsed/expanded, copied, etc.)

### Performance Considerations

- **Memoization:** Use React.memo() for expensive components (planned Phase 1)
- **Virtual Scrolling:** Consider for large lists (planned Phase 1)
- **Code Splitting:** Dynamic imports for heavy components (planned Phase 1)
- **Bundle Size:** Tree-shaking for unused UI components

---

## Roadmap

### Phase 0 (Current)
- ✅ AG-UI components (AgentStatus, ProgressTracker, ToolCallDisplay)
- ✅ ErrorDisplay component
- ✅ shadcn/ui primitives (Button, Card, Badge, etc.)
- ✅ JSDoc documentation

### Phase 1 (Next)
- [ ] Component unit tests (80%+ coverage)
- [ ] Playwright UI tests
- [ ] HITL approval dialog component
- [ ] Custom AG-UI components exploration
- [ ] Performance optimizations (memoization, virtual scrolling)
- [ ] Accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Storybook for component documentation

### Phase 2
- [ ] Advanced visualization components
- [ ] Custom event visualizers (tool call timeline, reasoning display)
- [ ] Company-specific branding components

---

## Troubleshooting

### Common Issues

**Issue:** Component not updating with new data
**Solution:** Verify component is wrapped in WebSocketProvider and AgentStateProvider

**Issue:** "Cannot use hooks" error
**Solution:** Add `'use client'` directive at top of file

**Issue:** TypeScript errors on component props
**Solution:** Check import paths and type definitions in `@/types`

**Issue:** Styling not applied
**Solution:** Verify Tailwind CSS classes are correct and not purged (check tailwind.config.ts)

---

## References

- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [AG-UI Protocol Documentation](https://docs.ag-ui.com/sdk/python/core/overview)
