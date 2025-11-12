/**
 * Root Layout - Next.js 14 App Router Root Layout (Phase 0)
 *
 * @fileoverview Root layout component that wraps all pages in the application.
 * This is a Server Component that sets up the HTML structure, font loading,
 * and client-side providers. Uses Inter font from Google Fonts and provides
 * global metadata for SEO.
 *
 * @example
 * // Automatically applied to all routes in the app
 * // app/page.tsx inherits this layout
 * // app/chat/page.tsx inherits this layout
 *
 * @see {@link https://nextjs.org/docs/app/api-reference/file-conventions/layout|Next.js Layout Documentation}
 * @see ./providers.tsx - Client-side providers (ErrorBoundary, WebSocketProvider)
 * @see ./globals.css - Global styles and Tailwind configuration
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import './globals.css';

/**
 * Inter font configuration
 * Optimized for Latin character subset to reduce initial load
 */
const inter = Inter({ subsets: ['latin'] });

/**
 * Application metadata for SEO and social sharing
 * Generated at build time (static)
 */
export const metadata: Metadata = {
  title: 'Deep Agent AGI',
  description: 'General-purpose deep agent framework with cost optimization',
};

/**
 * Root layout component wrapping all pages
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child pages/layouts to render
 * @returns {JSX.Element} HTML structure with providers and font configuration
 *
 * @remarks
 * - Server Component by default (no 'use client')
 * - Wraps all routes in the application
 * - Provides global HTML structure and metadata
 * - Delegates client-side logic to Providers component
 * - Sets Inter font on body element via className
 *
 * @see {@link Providers} - Client-side error boundary and WebSocket provider
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
