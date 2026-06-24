const KEY = "faceit_recent";
const MAX = 8;

export function getRecent(): string[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(v) ? v.slice(0, MAX) : [];
  } catch {
    return [];
  }
}

export function addRecent(query: string): string[] {
  const q = query.trim();
  if (!q) return getRecent();
  const next = [q, ...getRecent().filter((x) => x.toLowerCase() !== q.toLowerCase())].slice(0, MAX);
  try { localStorage.setItem(KEY, JSON.stringify(next)); } catch {}
  return next;
}

export function clearRecent(): string[] {
  try { localStorage.removeItem(KEY); } catch {}
  return [];
}
