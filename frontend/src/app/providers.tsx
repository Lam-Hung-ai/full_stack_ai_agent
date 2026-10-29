"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api";

// Retry reads only when the server never answered (network blip, restart
// during deploy). A response from FastAPI (401, 403, 404, 409, 422…) would
// come back the same, so it is not retried. Mutations are never retried.
const NETWORK_RETRIES = 2;

export function retryNetworkFailure(failureCount: number, error: unknown) {
  const reachedServer = error instanceof ApiError && error.status !== 0;
  return !reachedServer && failureCount < NETWORK_RETRIES;
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: retryNetworkFailure,
            retryDelay: 500,
            staleTime: 30_000,
          },
          mutations: { retry: false },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>{children}</TooltipProvider>
    </QueryClientProvider>
  );
}
