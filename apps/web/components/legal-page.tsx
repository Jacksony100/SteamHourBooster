import Link from "next/link";

import { Card, CardTitle } from "@/components/ui/card";
import { product } from "@/lib/product";

type Section = {
  title: string;
  body: string;
};

export function LegalPage({ title, intro, sections }: { title: string; intro: string; sections: Section[] }) {
  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl px-5 py-10">
      <Link href="/" className="inline-flex items-center gap-3 text-sm font-semibold text-sky-200">
        <span className="grid h-9 w-9 place-items-center rounded-xl border border-sky-300/30 bg-sky-300/15 font-black">{product.shortName}</span>
        Back to {product.name}
      </Link>
      <section className="mt-10 space-y-4">
        <div className="text-sm font-semibold text-emerald-200">Trust center</div>
        <h1 className="text-gradient text-4xl font-black md:text-6xl">{title}</h1>
        <p className="max-w-3xl text-base leading-8 text-slate-300">{intro}</p>
      </section>
      <div className="mt-8 grid gap-4">
        {sections.map((section) => (
          <Card key={section.title}>
            <CardTitle>{section.title}</CardTitle>
            <p className="mt-3 text-sm leading-7 text-slate-300">{section.body}</p>
          </Card>
        ))}
      </div>
    </main>
  );
}
