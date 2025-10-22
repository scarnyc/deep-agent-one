/**
 * CopilotKit Runtime API Route
 *
 * This Next.js API route connects CopilotKit to our FastAPI backend
 * using the AG-UI Protocol over HTTP/SSE.
 *
 * Architecture:
 * Frontend (CopilotKit) → /api/copilotkit → FastAPI backend (AG-UI)
 */

import { CopilotRuntime, CustomHttpAgent, copilotRuntimeNextJSAppRouterEndpoint } from '@copilotkit/runtime';
import { NextRequest } from 'next/server';

/**
 * FastAPI backend URL
 * Default: http://localhost:8000
 * Override with NEXT_PUBLIC_API_URL environment variable
 */
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Create CopilotRuntime with CustomHttpAgent
 *
 * The CustomHttpAgent connects to our FastAPI backend's AG-UI endpoint.
 * Our backend implements AG-UI Protocol via:
 * - POST /api/v1/chat (synchronous)
 * - POST /api/v1/chat/stream (SSE streaming)
 * - WebSocket /api/v1/ws (real-time events)
 */
const runtime = new CopilotRuntime({
  agents: {
    /**
     * Default agent: connects to our deep agent backend
     */
    deepAgent: new CustomHttpAgent({
      url: `${BACKEND_URL}/api/v1/chat/stream`,
      name: 'Deep Agent',
      description: 'General-purpose deep agent with web search, code execution, and file tools',
    }),
  },
});

/**
 * HTTP POST handler
 *
 * CopilotKit sends requests to this endpoint, which proxies them
 * to our FastAPI backend using the AG-UI Protocol.
 */
export async function POST(req: NextRequest) {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: 'vercel',
    endpoint: '/api/copilotkit',
  });

  return handleRequest(req);
}
