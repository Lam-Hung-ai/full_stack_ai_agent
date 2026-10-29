import type { NextConfig } from "next";

// The browser calls /api/v1 on the Next.js origin and Next forwards it to
// FastAPI, so the refresh cookie (SameSite=Strict, path /api/v1/auth) stays
// first-party. Server-only setting, not exposed to the browser.
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${backendUrl}/api/v1/:path*` }];
  },
};

export default nextConfig;
