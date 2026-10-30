"use client";

import { useRef } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { v7 as uuidv7 } from "uuid";
import { copySharedConversation, getSharedConversation } from "../api/shares-api";

/** What a link shows depends on who reads it (organization links, "Hỏi
 *  tiếp"), so the viewer is part of the key. */
export function shareKey(token: string, viewerId: string | null) {
  return ["shares", token, viewerId ?? "anonymous"] as const;
}

/** `ready`: wait until the session is known, so a member's token is sent. */
export function useSharedConversation(token: string, viewerId: string | null, ready: boolean) {
  return useQuery({
    queryKey: shareKey(token, viewerId),
    queryFn: ({ signal }) => getSharedConversation(token, signal),
    enabled: ready,
  });
}

export function useCopySharedConversation(token: string) {
  // One id for this page: pressing again after a failure resumes that copy.
  const requestId = useRef(uuidv7());
  return useMutation({ mutationFn: () => copySharedConversation(token, requestId.current) });
}
