"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";

/** next-themes, as the shadcn dark-mode guide sets it up for Next.js. */
export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
