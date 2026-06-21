import { Suspense } from "react";

import { PaymentStatus } from "@/features/billing/payment-status";

export default function PaymentSuccessPage() {
  return (
    <Suspense>
      <PaymentStatus status="success" />
    </Suspense>
  );
}
