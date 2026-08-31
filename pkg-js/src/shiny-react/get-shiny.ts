import { type ShinyClassExtended } from "./index";

/**
 * Get the Shiny object if it is available.
 *
 * `typeof window` rather than a bare `window`: this is reached from debounce
 * timers and event callbacks that can outlive the document — a jsdom test
 * tearing down between the last `setShinyInputValue` and its 100ms debounce, or
 * a page/iframe unloading — and there the bare identifier is a `ReferenceError`,
 * not `undefined`. Every caller already treats a missing Shiny as "do nothing",
 * so returning `undefined` degrades exactly the way they expect.
 */
export function getShiny(): ShinyClassExtended | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.Shiny;
}
