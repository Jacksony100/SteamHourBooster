"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Application route error", { message: error.message, digest: error.digest });
  }, [error]);

  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <Card className="w-full max-w-xl text-center">
        <div className="text-sm font-semibold uppercase tracking-[0.2em] text-rose-200">500</div>
        <h1 className="mt-4 text-3xl font-black">Something went wrong</h1>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          The dashboard could not finish this action. Retry the request or check the API health endpoint if the issue continues.
        </p>
        <Button className="mt-6" onClick={reset}>
          Retry
        </Button>
      </Card>
    </main>
  );
}
