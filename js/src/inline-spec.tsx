import React from "react";
import type { Spec } from "./spec";
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

/**
 * Seed static mounts present at load, then watch for any inserted later. Safe
 * to call at bundle load; runs immediately if the document is already parsed.
 */
export function installInlineSpecSeeding(): void {
  const init = () => {
    seedInlineSpecs();
    startMountObserver();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}

/**
 * Stop the post-load mount observer. Intended for tests; production code keeps
 * the observer running for the lifetime of the page.
 */
export function _stopMountObserverForTests(): void {
  mountObserver?.disconnect();
  mountObserver = null;
}
