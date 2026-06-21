import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export type CurrentUser = {
  id: number;
  username: string;
  is_admin: boolean;
  banned: boolean;
};

function defaultInternalApiUrl() {
  if (process.env.VERCEL) return "";
  const defaultOrigin = process.env.NODE_ENV === "production" ? "http://api:8000" : "http://127.0.0.1:8000";
  return `${defaultOrigin}/api/v1`;
}

const INTERNAL_API_URL = (process.env.INTERNAL_API_URL || process.env.API_INTERNAL_URL || defaultInternalApiUrl()).replace(/\/$/, "");
const sessionCookieName = "deckpilot_session";
const csrfCookieName = "deckpilot_csrf";
const legacySessionCookieName = "shb_session";
const legacyCsrfCookieName = "shb_csrf";

async function authCookieHeader() {
  const cookieStore = await cookies();
  const session = cookieStore.get(sessionCookieName)?.value || cookieStore.get(legacySessionCookieName)?.value;
  const csrf = cookieStore.get(csrfCookieName)?.value || cookieStore.get(legacyCsrfCookieName)?.value;

  if (!session) return "";
  return [`${sessionCookieName}=${session}`, csrf ? `${csrfCookieName}=${csrf}` : ""].filter(Boolean).join("; ");
}

export async function getCurrentUserFromServer(): Promise<CurrentUser | null> {
  const cookieHeader = await authCookieHeader();
  if (!cookieHeader) return null;
  if (!INTERNAL_API_URL) return null;

  const response = await fetch(`${INTERNAL_API_URL}/auth/me`, {
    headers: { cookie: cookieHeader },
    cache: "no-store"
  }).catch(() => null);

  if (!response?.ok) return null;
  return (await response.json()) as CurrentUser;
}

export async function requireCurrentUser() {
  const user = await getCurrentUserFromServer();
  if (!user) redirect("/login");
  return user;
}

export async function requireAdminUser() {
  const user = await requireCurrentUser();
  if (!user.is_admin) redirect("/dashboard");
  return user;
}
