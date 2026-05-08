import React, { useEffect, useRef } from "react";

export interface ShinyOutputProps
  extends React.HTMLAttributes<HTMLElement> {
  id: string;
  tagName?: string;
}

/**
 * Renders a Shiny output element (input element by class, e.g. `plotly-output`,
 * or by tag name, e.g. `shiny-data-frame`) inside a React tree, and registers
 * it with Shiny so server-driven updates flow through.
 *
 * No wrapper element: the `ref` goes straight onto the rendered element so
 * direct-child CSS (flex `gap`, `> *` selectors, grid layouts) works as the
 * caller expects. See https://github.com/posit-dev/shinyreact/issues/61.
 *
 * Binding-scope notes (the asymmetry between bindAll and unbindAll is
 * intentional — Shiny's API is asymmetric):
 *
 *   • `Shiny.bindAll(scope)` is descendants-only — output bindings call
 *     `$(scope).find(selector)`, which excludes `scope` itself. So we pass
 *     the *parent* element as scope, guaranteeing our element is found.
 *     This is safe to call repeatedly: Shiny skips elements already marked
 *     `.shiny-bound-output` / `.shiny-bound-input`, so re-binding the parent
 *     does not re-bind sibling outputs.
 *
 *   • `Shiny.unbindAll(scope)` would unbind every Shiny output under
 *     `scope`, which would clobber siblings. Instead we pass our own element
 *     with `includeSelf=true`, so only this output is unbound.
 */
export function ShinyOutput({
  id,
  tagName = "div",
  ...rest
}: ShinyOutputProps): React.JSX.Element {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    const scope = el?.parentElement;
    if (!el || !scope || !window.Shiny?.bindAll) return;
    void window.Shiny.bindAll(scope);
    return () => {
      window.Shiny?.unbindAll?.(el, true);
    };
  }, [id, tagName]);

  return React.createElement(tagName, { id, ref, ...rest });
}
