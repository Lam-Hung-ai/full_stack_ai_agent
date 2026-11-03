import { create } from "zustand";
import { persist } from "zustand/middleware";

type WorkspaceSelection = {
  /** Last workspace the user chose. Only an id: the list itself is server
   *  state, and the backend re-checks membership on every request. */
  selectedWorkspaceId: string | null;
  selectWorkspace: (workspaceId: string) => void;
};

export const useWorkspaceStore = create<WorkspaceSelection>()(
  persist(
    (set) => ({
      selectedWorkspaceId: null,
      selectWorkspace: (workspaceId) => set({ selectedWorkspaceId: workspaceId }),
    }),
    { name: "workspace-selection" },
  ),
);
