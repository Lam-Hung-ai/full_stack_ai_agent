import { create } from "zustand";
import type { ComposerDraft } from "../components/chat-composer";

/**
 * First question typed on the new-chat screen. The conversation is created
 * first, then its page sends this once it has mounted. Memory only.
 */
type PendingMessage = {
  pending: { conversationId: string; draft: ComposerDraft } | null;
  setPending: (conversationId: string, draft: ComposerDraft) => void;
  take: (conversationId: string) => ComposerDraft | null;
};

export const usePendingMessageStore = create<PendingMessage>()((set, get) => ({
  pending: null,
  setPending: (conversationId, draft) => set({ pending: { conversationId, draft } }),
  take: (conversationId) => {
    const { pending } = get();
    if (pending?.conversationId !== conversationId) return null;
    set({ pending: null });
    return pending.draft;
  },
}));
