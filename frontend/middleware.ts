/**
 * Next.js Middleware for Security Headers (Phase 0)
 *
 * This middleware adds essential security headers to all responses,
 * protecting against common web vulnerabilities.
 *
 * Security Features:
 * - X-Content-Type-Options: Prevents MIME type sniffing
 * - X-Frame-Options: Prevents clickjacking attacks
 * - X-XSS-Protection: Enables browser XSS protection
 * - Referrer-Policy: Controls referrer information
 * - Permissions-Policy: Restricts browser features
 * - Content-Security-Policy: Prevents XSS and injection (API routes only)
 *
 * References:
 * - https://nextjs.org/docs/app/building-your-application/routing/middleware
 * - https://owasp.org/www-project-secure-headers/
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware function to add security headers
 */
export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Security Headers (applied to all routes)
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), interest-cohort=()'
  );

  // Stricter CSP for API routes (no scripts needed)
  if (request.nextUrl.pathname.startsWith('/api/')) {
    response.headers.set(
      'Content-Security-Policy',
      "default-src 'self'; script-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self';"
    );
  }

  return response;
}

/**
 * Matcher configuration
 * Apply middleware to API routes and all pages (exclude Next.js internals)
 */
export const config = {
  matcher: [
    '/api/:path*',
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
