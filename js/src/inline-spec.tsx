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

    let spec: Spec;
    try {
      spec = JSON.parse(script.textContent || "null");
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
 * Install `seedInlineSpecs` to run once the DOM is ready. Safe to call at
 * bundle load; runs immediately if the document is already parsed.
 */
export function installInlineSpecSeeding(): void {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", seedInlineSpecs);
  } else {
    seedInlineSpecs();
  }
}
