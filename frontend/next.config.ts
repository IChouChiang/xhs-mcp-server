import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        source: '/api/ai/:path*',
        destination: 'http://127.0.0.1:8000/api/ai/:path*', // Proxy to Python backend
      },
    ]
  },
};

export default nextConfig;
