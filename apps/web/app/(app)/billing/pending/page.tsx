import { Suspense } from "react";

import { PaymentStatus } from "@/features/billing/payment-status";

export default function PaymentPendingPage() {
  return (
    <Suspense>
      <PaymentStatus status="pending" />
    </Suspense>
  );
}
