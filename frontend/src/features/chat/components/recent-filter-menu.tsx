"use client";

import { ListFilterIcon } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarGroupAction } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { type RecentGrouping, type RecentStatus, useSidebarStore } from "../stores/sidebar-store";
import type { ConversationSort } from "../types/chat.types";

const STATUS: Record<RecentStatus, string> = { active: "Đang dùng", archived: "Đã lưu trữ" };
const GROUPING: Record<RecentGrouping, string> = { none: "Không", day: "Theo ngày" };
const SORT: Record<ConversationSort, string> = {
  updated: "Hoạt động gần nhất",
  created: "Ngày tạo",
};

/** The "Gần đây" filter: status, grouping and order, each a submenu of choices. */
export function RecentFilterMenu() {
  const view = useSidebarStore();
  const changed = view.status !== "active" || view.grouping !== "none" || view.sort !== "updated";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <SidebarGroupAction
          aria-label="Lọc cuộc trò chuyện gần đây"
          className={cn("top-2.5", changed && "bg-sidebar-accent")}
          title="Lọc"
        >
          <ListFilterIcon />
        </SidebarGroupAction>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64" side="right">
        <Choice label="Trạng thái" onChange={view.setStatus} options={STATUS} value={view.status} />
        <Choice
          label="Nhóm theo"
          onChange={view.setGrouping}
          options={GROUPING}
          value={view.grouping}
        />
        <Choice label="Sắp xếp" onChange={view.setSort} options={SORT} value={view.sort} />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function Choice<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Record<T, string>;
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger>
        <span>{label}</span>
        <span className="ml-auto text-muted-foreground text-xs">{options[value]}</span>
      </DropdownMenuSubTrigger>
      <DropdownMenuSubContent className="w-48">
        <DropdownMenuRadioGroup onValueChange={(next) => onChange(next as T)} value={value}>
          {(Object.keys(options) as T[]).map((key) => (
            <DropdownMenuRadioItem key={key} value={key}>
              {options[key]}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuSubContent>
    </DropdownMenuSub>
  );
}
