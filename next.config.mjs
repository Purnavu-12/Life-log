/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // Type errors are now fixed; enforce type checking on build.
    ignoreBuildErrors: false,
  },
  images: {
    unoptimized: true,
  },
  // Proxy API requests to backend (client uses NEXT_PUBLIC_API_URL directly, but this
  // keeps relative /api/ requests working if used).
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007'}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
