import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Sysmap - Directorio Comunitario de Eventos Tech",
  description: "Descubre eventos tecnológicos locales de forma local-first y sostenible en Buenos Aires. Operado bajo la infraestructura de TecnoAncon.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="h-full" suppressHydrationWarning>
      <body style={{ minHeight: "100%", display: "flex", flexDirection: "column" }} suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

