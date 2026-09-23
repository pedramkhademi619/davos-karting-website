import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Behind nginx (compose/production) /api never reaches Next.js. Under `next dev` there is no proxy, so forward /api to the
  // backend to make the chat widget work; API_INTERNAL_URL overrides the default local address.
  async rewrites() {
    if (process.env.NODE_ENV === "production") return [];
    const api = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
