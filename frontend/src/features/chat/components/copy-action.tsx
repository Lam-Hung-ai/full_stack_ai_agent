"use client";

import { useEffect, useState } from "react";
import { CheckIcon, CopyIcon } from "lucide-react";
import { toast } from "sonner";
import { MessageAction } from "@/components/ai-elements/message";

const COPIED_MS = 2_000;

/** Copies `text`; the icon turns into a tick for a moment. */
export function CopyAction({ text, label = "Sao chép" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), COPIED_MS);
    return () => clearTimeout(timer);
  }, [copied]);

  return (
    <MessageAction
      label={copied ? "Đã sao chép" : label}
      onClick={() =>
        navigator.clipboard.writeText(text).then(
          () => setCopied(true),
          () => toast.error("Không sao chép được."),
        )
      }
      tooltip={copied ? "Đã sao chép" : label}
    >
      {copied ? <CheckIcon /> : <CopyIcon />}
    </MessageAction>
  );
}
