"use client";

import { useRouter } from "next/navigation";
import { LogOutIcon, MailCheckIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLogout, useRequestEmailVerification } from "../hooks/use-auth-mutations";
import { useSession } from "../hooks/use-session";

export function UserMenu() {
  const router = useRouter();
  const { data } = useSession();
  const logoutMutation = useLogout();
  const verifyMutation = useRequestEmailVerification();
  if (!data) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="sm" variant="ghost">
          {data.user.name}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="truncate font-normal text-muted-foreground">
          {data.user.email}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {!data.user.email_verified && (
          <DropdownMenuItem
            disabled={verifyMutation.isPending || verifyMutation.isSuccess}
            // Keep the menu open so the label can say the letter went out.
            onSelect={(event) => {
              event.preventDefault();
              verifyMutation.mutate(data.user.email);
            }}
          >
            <MailCheckIcon />
            {verifyMutation.isSuccess ? "Đã gửi thư xác minh" : "Gửi thư xác minh email"}
          </DropdownMenuItem>
        )}
        <DropdownMenuItem
          disabled={logoutMutation.isPending}
          onSelect={() =>
            logoutMutation.mutate(undefined, { onSettled: () => router.replace("/login") })
          }
        >
          <LogOutIcon />
          Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
