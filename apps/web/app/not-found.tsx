import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { product } from "@/lib/product";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <Card className="w-full max-w-xl text-center">
        <div className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">404</div>
        <h1 className="mt-4 text-3xl font-black">Page not found</h1>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          This route is not part of the current {product.name} workspace.
        </p>
        <Button asChild className="mt-6">
          <Link href="/dashboard">Back to dashboard</Link>
        </Button>
      </Card>
    </main>
  );
}
