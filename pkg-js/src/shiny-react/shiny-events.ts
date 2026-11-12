import { getShiny } from "./get-shiny";

type JQueryDocument = {
  on(type: string, fn: () => void): unknown;
  off(type: string, fn: () => void): unknown;
};

/**
 * Listen for a Shiny lifecycle event (`shiny:connected`, `shiny:busy`, ...) on
 * `document`, and return a function that stops listening.
 *
 * Shiny fires these with jQuery's `trigger()`, which calls jQuery handlers
 * only — an `addEventListener()` listener never sees them (#328). So listen
 * through jQuery when the page has it. A jQuery handler also receives native
 * `dispatchEvent()` events, so either kind of sender reaches it.
 *
 * Without jQuery (no Shiny page, or jsdom tests) fall back to a native
 * listener. `window.jQuery` is read at call time, so this must run after
 * jQuery loads; Shiny itself needs jQuery, so a page with `window.Shiny` and
 * no `window.jQuery` is a load-order bug, and we warn.
 *
 * Not handled: a second jQuery loaded after Shiny's replaces `window.jQuery`,
 * and Shiny's `trigger()` only calls handlers bound through its own copy.
 */
export function onShinyEvent(type: string, fn: () => void): () => void {
  const jQuery = (window as { jQuery?: (el: Document) => JQueryDocument })
    .jQuery;
  if (jQuery) {
    jQuery(document).on(type, fn);
    return () => jQuery(document).off(type, fn);
  }
  if (getShiny()) {
    console.warn(
      `[shinyreact] window.Shiny is present but window.jQuery is not; ` +
        `"${type}" will never be heard.`,
    );
  }
  document.addEventListener(type, fn);
  return () => document.removeEventListener(type, fn);
}
