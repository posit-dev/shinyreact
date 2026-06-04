import React from "react";
import type { Spec } from "./spec";
import { ShinyreactRenderer } from "./renderer";
import { getOrCreateRoot, hasRoot } from "./roots";

/**
 * Render every `.shinyreact-static` mount from its child
 * `<script type="application/json">` payload.
 *
 * This is the delivery path for `Node` objects embedded directly in page
 * chrome (no server render function, no output id). The script is linked to
 * its mount by DOM adjacency (it is the div's child), so no id is needed.
 * Mounts that already have a React root are skipped, keeping the pass
 * idempotent.
 */
export function seedInlineSpecs(): void {
  const mounts = document.querySelectorAll<HTMLElement>(".shinyreact-static");
  mounts.forEach((el) => {
    if (hasRoot(el)) return;
    const script = el.querySelector<HTMLScriptElement>(
      ':scope > script[type="application/json"]',
    );
    if (!script) return;

    let spec: Spec | null;
    try {
      spec = JSON.parse(script.textContent || "null") as Spec | null;
    } catch (err) {
      console.error("[shinyreact] failed to parse inline static spec:", err);
      return;
    }
    if (spec == null) return;

    const root = getOrCreateRoot(el);
    root.render(React.createElement(ShinyreactRenderer, { spec }));
  });
}

/**
 * Install `seedInlineSpecs` to run once the page's parse-time scripts have all
 * executed. Safe to call at bundle load.
 *
 * A static mount may reference React components registered by a *sibling*
 * bundle (e.g. a downstream package). Both bundles ship as `defer` scripts, so
 * the shinyreact bundle commonly runs first — at `readyState === "interactive"`
 * — *before* the sibling has registered its components. Seeding right then
 * renders against an incomplete registry: the renderer throws on the unknown
 * component and the mount's React root is poisoned for good (a later seed pass
 * skips it via `hasRoot`). See issue #123.
 *
 * `DOMContentLoaded` fires only after every parse-time `defer`/module script has
 * executed, so by then all sibling registrations have landed. We wait for it
 * rather than seeding immediately. `load` is a safety net for the rare case
 * where this runs after `DOMContentLoaded` has already fired but before `load`
 * (e.g. a non-`defer` injection); `seedInlineSpecs` is idempotent, so a double
 * fire is harmless. When the document is already `complete` there is no future
 * event to wait for, so we seed at once.
 */
export function installInlineSpecSeeding(): void {
  if (document.readyState === "complete") {
    seedInlineSpecs();
  } else {
    document.addEventListener("DOMContentLoaded", seedInlineSpecs, {
      once: true,
    });
    window.addEventListener("load", seedInlineSpecs, { once: true });
  }
}
