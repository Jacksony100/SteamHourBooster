import { AdminClient } from "@/features/admin/admin-client";
import { requireAdminUser } from "@/lib/server-auth";

export default async function AdminPage() {
  await requireAdminUser();
  return <AdminClient />;
}
