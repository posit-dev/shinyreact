/**
 * Explain the missing Bootstrap modal instead of letting Shiny throw.
 *
 * Shiny shows a modal by running `$('#shiny-modal').modal()` — Bootstrap's
 * jQuery plugin. That covers `showModal()` / `modal_show()`, and the bookmark
 * URL dialog `session$doBookmark()` / `session.bookmark()` falls back to when
 * the app registered no `onBookmarked()` callback. `page_react()` loads no
 * Bootstrap (#285), so the browser threw a bare `$(...).modal is not a
 * function` (#326).
 *
 * Page scope: this writes to `jQuery.fn`, because Shiny's inline modal script
 * calls the page's jQuery and nothing else can answer it. It only fills an
 * empty slot, so Bootstrap already on the page, or a second copy of this
 * bundle, is left alone; Bootstrap loaded later overwrites it.
 */
export const MODAL_FALLBACK_MESSAGE =
  "[shinyreact] Shiny tried to open a Bootstrap modal, but this page has no " +
  "Bootstrap. If you are bookmarking, register your own callback: " +
  "onBookmarked(function(url) updateQueryString(url)) in R, or " +
  "session.bookmark.on_bookmarked(session.bookmark.update_query_string) in " +
  "Python. For showModal() / modal_show(), build the dialog in React instead.";

export function installModalFallback(): void {
  if (typeof window === "undefined") return;
  const jQuery = (window as { jQuery?: { fn?: Record<string, unknown> } })
    .jQuery;
  if (!jQuery?.fn || jQuery.fn.modal) return;
  jQuery.fn.modal = function <T>(this: T): T {
    console.error(MODAL_FALLBACK_MESSAGE);
    return this;
  };
}
