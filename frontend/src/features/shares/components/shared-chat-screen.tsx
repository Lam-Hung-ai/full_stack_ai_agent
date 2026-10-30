"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MessageSquarePlusIcon } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useSession } from "@/features/auth";
import { ChatMessages, type FileLinkSource } from "@/features/chat";
import { useSelectWorkspace } from "@/features/workspaces";
import { ApiError } from "@/lib/api";
import { getSharedFileLink } from "../api/shares-api";
import {
  shareKey,
  useCopySharedConversation,
  useSharedConversation,
} from "../hooks/use-shared-conversation";
import { branchRows, latestLeaf } from "../utils/branch";

const dateFormat = new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" });

/** A shared snapshot, read-only; "Hỏi tiếp" continues it as one's own copy. */
export function SharedChatScreen({ token }: { token: string }) {
  const router = useRouter();
  const session = useSession();
  const viewerId = session.data?.user.id ?? null;
  const shared = useSharedConversation(token, viewerId, !session.isPending);
  const copy = useCopySharedConversation(token);
  const selectWorkspace = useSelectWorkspace();
  const [leafId, setLeafId] = useState<string | null>(null);
  const fileSource = useMemo<FileLinkSource>(
    () => ({
      key: shareKey(token, viewerId),
      fetch: (fileId, signal) => getSharedFileLink(token, fileId, signal),
    }),
    [token, viewerId],
  );

  if (session.isPending || shared.isPending) {
    return (
      <div className="flex h-dvh items-center justify-center" aria-busy="true">
        <Spinner aria-label="Đang tải" />
      </div>
    );
  }
  if (shared.isError) {
    const gone = shared.error instanceof ApiError && shared.error.status === 404;
    return (
      <div className="mx-auto max-w-md p-6">
        <Alert variant="destructive">
          <AlertDescription>
            {gone
              ? "Link không tồn tại, đã bị thu hồi, hoặc bạn cần đăng nhập bằng tài khoản thuộc tổ chức đã chia sẻ."
              : "Không tải được nội dung. Vui lòng thử lại."}
          </AlertDescription>
        </Alert>
        {gone && !session.isSuccess && (
          <Button asChild className="mt-4" variant="outline">
            <Link href={`/login?next=${encodeURIComponent(`/s/${token}`)}`}>Đăng nhập</Link>
          </Button>
        )}
      </div>
    );
  }

  const data = shared.data;
  const rows = branchRows(data.messages, leafId ?? data.current_message_id);
  const continueChat = () =>
    copy.mutate(undefined, {
      onSuccess: (result) => {
        selectWorkspace(result.workspace_id);
        router.push(`/c/${result.conversation_id}`);
      },
    });

  return (
    <div className="mx-auto flex h-dvh w-full max-w-3xl flex-col p-4">
      <header className="flex items-center justify-between gap-4 border-b pb-3">
        <div className="min-w-0">
          <h1 className="truncate font-semibold">{data.title}</h1>
          <p className="text-muted-foreground text-xs">
            {data.mode === "public" ? "Chia sẻ công khai" : "Chia sẻ trong tổ chức"} · phiên bản{" "}
            {data.version} · {dateFormat.format(new Date(data.published_at))}
          </p>
        </div>
        {data.can_copy ? (
          <Button disabled={copy.isPending} onClick={continueChat}>
            <MessageSquarePlusIcon />
            {copy.isPending ? "Đang tạo bản sao…" : "Hỏi tiếp"}
          </Button>
        ) : (
          <Button asChild variant="outline">
            <Link href={`/login?next=${encodeURIComponent(`/s/${token}`)}`}>Đăng nhập để hỏi tiếp</Link>
          </Button>
        )}
      </header>
      {copy.isError && (
        <Alert className="mt-3" variant="destructive">
          <AlertDescription>Không tạo được bản sao. Bấm “Hỏi tiếp” để thử lại.</AlertDescription>
        </Alert>
      )}
      <ChatMessages
        actions={{ onSwitch: (id) => setLeafId(latestLeaf(data.messages, id)) }}
        fileSource={fileSource}
        isBusy={false}
        rows={rows}
      />
    </div>
  );
}
