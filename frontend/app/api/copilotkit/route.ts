/**
 * CopilotKit Runtime API Route (Phase 0 - Security Hardened)
 *
 * This Next.js API route provides a secure proxy between CopilotKit
 * and our FastAPI backend with CSRF protection, input validation,
 * and timeout handling.
 *
 * Architecture:
 * Frontend (CopilotKit) → /api/copilotkit → FastAPI backend
 *
 * Security Features:
 * - CSRF protection via origin verification
 * - Input validation with Zod schemas
 * - Request timeouts (30s)
 * - Sanitized error messages
 * - Structured logging
 *
 * Note: In Phase 1, we'll implement full AG-UI Protocol integration
 * with proper event streaming and CustomHttpAgent.
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

/**
 * FastAPI backend URL - validated at module load
 */
const BACKEND_URL = (() => {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    new URL(url);
    return url;
  } catch {
    throw new Error('Invalid NEXT_PUBLIC_API_URL configuration');
  }
})();

/**
 * Allowed origins for CSRF protection
 */
const ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS?.split(',') || [
  'http://localhost:3000',
  'http://localhost:3001',
];

/**
 * Request timeout in milliseconds (30 seconds)
 */
const REQUEST_TIMEOUT_MS = 30000;

/**
 * Zod schema for chat request validation
 */
const ChatRequestSchema = z.object({
  message: z.string().min(1, 'Message cannot be empty').max(10000, 'Message too long'),
  thread_id: z.string().uuid().optional(),
  metadata: z.record(z.any()).optional(),
});

/**
 * Verify request origin for CSRF protection
 */
function verifyOrigin(req: NextRequest): boolean {
  const origin = req.headers.get('origin');
  if (!origin) {
    // Allow requests without origin header in development
    return process.env.NODE_ENV === 'development';
  }
  return ALLOWED_ORIGINS.includes(origin);
}

/**
 * Simple structured logger
 */
function log(level: 'info' | 'error', message: string, context?: Record<string, any>) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context,
  };
  const logMethod = level === 'error' ? console.error : console.log;
  logMethod(JSON.stringify(logEntry));
}

/**
 * POST handler - Forward requests to FastAPI backend
 */
export async function POST(req: NextRequest) {
  const requestId = crypto.randomUUID();

  log('info', 'API request started', {
    requestId,
    method: 'POST',
    path: '/api/copilotkit',
  });

  try {
    // CSRF protection: verify origin
    if (!verifyOrigin(req)) {
      log('error', 'CSRF check failed - invalid origin', {
        requestId,
        origin: req.headers.get('origin'),
      });
      return NextResponse.json(
        { error: 'Invalid origin' },
        { status: 403 }
      );
    }

    // Parse and validate request body
    const rawBody = await req.json();
    let validatedBody;

    try {
      validatedBody = ChatRequestSchema.parse(rawBody);
    } catch (error) {
      if (error instanceof z.ZodError) {
        log('error', 'Request validation failed', {
          requestId,
          errors: error.errors,
        });
        return NextResponse.json(
          { error: 'Invalid request data', details: error.errors },
          { status: 400 }
        );
      }
      throw error;
    }

    // Set up request timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      // Forward validated request to FastAPI backend
      const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validatedBody),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json();

      log('info', 'API request completed', {
        requestId,
        status: response.status,
      });

      return NextResponse.json(data, { status: response.status });
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error && error.name === 'AbortError') {
        log('error', 'Request timeout', { requestId });
        return NextResponse.json(
          { error: 'Request timeout' },
          { status: 504 }
        );
      }
      throw error;
    }
  } catch (error) {
    // Log detailed error server-side only
    log('error', 'API request failed', {
      requestId,
      error: error instanceof Error ? error.message : 'Unknown error',
      ...(process.env.NODE_ENV === 'development' && {
        stack: error instanceof Error ? error.stack : undefined,
      }),
    });

    // Return sanitized error to client
    return NextResponse.json(
      {
        error:
          process.env.NODE_ENV === 'development'
            ? 'Failed to connect to backend'
            : 'An error occurred',
      },
      { status: 500 }
    );
  }
}

/**
 * GET handler - Health check
 * Hides backend URL in production for security
 */
export async function GET() {
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json({ status: 'ok' });
  }

  return NextResponse.json({
    status: 'ok',
    backend: BACKEND_URL,
    message: 'CopilotKit API Route (Phase 0 - Security Hardened)',
  });
}
