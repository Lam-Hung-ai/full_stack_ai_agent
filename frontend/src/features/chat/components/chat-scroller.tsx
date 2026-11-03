"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { ArrowDownIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Closer than this to the end counts as at the end. */
const END_SLACK_PX = 8;
/** Room above a sent question moved to the top. */
const TOP_GAP_PX = 24;
/** A scroll this soon after the reader's input is theirs, not the page's. */
const INPUT_WINDOW_MS = 800;
/** Keys that act on what has focus rather than scroll. */
const ACTIVATE_KEYS = new Set(["Enter", " "]);
const UP_KEYS = new Set(["ArrowUp", "PageUp", "Home"]);
const DOWN_KEYS = new Set(["ArrowDown", "PageDown", " "]);

/**
 * The chat's scroll area. It follows new content only while the reader asks
 * for it, and never guesses:
 * - Following starts when they go to the end themselves (scroll, wheel or
 *   arrow down at the end, End, or the button), and on opening the chat,
 *   which starts there.
 * - It stops as soon as they scroll up, or act on the content (open a step,
 *   select text), so what they are reading stays put while it grows below.
 * - A question just sent (`anchorId`, a row's `data-row-id`) moves to the
 *   top with room below for the answer, and is not followed: the answer
 *   is read from its start, until the reader goes to the end.
 * The button shows whenever there is more below and the view is not
 * following, so which of the two it is doing can always be seen.
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
  const following = useRef(true);
  const lastInput = useRef(0);
  const lastTop = useRef(0);
  const [atEnd, setAtEnd] = useState(true);
  // The room stays once the turn ends, or the view would jump when it went.
  const [anchor, setAnchor] = useState(anchorId);
  if (anchorId && anchorId !== anchor) setAnchor(anchorId);

  const measure = useCallback(() => {
    const scroller = scrollRef.current;
    if (!scroller) return;
    setAtEnd(endOf(scroller) - scroller.scrollTop <= END_SLACK_PX);
  }, []);

  const update = useCallback(() => {
    const scroller = scrollRef.current;
    const content = contentRef.current;
    const spacer = spacerRef.current;
    if (!scroller || !content || !spacer) return;
    const question = anchor ? questionTop(scroller, content, anchor) : null;
    const room = question === null ? 0 : question - TOP_GAP_PX + scroller.clientHeight;
    spacer.style.height = `${Math.max(0, room - content.offsetHeight)}px`;
    if (following.current) scroller.scrollTop = endOf(scroller);
    measure();
  }, [anchor, measure]);

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
    following.current = false;
    scroller.scrollTo({ top: top - TOP_GAP_PX, behavior: "smooth" });
  }, [anchor]);

  const onScroll = () => {
    const scroller = scrollRef.current;
    if (!scroller) return;
    const top = scroller.scrollTop;
    if (performance.now() - lastInput.current < INPUT_WINDOW_MS) {
      if (top < lastTop.current - 1) following.current = false;
      else if (endOf(scroller) - top <= END_SLACK_PX) following.current = true;
    }
    lastTop.current = top;
    measure();
  };

  const stopFollowing = () => {
    following.current = false;
  };
  const markInput = () => {
    lastInput.current = performance.now();
  };

  return (
    <div className="relative min-h-0 flex-1">
      <div
        className="size-full overflow-y-auto"
        onKeyDown={(event) => {
          if (event.target !== event.currentTarget && ACTIVATE_KEYS.has(event.key)) {
            stopFollowing();
            return;
          }
          markInput();
          // The browser animates these, so the end has moved by the time
          // it gets there: the key says it.
          if (event.key === "End" || (atEnd && DOWN_KEYS.has(event.key))) following.current = true;
          else if (UP_KEYS.has(event.key)) stopFollowing();
        }}
        onPointerDown={(event) => {
          stopFollowing();
          // On the scroll area itself: its scrollbar is being dragged.
          if (event.target === event.currentTarget) markInput();
        }}
        onScroll={onScroll}
        onTouchStart={() => {
          stopFollowing();
          markInput();
        }}
        onTouchMove={markInput}
        onWheel={(event) => {
          markInput();
          if (event.deltaY < 0) stopFollowing();
          else if (atEnd) following.current = true;
        }}
        ref={scrollRef}
        role="log"
        // Focusable, so the keyboard can scroll it (End, Page Down).
        tabIndex={0}
      >
        <div ref={contentRef}>{children}</div>
        <div aria-hidden ref={spacerRef} />
      </div>
      {!atEnd && (
        <Button
          aria-label="Xuống cuối và theo dõi câu trả lời"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full"
          onClick={() => {
            following.current = true;
            const scroller = scrollRef.current;
            scroller?.scrollTo({ top: endOf(scroller), behavior: "smooth" });
          }}
          size="icon"
          title="Xuống cuối"
          type="button"
          variant="outline"
        >
          <ArrowDownIcon />
        </Button>
      )}
    </div>
  );
}

function endOf(scroller: HTMLElement): number {
  return scroller.scrollHeight - scroller.clientHeight;
}

/** Where a row starts in the scrolled content, or null when it is not drawn. */
function questionTop(scroller: HTMLElement, content: HTMLElement, rowId: string): number | null {
  const row = content.querySelector(`[data-row-id="${CSS.escape(rowId)}"]`);
  if (!row) return null;
  return row.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop;
}
