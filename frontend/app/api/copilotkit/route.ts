/**
 * CopilotKit Runtime API Route (Phase 0 Simplified)
 *
 * This Next.js API route provides a simple proxy between CopilotKit
 * and our FastAPI backend.
 *
 * Architecture:
 * Frontend (CopilotKit) → /api/copilotkit → FastAPI backend
 *
 * Note: In Phase 1, we'll implement full AG-UI Protocol integration
 * with proper event streaming and CustomHttpAgent.
 */

import { NextRequest, NextResponse } from 'next/server';

/**
 * FastAPI backend URL
 */
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * POST handler - Forward requests to FastAPI backend
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Forward request to FastAPI backend
    const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('[CopilotKit API] Error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}

/**
 * GET handler - Health check
 */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    backend: BACKEND_URL,
    message: 'CopilotKit API Route (Phase 0)',
  });
}
