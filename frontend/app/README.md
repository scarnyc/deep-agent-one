# App (Next.js App Router)

## Purpose
Next.js 14 App Router pages and layouts for Deep Agent AGI UI. This directory contains all route definitions, page components, and layouts that make up the application's routing structure.

## Directory Structure
```
app/
├── layout.tsx          # Root layout (wraps all pages, provides fonts + metadata)
├── page.tsx            # Home page (/) - Landing page with CTA
├── globals.css         # Global styles (Tailwind base, components, utilities)
├── providers.tsx       # Client-side providers (ErrorBoundary + WebSocketProvider)
├── chat/               # Chat interface route
│   ├── page.tsx        # Chat page (/chat) - Main user interaction
│   └── components/     # Chat-specific components
│       └── ChatInterface.tsx
├── test-ag-ui/         # Component testing route
│   └── page.tsx        # Test page (/test-ag-ui) - AG-UI component testing
├── api/                # API routes (if needed)
└── __tests__/          # Tests for app-level components
```

## Routes

### Public Routes
- **`/`** - Home page (landing page with "Start Chat" CTA)
  - Server Component (static)
  - Displays application title and description
  - Navigates to `/chat` on button click
  - File: `page.tsx`

- **`/chat`** - Main chat interface
  - Client Component (interactive)
  - WebSocket connection for real-time agent communication
  - 3-column layout: AgentStatus + ProgressTracker | ChatInterface | ToolCallDisplay
  - Thread initialization on mount
  - Error boundary for graceful error handling
  - File: `chat/page.tsx`

### Development Routes
- **`/test-ag-ui`** - AG-UI component testing page
  - Client Component (interactive)
  - Manual testing controls for AG-UI components
  - Mock data injection for testing
  - 3-column layout showing all components side-by-side
  - File: `test-ag-ui/page.tsx`

## App Router Features

### Server Components by Default
All components in the app directory are Server Components unless marked with `'use client'`. This provides:
- Automatic code splitting
- Zero JavaScript sent to client (for static components)
- Direct database access (if needed)
- Improved performance and SEO

### Nested Layouts
Layouts wrap child pages and persist across navigation:
- **Root Layout** (`layout.tsx`): Wraps entire app, provides HTML structure, fonts, metadata
- **Child Layouts**: Can be nested in route folders for route-specific layouts

### Loading States
- Automatic loading UI with `loading.tsx` (not yet implemented)
- Manual loading state in chat page during thread initialization

### Error Boundaries
- Page-level error boundaries in `chat/page.tsx` and `test-ag-ui/page.tsx`
- Root-level error boundary in `providers.tsx`
- Graceful error handling with retry mechanism

### Metadata API
Static metadata in `layout.tsx`:
```tsx
export const metadata: Metadata = {
  title: 'Deep Agent AGI',
  description: 'General-purpose deep agent framework with cost optimization',
};
```

## Usage

### Creating a New Page

**Server Component (default):**
```tsx
// app/example/page.tsx
export default function ExamplePage() {
  return (
    <main>
      <h1>Example Page</h1>
      <p>This is a server component (static rendering).</p>
    </main>
  );
}
```

**Client Component (interactive):**
```tsx
// app/interactive/page.tsx
'use client';

import { useState } from 'react';

export default function InteractivePage() {
  const [count, setCount] = useState(0);

  return (
    <main>
      <h1>Interactive Page</h1>
      <button onClick={() => setCount(count + 1)}>
        Count: {count}
      </button>
    </main>
  );
}
```

### Layout Composition

**Root Layout** (`app/layout.tsx`):
```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

**Nested Layout** (example):
```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <nav>Dashboard Nav</nav>
      <main>{children}</main>
    </div>
  );
}
```

### Adding Metadata
```tsx
// Static metadata
export const metadata: Metadata = {
  title: 'Page Title',
  description: 'Page description for SEO',
};

// Dynamic metadata
export async function generateMetadata({ params }): Promise<Metadata> {
  return {
    title: `Item ${params.id}`,
  };
}
```

## Styling

### Tailwind CSS Utility Classes
All components use Tailwind utility classes for styling:
```tsx
<div className="flex items-center justify-center min-h-screen p-4 bg-background">
  <h1 className="text-4xl font-bold mb-4 text-foreground">Title</h1>
</div>
```

### Global Styles (`globals.css`)
- Tailwind directives: `@tailwind base`, `@tailwind components`, `@tailwind utilities`
- CSS variables for theming (light/dark mode support)
- Global resets and base styles

### Component-Specific Styles
- Use CSS modules for component-specific styles: `ComponentName.module.css`
- Co-locate with component files
- Example: `chat/components/ChatInterface.module.css`

## Data Fetching

### Server Components (Static Data)
```tsx
// app/posts/page.tsx
async function getPosts() {
  const res = await fetch('https://api.example.com/posts');
  return res.json();
}

export default async function PostsPage() {
  const posts = await getPosts();
  return <ul>{posts.map(post => <li key={post.id}>{post.title}</li>)}</ul>;
}
```

### Client Components (Real-Time Data)
```tsx
'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/contexts/WebSocketProvider';

export default function RealTimePage() {
  const { sendMessage, lastMessage } = useWebSocket();

  useEffect(() => {
    if (lastMessage) {
      // Process WebSocket message
    }
  }, [lastMessage]);

  return <div>Real-time content</div>;
}
```

## Navigation

### Link Component (Client-Side Navigation)
```tsx
import Link from 'next/link';

<Link href="/chat">Go to Chat</Link>
```

### Programmatic Navigation
```tsx
'use client';

import { useRouter } from 'next/navigation';

export default function Component() {
  const router = useRouter();

  const handleNavigate = () => {
    router.push('/chat');
  };

  return <button onClick={handleNavigate}>Navigate</button>;
}
```

## Client-Side State Management

### Zustand Store (useAgentState)
Centralized state management for agent data:
```tsx
'use client';

import { useAgentState } from '@/hooks/useAgentState';

export default function Component() {
  const { messages, addMessage, active_thread_id } = useAgentState();

  return <div>{messages.length} messages</div>;
}
```

### WebSocket Context
Real-time communication with backend:
```tsx
'use client';

import { useWebSocket } from '@/contexts/WebSocketProvider';

export default function Component() {
  const { sendMessage, isConnected } = useWebSocket();

  return (
    <button onClick={() => sendMessage({ type: 'chat', content: 'Hello' })}>
      Send Message
    </button>
  );
}
```

## Error Handling

### Page-Level Error Boundary
```tsx
'use client';

import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={resetErrorBoundary}>Try Again</button>
    </div>
  );
}

export default function PageWithErrorBoundary() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <PageContent />
    </ErrorBoundary>
  );
}
```

### Root-Level Error Boundary
Located in `providers.tsx`, catches all errors across the app.

## Dependencies

### Next.js
- **next**: ^14.0.0 - App Router framework
- Features: Server Components, nested layouts, streaming, RSC

### React
- **react**: ^18.0.0 - Component library
- **react-dom**: ^18.0.0 - DOM rendering
- **react-error-boundary**: ^4.0.0 - Error boundaries

### Styling
- **tailwindcss**: ^3.4.0 - Utility-first CSS framework
- **next/font**: Built-in font optimization (Inter font)

### State Management
- **zustand**: ^4.4.0 - Lightweight state management (useAgentState)

### WebSocket
- **ws**: Native WebSocket API (browser)
- Custom context: `@/contexts/WebSocketProvider`

## Related Documentation

### Internal Docs
- [Components](../components/README.md) - React components and UI primitives
- [Hooks](../hooks/README.md) - Custom React hooks
- [Contexts](../contexts/README.md) - React context providers
- [Frontend Root](../README.md) - Frontend architecture overview

### External Docs
- [Next.js App Router](https://nextjs.org/docs/app) - Official Next.js documentation
- [Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components) - RSC guide
- [Route Handlers](https://nextjs.org/docs/app/building-your-application/routing/route-handlers) - API routes
- [Metadata API](https://nextjs.org/docs/app/building-your-application/optimizing/metadata) - SEO optimization

## Testing

### Unit Tests
```bash
# Test page components
npm run test app/__tests__
```

### Integration Tests
```bash
# Test route navigation and data flow
npm run test tests/integration/
```

### E2E Tests
```bash
# Test complete user journeys
npm run test tests/e2e/
pytest tests/e2e/
```

### UI Tests (Playwright)
```bash
# Test browser interactions
pytest tests/ui/
```

## Performance Optimization

### Code Splitting
- Automatic route-based code splitting
- Dynamic imports for heavy components:
  ```tsx
  import dynamic from 'next/dynamic';
  const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
    loading: () => <p>Loading...</p>,
  });
  ```

### Image Optimization
```tsx
import Image from 'next/image';

<Image
  src="/image.png"
  alt="Description"
  width={500}
  height={300}
  priority // For above-the-fold images
/>
```

### Font Optimization
Inter font is optimized via `next/font/google` in `layout.tsx`:
- Self-hosted fonts (no external requests)
- Automatic font subsetting
- Zero layout shift

## Accessibility

### Semantic HTML
Use semantic HTML elements for better accessibility:
```tsx
<main role="main" aria-label="Chat interface">
  <nav aria-label="Main navigation">...</nav>
  <article>...</article>
</main>
```

### ARIA Attributes
Add ARIA attributes for screen readers:
```tsx
<button aria-label="Send message" aria-disabled={!isConnected}>
  Send
</button>
```

### Keyboard Navigation
Ensure all interactive elements are keyboard accessible:
- Use native HTML elements (`<button>`, `<a>`, etc.)
- Add `tabIndex` for custom interactive elements
- Test with keyboard only (Tab, Enter, Escape)

## Development Workflow

### Local Development
```bash
# Start development server
cd frontend
npm run dev

# Open in browser
open http://localhost:3000
```

### Adding a New Route
1. Create directory: `app/new-route/`
2. Add page component: `app/new-route/page.tsx`
3. (Optional) Add layout: `app/new-route/layout.tsx`
4. (Optional) Add loading state: `app/new-route/loading.tsx`
5. Update documentation (this README)

### Adding a New Feature
1. Create feature branch: `git checkout -b feature/new-route`
2. Implement page/layout components
3. Add JSDoc comments to all components
4. Write tests (unit, integration, E2E)
5. Update documentation
6. Run pre-commit review: code-review-expert + testing-expert
7. Commit with semantic message: `feat(app): add new route for [feature]`
8. Push and create PR

## Best Practices

### Server vs. Client Components
- **Default to Server Components** for static content
- **Use Client Components** only when needed:
  - Event handlers (`onClick`, `onChange`, etc.)
  - State management (`useState`, `useReducer`, etc.)
  - Effects (`useEffect`, `useLayoutEffect`, etc.)
  - Browser APIs (`window`, `localStorage`, etc.)

### Component Organization
- Keep page components lean (delegate to child components)
- Use `components/` subdirectory for page-specific components
- Share common components via `@/components/` (root-level)

### Error Handling
- Wrap pages in error boundaries for graceful failures
- Log errors to console (dev) or monitoring service (prod)
- Provide clear error messages and retry mechanisms

### Performance
- Use Server Components for data fetching when possible
- Implement loading states for async operations
- Optimize images with `next/image`
- Lazy load heavy components

### Accessibility
- Use semantic HTML elements
- Add ARIA labels for screen readers
- Ensure keyboard navigation works
- Test with accessibility tools (axe DevTools)

### Documentation
- Add JSDoc comments to all page components
- Document route structure and navigation
- Explain data fetching strategies
- Update README when adding new routes

## Troubleshooting

### Common Issues

**Issue:** "Hydration mismatch" error
- **Cause:** Server-rendered HTML doesn't match client-rendered HTML
- **Fix:** Ensure `useEffect` runs only on client, avoid `Date.now()` in SSR

**Issue:** "Error: Text content does not match server-rendered HTML"
- **Cause:** Using browser-only APIs in Server Components
- **Fix:** Add `'use client'` directive at top of file

**Issue:** "Module not found" error
- **Cause:** Incorrect import path or missing dependency
- **Fix:** Check `tsconfig.json` paths, run `npm install`

**Issue:** WebSocket not connecting
- **Cause:** Backend not running or incorrect URL
- **Fix:** Verify backend running on `ws://localhost:8000/ws/agent`, check `.env.local`

### Debug Mode
```bash
# Enable debug logging
NODE_ENV=development npm run dev

# Check browser console for errors
# Check Network tab for WebSocket connection
```

## Contributing

When adding new routes or pages:
1. Follow the App Router conventions (file-based routing)
2. Add JSDoc comments to all components
3. Update this README with new route documentation
4. Write tests for new pages (unit + E2E)
5. Run pre-commit review agents (code-review-expert + testing-expert)
6. Use semantic commit messages

## Future Enhancements (Phase 1+)

- [ ] Add authentication pages (`/login`, `/signup`)
- [ ] Implement user dashboard (`/dashboard`)
- [ ] Add settings page (`/settings`)
- [ ] Create admin panel (`/admin`)
- [ ] Add loading states (`loading.tsx`) for all routes
- [ ] Implement not-found pages (`not-found.tsx`)
- [ ] Add route groups for better organization
- [ ] Implement parallel routes for multi-pane layouts
- [ ] Add intercepting routes for modals

---

**Last Updated:** 2025-11-12
**Phase:** Phase 0 (MVP)
**Status:** Active Development
