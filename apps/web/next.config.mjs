const isVercel = Boolean(process.env.VERCEL);
const defaultApiOrigin = process.env.NODE_ENV === "production" ? "http://api:8000" : "http://127.0.0.1:8000";
const apiOrigin = process.env.INTERNAL_API_ORIGIN || process.env.API_INTERNAL_ORIGIN || (isVercel ? "" : defaultApiOrigin);

const nextConfig = {
  output: process.env.NEXT_OUTPUT_MODE === "standalone" ? "standalone" : undefined,
  typedRoutes: true,
  async rewrites() {
    if (!apiOrigin) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`
      }
    ];
  }
};

export default nextConfig;
