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
      <head>
        {/* Design-system fonts (Satoshi for display, General Sans for body). */}
        <link
          rel="stylesheet"
          href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&f[]=general-sans@400,500,600,700&display=swap"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
