"use client";

import { useState } from "react";
import { CheckIcon, CopyIcon } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { ApiError } from "@/lib/api";
import { useShare, useShareActions } from "../hooks/use-share";

const dateFormat = new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" });

const ERRORS: Record<string, string> = {
  conversation_busy: "Đang có câu trả lời chưa xong. Hãy chia sẻ khi lượt đã kết thúc.",
  nothing_to_share: "Chat chưa có nội dung để chia sẻ.",
  permission_denied: "Bạn không có quyền chia sẻ chat trong tổ chức này.",
};

function shareError(error: unknown): string {
  return (error instanceof ApiError && ERRORS[error.code]) || "Đã có lỗi xảy ra. Vui lòng thử lại.";
}

/**
 * Share a chat as a snapshot: everything it holds now, all versions. Later
 * messages are not shared until the owner updates the snapshot.
 */
export function ShareDialog({
  conversationId,
  isPersonal,
  onClose,
}: {
  conversationId: string;
  isPersonal: boolean;
  onClose: () => void;
}) {
  const share = useShare(conversationId);
  const { publish, revoke } = useShareActions(conversationId);
  const [copied, setCopied] = useState<boolean | "failed">(false);
  const error = publish.error ?? revoke.error;

  const copyLink = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
    } catch {
      // No clipboard access (permission, plain HTTP): copy it by hand.
      setCopied("failed");
    }
  };

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Chia sẻ cuộc trò chuyện</DialogTitle>
          <DialogDescription>
            {isPersonal
              ? "Ai có link đều xem được, không cần đăng nhập. Người xem đăng nhập có thể hỏi tiếp trên bản sao của họ."
              : "Chỉ thành viên đang hoạt động của tổ chức có link mới xem được."}{" "}
            Bản chia sẻ là ảnh chụp lúc này, gồm mọi phiên bản câu trả lời.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{shareError(error)}</AlertDescription>
          </Alert>
        )}
        {share.isPending ? (
          <Spinner aria-label="Đang tải" />
        ) : share.data ? (
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <Input aria-label="Link chia sẻ" readOnly value={share.data.url} />
              <Button
                aria-label="Sao chép link"
                onClick={() => void copyLink(share.data!.url)}
                size="icon"
                variant="outline"
              >
                {copied === true ? <CheckIcon /> : <CopyIcon />}
              </Button>
            </div>
            {copied === "failed" && (
              <p className="text-destructive text-xs">
                Không sao chép tự động được; hãy chọn link ở trên và sao chép.
              </p>
            )}
            <p className="text-muted-foreground text-xs">
              Phiên bản {share.data.version}, cập nhật {dateFormat.format(new Date(share.data.published_at))}
            </p>
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">Chat này chưa được chia sẻ.</p>
        )}
        <DialogFooter className="gap-2 sm:justify-between">
          {share.data ? (
            <Button disabled={revoke.isPending} onClick={() => revoke.mutate()} variant="destructive">
              Thu hồi link
            </Button>
          ) : (
            <span />
          )}
          <Button disabled={publish.isPending} onClick={() => publish.mutate()}>
            {share.data ? "Cập nhật bản chia sẻ" : "Tạo link chia sẻ"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
