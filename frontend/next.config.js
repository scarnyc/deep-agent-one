/** @type {import('next').NextConfig} */
const nextConfig = {
  // Phase 0: Disable strict mode to prevent WebSocket connection issues
  // React Strict Mode causes double-mounting in development, creating
  // multiple WebSocket connections that exhaust backend resources (400 errors)
  // TODO Phase 1: Re-enable after implementing singleton WebSocket pattern
  reactStrictMode: false,

  // Enable WebSocket support for AG-UI Protocol
  webpack: (config) => {
    config.externals.push({
      'utf-8-validate': 'commonjs utf-8-validate',
      'bufferutil': 'commonjs bufferutil',
    });
    return config;
  },

  // Proxy API requests to backend during development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/api/:path*',
      },
    ];
  },

  // Security headers
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

  // Experimental features for Next.js 15
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },
};

module.exports = nextConfig;
