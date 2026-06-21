import { Card } from "@/components/ui/card";

export default function Loading() {
  return (
    <main className="min-h-screen px-5 py-8 lg:px-8">
      <div className="mx-auto grid max-w-6xl gap-6">
        <div className="h-10 w-64 animate-pulse rounded-2xl bg-white/10" />
        <div className="grid gap-4 md:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <Card key={item}>
              <div className="h-4 w-24 animate-pulse rounded bg-white/10" />
              <div className="mt-5 h-9 w-32 animate-pulse rounded bg-white/15" />
              <div className="mt-4 h-3 w-full animate-pulse rounded bg-white/10" />
            </Card>
          ))}
        </div>
        <Card>
          <div className="h-5 w-40 animate-pulse rounded bg-white/10" />
          <div className="mt-6 grid gap-3">
            {[0, 1, 2, 3].map((item) => (
              <div key={item} className="h-14 animate-pulse rounded-2xl bg-white/10" />
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}
