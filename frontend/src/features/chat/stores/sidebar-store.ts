import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ConversationSort } from "../types/chat.types";

export type RecentStatus = "active" | "archived";
export type RecentGrouping = "none" | "day";

/** How the "Gần đây" list is filtered, grouped and sorted; kept per browser. */
type SidebarView = {
  status: RecentStatus;
  grouping: RecentGrouping;
  sort: ConversationSort;
  setStatus: (status: RecentStatus) => void;
  setGrouping: (grouping: RecentGrouping) => void;
  setSort: (sort: ConversationSort) => void;
};

export const useSidebarStore = create<SidebarView>()(
  persist(
    (set) => ({
      status: "active",
      grouping: "none",
      sort: "updated",
      setStatus: (status) => set({ status }),
      setGrouping: (grouping) => set({ grouping }),
      setSort: (sort) => set({ sort }),
    }),
    {
      name: "chat-sidebar-view",
      partialize: ({ status, grouping, sort }) => ({ status, grouping, sort }),
    },
  ),
);
