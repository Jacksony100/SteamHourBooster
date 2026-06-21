import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "System Status" };

export default function StatusPage() {
  return (
    <LegalPage
      title="System status"
      intro="Use this page as the public status baseline for beta deployments. Operators should pair it with API health endpoints and infrastructure monitoring."
      sections={[
        {
          title: "Health endpoints",
          body: "The API exposes /healthz for liveness and /readyz for readiness. In production readiness checks database connectivity and Redis availability."
        },
        {
          title: "Current release state",
          body: "This build is a release-candidate beta. Real Steam session automation is not enabled unless official integration is explicitly configured and reviewed."
        },
        {
          title: "Incident response",
          body: "If billing, authentication, or session queues fail, disable checkout, preserve logs, stop workers gracefully, and roll back to the previous verified image."
        },
        {
          title: "Backups",
          body: "Production operators should run encrypted PostgreSQL backups and regularly test restore procedures before accepting paid users."
        }
      ]}
    />
  );
}
