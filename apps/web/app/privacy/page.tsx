import type { Metadata } from "next";

import { LegalPage } from "@/components/legal-page";

export const metadata: Metadata = { title: "Privacy" };

export default function PrivacyPage() {
  return (
    <LegalPage
      title="Privacy"
      intro="DeckPilot stores only the data needed to operate the dashboard, subscriptions, audit history, and account management flows."
      sections={[
        {
          title: "Data we store",
          body: "The app stores username, optional email, subscription state, account labels, selected game ids, session events, payments metadata, and audit records."
        },
        {
          title: "Sensitive data",
          body: "Application passwords are one-way hashes. Compatibility account credentials, when accepted in non-production flows, are encrypted at rest. Steam Guard codes are not stored."
        },
        {
          title: "Export and deletion",
          body: "Users can export account data and delete their workspace account from Settings. Audit records may be retained where needed for security and billing integrity."
        },
        {
          title: "Payments",
          body: "Payment provider secrets are stored only in server environment variables. Redirect pages do not grant subscriptions; verified provider events are required."
        }
      ]}
    />
  );
}
