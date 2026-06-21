const isVercel = Boolean(process.env.VERCEL);
const defaultApiOrigin = process.env.NODE_ENV === "production" ? "http://api:8000" : "http://127.0.0.1:8000";
const apiOrigin = process.env.INTERNAL_API_ORIGIN || process.env.API_INTERNAL_ORIGIN || (isVercel ? "" : defaultApiOrigin);
const isProd = process.env.NODE_ENV === "production";

// Approved Steam public CDN hosts for avatars + game artwork (mirrors
// apps/api/app/steam_data/cdn.py ALLOWED_IMAGE_HOSTS). The Steam Web API key
// never reaches the browser; only these public image hosts are allowed.
const steamImageHosts = [
  "cdn.cloudflare.steamstatic.com",
  "media.steampowered.com",
  "avatars.cloudflare.steamstatic.com",
  "shared.cloudflare.steamstatic.com",
];

// Content Security Policy. Connect/img allow the API + Steam image CDNs.
const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "form-action 'self'",
  `img-src 'self' data: blob: ${steamImageHosts.map((h) => `https://${h}`).join(" ")}`,
  "font-src 'self' https://api.fontshare.com https://cdn.fontshare.com data:",
  "style-src 'self' 'unsafe-inline' https://api.fontshare.com",
  // Next.js requires inline/eval for the dev runtime; tighten in prod.
  isProd ? "script-src 'self' 'unsafe-inline'" : "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "connect-src 'self' https://api.fontshare.com",
].join("; ");

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(), microphone=(), camera=(), payment=()" },
  { key: "Content-Security-Policy", value: csp },
  ...(isProd ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }] : []),
];

const nextConfig = {
  output: process.env.NEXT_OUTPUT_MODE === "standalone" ? "standalone" : undefined,
  typedRoutes: true,
  images: {
    remotePatterns: steamImageHosts.map((hostname) => ({ protocol: "https", hostname })),
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    if (!apiOrigin) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
