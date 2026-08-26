import React from "react";
export interface ShinyOutputProps extends React.HTMLAttributes<HTMLElement> {
    id: string;
    tagName?: string;
    /**
     * Namespace to prefix `id` with on the rendered element.
     *
     * - `undefined` (default): use the namespace from the enclosing
     *   `ShinyModuleProvider`, or no prefix if there isn't one.
     * - A string: override the context namespace.
     * - `null`: opt out of context — render the bare `id`. Useful when `id`
     *   already contains a prefix (e.g. ImageOutput's clientdata IDs).
     */
    namespace?: string | null;
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
export declare function ShinyOutput({ id, tagName, namespace: explicitNamespace, ...rest }: ShinyOutputProps): React.JSX.Element;
