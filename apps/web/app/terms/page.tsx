import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Terms" };

export default function TermsPage() {
  return (
    <LegalPage
      title="Terms"
      intro="DeckPilot is a beta account workspace for accounts you own. These practical terms describe the intended release scope."
      sections={[
        {
          title: "Allowed use",
          body: "Use DeckPilot only with accounts you own or are authorized to manage. Do not use it for credential abuse, spam, evasion, or activity that violates third-party platform rules."
        },
        {
          title: "Demo and official modes",
          body: "The beta release runs in demo mode unless official integration is explicitly configured. Demo mode uses simulated sessions and does not claim to run real Steam activity."
        },
        {
          title: "No affiliation",
          body: "DeckPilot is not affiliated with Valve, Steam, or any payment provider. Steam and related marks belong to their respective owners."
        },
        {
          title: "Admin actions",
          body: "Administrative subscription, ban, role, and session actions are audited. Admins must not expose or request user secrets."
        }
      ]}
    />
  );
}
