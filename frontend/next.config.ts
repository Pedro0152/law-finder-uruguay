import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  rewrites: async () => {
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: "http://127.0.0.1:8000/api/:path*",
        },
      ];
    }
    // In production, Vercel routes /api/index.py natively. We don't need to manually proxy to /api/ and lose the path.
    return [];
  },
};

export default nextConfig;
