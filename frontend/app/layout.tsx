/**
 * Root Layout Component (App Router)
 *
 * @fileoverview Root layout wrapping all pages in the application.
 * Provides HTML structure, metadata, and global styles.
 * Required for Next.js App Router - cannot be deleted.
 *
 * @example
 * // Automatically wraps all pages at all routes
 * // Cannot be opted out - mandatory for App Router
 *
 * @see ./page.tsx - Home page using this layout
 * @see ./chat/page.tsx - Chat page using this layout
 * @see {@link https://nextjs.org/docs/app/api-reference/file-conventions/layout|Next.js Layout Documentation}
 */

import type { Metadata } from 'next'
import './globals.css'

/**
 * Application metadata for SEO and browser tabs
 *
 * @property {string} title - Displayed in browser tab
 * @property {string} description - Meta description for search engines
 */
export const metadata: Metadata = {
  title: 'Deep Agent AGI',
  description: 'General-purpose deep agent framework',
}

/**
 * Root layout component wrapping all pages
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Page content to render
 * @returns {JSX.Element} HTML document structure with page content
 *
 * @remarks
 * - Server Component (no 'use client' directive)
 * - Renders once per navigation
 * - Provides <html> and <body> tags
 * - Imports global CSS styles
 * - Cannot use hooks or browser-only APIs
 *
 * Required Elements:
 * - Must export default function
 * - Must render <html> and <body> tags
 * - Must render {children} inside <body>
 * - Should include lang attribute for accessibility
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
