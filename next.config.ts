import type { NextConfig } from "next";
import { withSentryConfig } from '@sentry/nextjs';

const nextConfig: NextConfig = {
  reactCompiler: true,

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
        pathname: '/**',
      },
    ],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
  },

  // Security & performance headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          { key: 'Content-Security-Policy', value: "base-uri 'self'; object-src 'none'; frame-ancestors 'self'" },
          // No includeSubDomains/preload: sibling domains need separate TLS review.
          ...(process.env.NODE_ENV === 'production' ? [
            { key: 'Strict-Transport-Security', value: 'max-age=31536000' },
          ] : []),
        ],
      },
      // Next.js owns static-asset caching: production assets are fingerprinted,
      // but development CSS URLs can stay unchanged across edits. An immutable
      // override here leaves browsers using stale styles throughout live preview.
    ];
  },

  // Compression
  compress: true,

  // Bundle analyzer (enable via ANALYZE=true npm run build)
  ...(process.env.ANALYZE === 'true' && {
    productionBrowserSourceMaps: false,
  }),
};

export default withSentryConfig(nextConfig, {
  org: 'intelliwheels',
  project: 'intelliwheels-frontend',

  // Suppress source map upload logs
  silent: !process.env.CI,

  // Disable Sentry build telemetry in CI logs
  telemetry: false,

  // Upload source maps for readable stack traces in Sentry
  widenClientFileUpload: true,

  webpack: {
    // Replacement for deprecated disableLogger
    treeshake: {
      removeDebugLogging: true,
    },
    // Replacement for deprecated autoInstrumentServerFunctions
    autoInstrumentServerFunctions: true,
  },
});
