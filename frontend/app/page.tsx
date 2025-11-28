/**
 * Home Page - Landing Page (Route: `/`)
 *
 * @fileoverview Landing page for Deep Agent AGI application.
 * Displays welcome message and call-to-action button to navigate to chat interface.
 * Uses Server Component for static rendering and optimal performance.
 *
 * @example
 * // Accessible at http://localhost:3000/
 * // Automatically inherits RootLayout
 *
 * @see ./layout.tsx - Root layout wrapping this page
 * @see ./chat/page.tsx - Chat interface page (destination)
 * @see {@link https://nextjs.org/docs/app/api-reference/file-conventions/page|Next.js Page Documentation}
 */

/**
 * Home page component displaying landing page with CTA
 *
 * @returns {JSX.Element} Centered landing page with title and link to chat
 *
 * @remarks
 * - Server Component (no 'use client' directive)
 * - Static rendering at build time
 * - Uses Tailwind CSS utility classes for styling
 * - Navigates to /chat route on button click
 * - Fully responsive design with min-h-screen
 *
 * Features:
 * - Application title and description
 * - Call-to-action button to start chat
 * - Hover effects on button
 * - Accessible semantic HTML (main, h1, p, a)
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Deep Agent One</h1>
        <p className="text-muted-foreground mb-8">
          General-purpose deep agent framework
        </p>
        <a
          href="/chat"
          className="inline-flex items-center justify-center rounded-md bg-primary px-8 py-3 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
        >
          Start Chat
        </a>
      </div>
    </main>
  );
}
