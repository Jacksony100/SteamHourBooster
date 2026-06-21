import { AppShell } from "@/components/app-shell";
import { requireCurrentUser } from "@/lib/server-auth";

export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const user = await requireCurrentUser();
  return <AppShell currentUser={user}>{children}</AppShell>;
}
