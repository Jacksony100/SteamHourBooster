import { Suspense } from "react";

import { PaymentStatus } from "@/features/billing/payment-status";

export default function PaymentFailedPage() {
  return (
    <Suspense>
      <PaymentStatus status="failed" />
    </Suspense>
  );
}
