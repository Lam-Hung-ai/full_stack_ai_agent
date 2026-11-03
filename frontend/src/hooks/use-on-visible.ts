"use client";

import { useEffect, useRef } from "react";

/**
 * A ref for an element; `onVisible` runs when it comes within reach of the
 * screen (200px early) while `enabled`. Re-enabling checks again, so a list
 * still too short after one page loads the next one too.
 */
export function useOnVisible<T extends Element>(onVisible: () => void, enabled: boolean) {
  const ref = useRef<T>(null);
  const latest = useRef(onVisible);
  useEffect(() => {
    latest.current = onVisible;
  }, [onVisible]);

  useEffect(() => {
    const element = ref.current;
    if (!element || !enabled) return;
    const observer = new IntersectionObserver(
      (entries) => entries.some((entry) => entry.isIntersecting) && latest.current(),
      { rootMargin: "200px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [enabled]);

  return ref;
}
