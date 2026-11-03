"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { ArrowDownIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Closer than this to the end counts as at the end. */
const END_SLACK_PX = 8;
/** Room above a sent question moved to the top. */
const TOP_GAP_PX = 24;

/**
 * The chat's scroll area. It never follows the content: a step opening or
 * reasoning streaming grows below while the view stays where it is. Only
 * these move it:
 * - opening the chat puts it at the end, and keeps it there while late
 *   content (highlighted code, math) settles, until the reader touches it;
 * - a question just sent (`anchorId`, a row's `data-row-id`) moves to the
 *   top, with room below for the answer to grow into;
 * - the button goes to the end.
 */
export function ChatScroller({
  anchorId,
  children,
}: {
  anchorId?: string | null;
  children: React.ReactNode;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const spacerRef = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);
  const [atEnd, setAtEnd] = useState(true);
  // The room stays once the turn ends, or the view would jump when it went.
  const [anchor, setAnchor] = useState(anchorId);
  if (anchorId && anchorId !== anchor) setAnchor(anchorId);

  const update = useCallback(() => {
    const scroller = scrollRef.current;
    const content = contentRef.current;
    const spacer = spacerRef.current;
    if (!scroller || !content || !spacer) return;
    const question = anchor ? questionTop(scroller, content, anchor) : null;
    const room = question === null ? 0 : question - TOP_GAP_PX + scroller.clientHeight;
    spacer.style.height = `${Math.max(0, room - content.offsetHeight)}px`;
    if (pinned.current) scroller.scrollTop = scroller.scrollHeight;
    setAtEnd(scroller.scrollHeight - scroller.clientHeight - scroller.scrollTop <= END_SLACK_PX);
  }, [anchor]);

  useLayoutEffect(() => {
    const scroller = scrollRef.current;
    const content = contentRef.current;
    if (!scroller || !content) return;
    update();
    const observer = new ResizeObserver(update);
    observer.observe(scroller);
    observer.observe(content);
    return () => observer.disconnect();
  }, [update]);

  useEffect(() => {
    const scroller = scrollRef.current;
    const content = contentRef.current;
    if (!anchor || !scroller || !content) return;
    const top = questionTop(scroller, content, anchor);
    if (top === null) return;
    pinned.current = false;
    scroller.scrollTo({ top: top - TOP_GAP_PX, behavior: "smooth" });
  }, [anchor]);

  const release = () => {
    pinned.current = false;
  };

  return (
    <div className="relative min-h-0 flex-1">
      <div
        className="size-full overflow-y-auto"
        onKeyDown={release}
        onPointerDown={release}
        onScroll={update}
        onTouchStart={release}
        onWheel={release}
        ref={scrollRef}
        role="log"
      >
        <div ref={contentRef}>{children}</div>
        <div aria-hidden ref={spacerRef} />
      </div>
      {!atEnd && (
        <Button
          aria-label="Xuống cuối"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full"
          onClick={() => {
            release();
            const scroller = scrollRef.current;
            scroller?.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" });
          }}
          size="icon"
          type="button"
          variant="outline"
        >
          <ArrowDownIcon />
        </Button>
      )}
    </div>
  );
}

/** Where a row starts in the scrolled content, or null when it is not drawn. */
function questionTop(scroller: HTMLElement, content: HTMLElement, rowId: string): number | null {
  const row = content.querySelector(`[data-row-id="${CSS.escape(rowId)}"]`);
  if (!row) return null;
  return row.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop;
}
