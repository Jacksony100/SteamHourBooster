import { NextResponse, type NextRequest } from "next/server";

const protectedPrefixes = ["/dashboard", "/admin", "/settings", "/billing"];
const sessionCookieName = "deckpilot_session";
const legacySessionCookieName = "shb_session";

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has(sessionCookieName) || request.cookies.has(legacySessionCookieName);
  const isProtected = protectedPrefixes.some((prefix) => request.nextUrl.pathname.startsWith(prefix));
  if (isProtected && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/admin/:path*", "/settings/:path*", "/billing/:path*"]
};
