const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE_PATH || "/api/v1";
const csrfCookieName = "deckpilot_csrf";
const legacyCsrfCookieName = "shb_csrf";

type ApiOptions = RequestInit & { csrf?: boolean };

function apiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) return path;
  const base = PUBLIC_API_BASE.replace(/\/$/, "");
  const withoutApiPrefix = path.startsWith("/api/v1") ? path.slice("/api/v1".length) : path;
  const normalizedPath = withoutApiPrefix.startsWith("/") ? withoutApiPrefix : `/${withoutApiPrefix}`;
  return `${base}${normalizedPath}`;
}

function csrfToken() {
  if (typeof document === "undefined") return "";
  const cookies = document.cookie.split("; ");
  return cookies.find((row) => row.startsWith(`${csrfCookieName}=`))?.split("=")[1] || cookies.find((row) => row.startsWith(`${legacyCsrfCookieName}=`))?.split("=")[1] || "";
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.csrf) headers.set("X-CSRF-Token", csrfToken());
  const response = await fetch(apiUrl(path), {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store"
  });
  if (!response.ok) {
    if (typeof window !== "undefined" && response.status === 401) {
      window.location.href = "/login";
    }
    const payload = await response.json().catch(() => ({ detail: response.statusText || "Request failed" }));
    throw new Error(payload.detail || "Request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json().catch(() => undefined as T);
}
