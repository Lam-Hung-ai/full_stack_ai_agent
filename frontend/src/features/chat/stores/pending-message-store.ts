import { create } from "zustand";

/**
 * First question typed on the new-chat screen. The conversation is created
 * first, then its page sends this once it has mounted. Memory only.
 */
type PendingMessage = {
  pending: { conversationId: string; text: string } | null;
  setPending: (conversationId: string, text: string) => void;
  take: (conversationId: string) => string | null;
};

export const usePendingMessageStore = create<PendingMessage>()((set, get) => ({
  pending: null,
  setPending: (conversationId, text) => set({ pending: { conversationId, text } }),
  take: (conversationId) => {
    const { pending } = get();
    if (pending?.conversationId !== conversationId) return null;
    set({ pending: null });
    return pending.text;
  },
}));
