import React from "react";
import type { Spec } from "./types";
import { ShinyreactRenderer } from "./renderer";
import { getOrCreateRoot, hasRoot } from "./roots";

/**
 * Render a single `.shinyreact-static` mount from its child
 * `<script type="application/json">` payload. Mounts that already have a React
 * root are skipped, keeping every seeding pass idempotent.
 */
function seedMount(el: HTMLElement): void {
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
}

/**
 * Render every `.shinyreact-static` mount within `root` (default: the whole
 * document) from its child `<script type="application/json">` payload.
 *
 * This is the delivery path for `Node` objects embedded directly in page
 * chrome (no server render function, no output id). The script is linked to
 * its mount by DOM adjacency (it is the div's child), so no id is needed.
 *
 * `root` may be the document, a freshly inserted element, or any other
 * `ParentNode`. When `root` is itself a static mount (e.g. a node handed
 * straight from a `MutationObserver` record), it is seeded too — not just its
 * descendants.
 */
export function seedInlineSpecs(root: ParentNode = document): void {
  if (root instanceof HTMLElement && root.matches(".shinyreact-static")) {
    seedMount(root);
  }
  root
    .querySelectorAll<HTMLElement>(".shinyreact-static")
    .forEach((el) => seedMount(el));
}

// Standing observer for static mounts inserted after load (e.g. Node.tagify()
// delivered via @render.ui / insertUI over the WebSocket). Module-scoped so
// installInlineSpecSeeding() is idempotent.
let mountObserver: MutationObserver | null = null;

/**
 * Watch for `.shinyreact-static` mounts inserted after page load and seed them.
 *
 * Shiny exposes no scope-level "content inserted" event and no binding type for
 * id-less content, so a `MutationObserver` is the only Shiny-version-independent
 * hook. The callback stays cheap: it only inspects added element nodes and
 * relies on `seedMount`'s `hasRoot` guard for idempotency, so re-observing an
 * already-seeded subtree is a no-op.
 */
function startMountObserver(): void {
  if (mountObserver || typeof MutationObserver === "undefined") return;
  mountObserver = new MutationObserver((records) => {
    for (const record of records) {
      record.addedNodes.forEach((node) => {
        if (node instanceof HTMLElement) seedInlineSpecs(node);
      });
    }
  });
  mountObserver.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
}

// Seed mounts present now, then watch for any inserted later. A stable module
// reference so install listeners can be deregistered (used by tests).
function seedAndObserve(): void {
  seedInlineSpecs();
  startMountObserver();
}

/**
 * Install seeding to run once the page's parse-time scripts have all executed,
 * then watch for static mounts inserted later. Safe to call at bundle load.
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
 * (e.g. a non-`defer` injection); seeding is idempotent, so a double fire is
 * harmless. When the document is already `complete` there is no future event to
 * wait for, so we run at once.
 *
 * The post-load `MutationObserver` is started by the same deferred callback, so
 * it only begins observing after the registry is complete — a mount it caught
 * mid-parse would hit the same incomplete-registry trap (#123).
 */
export function installInlineSpecSeeding(): void {
  if (document.readyState === "complete") {
    seedAndObserve();
  } else {
    document.addEventListener("DOMContentLoaded", seedAndObserve, {
      once: true,
    });
    window.addEventListener("load", seedAndObserve, { once: true });
  }
}

/**
 * Stop the post-load mount observer and remove any pending install listeners.
 * Intended for tests; production keeps the observer running for the page's life.
 */
export function _stopMountObserverForTests(): void {
  mountObserver?.disconnect();
  mountObserver = null;
  document.removeEventListener("DOMContentLoaded", seedAndObserve);
  window.removeEventListener("load", seedAndObserve);
}
