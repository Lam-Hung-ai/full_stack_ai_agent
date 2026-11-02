import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Source_Serif_4 } from "next/font/google";
import { AppProviders } from "./providers";
import "katex/dist/katex.min.css";
import "./globals.css";

// Serif for what the agent says (answers, its questions, the greeting),
// sans for what the user types and the interface, mono for code. Each with
// the Vietnamese subset so diacritics never fall back to another face.
const sans = Inter({ variable: "--font-inter", subsets: ["latin", "vietnamese"] });
const serif = Source_Serif_4({ variable: "--font-source-serif", subsets: ["latin", "vietnamese"] });
const mono = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin", "vietnamese"] });

export const metadata: Metadata = {
  title: "Agent Chat",
  description: "FastAPI + LangGraph agent with a Next.js + shadcn/ui chat frontend",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="vi"
      className={`${sans.variable} ${serif.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
