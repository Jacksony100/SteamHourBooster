import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "@/components/providers";
import { product } from "@/lib/product";

export const metadata: Metadata = {
  title: {
    default: product.name,
    template: `%s | ${product.name}`
  },
  description: product.description,
  applicationName: product.name,
  icons: [{ rel: "icon", url: "/icon.svg" }]
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
