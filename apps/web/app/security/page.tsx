import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Security" };

export default function SecurityPage() {
  return (
    <LegalPage
      title="Security"
      intro="DeckPilot is designed around explicit user actions, encrypted storage, rate limits, and audited administrative changes."
      sections={[
        {
          title: "Authentication",
          body: "User passwords are hashed. Browser sessions use HTTP-only cookies, CSRF protection, and server-side session revocation."
        },
        {
          title: "Production guards",
          body: "Production startup rejects weak secrets, insecure cookies, SQLite, wildcard CORS, mock billing, and unreviewed demo mode unless explicitly labeled."
        },
        {
          title: "Integration boundary",
          body: "The product does not include stealth behavior, network-routing evasion, account-risk evasion, CAPTCHA circumvention, or hidden automation. Demo mode is simulated."
        },
        {
          title: "Reporting",
          body: "For beta deployments, report suspected vulnerabilities to the project maintainer or private repository owner. Do not include passwords, API keys, or Steam Guard codes in reports."
        }
      ]}
    />
  );
}
