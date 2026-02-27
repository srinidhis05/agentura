import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const apiTarget = process.env.API_TARGET || "http://localhost:3001";
    return [
      {
        source: "/healthz",
        destination: `${apiTarget}/healthz`,
      },
    ];
  },
};

export default nextConfig;
