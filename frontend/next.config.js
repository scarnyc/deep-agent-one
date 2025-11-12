/**
 * Next.js Configuration (Phase 0)
 *
 * This configuration file defines settings for the Deep Agent AGI frontend,
 * including WebSocket support, API proxying, security headers, and optimizations.
 *
 * Key Features:
 * - WebSocket support for AG-UI Protocol real-time communication
 * - API request proxying to FastAPI backend during development
 * - Security headers (X-Frame-Options, CSP, etc.)
 * - Package import optimization for faster builds
 *
 * References:
 * - https://nextjs.org/docs/app/api-reference/next-config-js
 * - https://docs.ag-ui.com/sdk/python/core/overview
 *
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  // Phase 0: Disable strict mode to prevent WebSocket connection issues
  // React Strict Mode causes double-mounting in development, creating
  // multiple WebSocket connections that exhaust backend resources (400 errors)
  // TODO Phase 1: Re-enable after implementing singleton WebSocket pattern
  reactStrictMode: false,

  /**
   * Webpack Configuration
   *
   * Marks WebSocket-related native modules as external to prevent
   * bundling issues. These modules are optional peer dependencies
   * for the 'ws' package used by AG-UI Protocol.
   *
   * @param {object} config - Webpack configuration object
   * @returns {object} Modified webpack configuration
   */
  webpack: (config) => {
    config.externals.push({
      'utf-8-validate': 'commonjs utf-8-validate',
      'bufferutil': 'commonjs bufferutil',
    });
    return config;
  },

  /**
   * Rewrites Configuration
   *
   * Proxies API requests to the FastAPI backend during development.
   * Requests to /api/* are forwarded to NEXT_PUBLIC_API_URL/api/*.
   *
   * @returns {Promise<Array<object>>} Array of rewrite rules
   */
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/api/:path*',
      },
    ];
  },

  /**
   * Security Headers Configuration
   *
   * Adds essential security headers to all responses:
   * - X-DNS-Prefetch-Control: Controls DNS prefetching
   * - X-Frame-Options: Prevents clickjacking (SAMEORIGIN)
   * - X-Content-Type-Options: Prevents MIME type sniffing
   * - Referrer-Policy: Controls referrer information leakage
   *
   * @returns {Promise<Array<object>>} Array of header configurations
   */
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
        ],
      },
    ];
  },

  /**
   * Experimental Features
   *
   * Enables package import optimizations for faster builds.
   * Optimizes imports from lucide-react and @radix-ui packages.
   */
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },
};

module.exports = nextConfig;
