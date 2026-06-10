import React from "react";
import type { Spec } from "./types";
import { ShinyreactRenderer } from "./renderer";
import { getOrCreateRoot, hasRoot, unmountRoot } from "./roots";

// Shiny output binding for .shinyreact-output elements.
class ShinyreactOutputBinding extends Shiny.OutputBinding {
  find(scope: Element): ArrayLike<Element> {
    return $(scope).find(".shinyreact-output");
  }

  renderValue(el: Element, data: Spec | null): void {
    if (!data) {
      if (hasRoot(el)) unmountRoot(el);
      return;
    }
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(React.createElement(ShinyreactRenderer, { spec: data }));
  }

  renderError(el: Element, err: { message: string }): void {
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(
      React.createElement(
        "div",
        { style: { color: "red", padding: "8px" } },
        err.message,
      ),
    );
  }
}

/**
 * Register shinyreact's output binding with Shiny. Shiny is always loaded
 * before this runs because HTMLDependency ordering places Shiny's scripts
 * first.
 */
export function registerShinyreactOutputBinding(): void {
  Shiny.outputBindings.register(
    new ShinyreactOutputBinding(),
    "shinyreact.output",
  );
}
