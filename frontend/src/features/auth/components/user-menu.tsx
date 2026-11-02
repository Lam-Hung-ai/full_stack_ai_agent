"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronsUpDownIcon, LogOutIcon, MailCheckIcon, ServerCogIcon } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { useLogout, useRequestEmailVerification } from "../hooks/use-auth-mutations";
import { useSession } from "../hooks/use-session";

function initials(name: string): string {
  const words = name.trim().split(/\s+/);
  const letters = words.length > 1 ? [words[0][0], words.at(-1)?.[0]] : [words[0]?.[0]];
  return letters.join("").toUpperCase() || "?";
}

/**
 * Account button at the foot of the sidebar. `subtitle` and `children`
 * (menu items) are composed in by the app, such as the workspace menu.
 */
export function UserMenu({
  subtitle,
  children,
}: {
  subtitle?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const router = useRouter();
  const { data } = useSession();
  const logoutMutation = useLogout();
  const verifyMutation = useRequestEmailVerification();
  if (!data) return null;

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton className="data-[state=open]:bg-sidebar-accent" size="lg">
              <Avatar className="size-8 rounded-full">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                  {initials(data.user.name)}
                </AvatarFallback>
              </Avatar>
              <span className="grid min-w-0 flex-1 text-left leading-tight">
                <span className="truncate font-medium">{data.user.name}</span>
                {subtitle && (
                  <span className="truncate text-muted-foreground text-xs">{subtitle}</span>
                )}
              </span>
              <ChevronsUpDownIcon className="ml-auto text-muted-foreground" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="start"
            className="w-(--radix-dropdown-menu-trigger-width) min-w-60"
            side="top"
          >
            <DropdownMenuLabel className="truncate font-normal text-muted-foreground">
              {data.user.email}
            </DropdownMenuLabel>
            {children}
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
            {data.user.is_superuser && (
              <DropdownMenuItem asChild>
                <Link href="/admin/llm">
                  <ServerCogIcon />
                  Quản trị LLM
                </Link>
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
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
