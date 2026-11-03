"use client";

import { useEffect, useState } from "react";

/**
 * Whole seconds since `active` turned on, ticking once a second; it stops
 * (and keeps its last value) while inactive.
 */
export function useElapsedSeconds(active: boolean): number {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!active) return;
    const start = Date.now();
    const timer = setInterval(() => setSeconds(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [active]);
  return seconds;
}
