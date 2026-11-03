"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Spinner } from "@/components/ui/spinner";
import { onSessionExpired } from "@/lib/auth/session";
import { useSession } from "../hooks/use-session";

/** Renders its children only inside a live session; otherwise goes to /login. */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const session = useSession();

  useEffect(
    () =>
      onSessionExpired(() => {
        queryClient.clear();
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      }),
    [pathname, queryClient, router],
  );

  useEffect(() => {
    if (session.isError) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [pathname, router, session.isError]);

  if (!session.isSuccess) {
    return (
      <div className="flex h-dvh items-center justify-center" aria-busy="true">
        <Spinner aria-label="Đang tải phiên đăng nhập" />
      </div>
    );
  }
  return children;
}
