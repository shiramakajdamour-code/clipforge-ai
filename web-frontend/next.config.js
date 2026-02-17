/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost', '127.0.0.1'],
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://backend:8000/:path*', // Proxy to backend in Docker
      },
      {
        source: '/api/uploads/:path*',
        destination: 'http://backend:8000/uploads/:path*',
      },
      {
        source: '/api/clips/:path*',
        destination: 'http://backend:8000/clips/:path*',
      },
      {
        source: '/api/thumbnails/:path*',
        destination: 'http://backend:8000/thumbnails/:path*',
      },
    ];
  },
  // For local development without Docker
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig
