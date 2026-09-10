import React, { useEffect, useRef } from "react";
import { useNamespacedId } from "./shiny-react/ShinyModuleContext";

/**
 * `Shiny.bindAll(scope)` is `async`, and Shiny's own `bindOutputs()` marks
 * a matched element `.shiny-bound-output` only *after* an `await` for that
 * element resolves. Several `ShinyOutput` siblings sharing one parent all
 * pass that same parent as `scope` (see the file comment below), and React
 * fires all their mount effects in the same commit, so several `bindAll()`
 * calls can start scanning that same parent before any of them has marked
 * anything bound yet. Each such call then (re-)binds every sibling it
 * finds, which Shiny's own "Duplicate output IDs" bookkeeping records
 * permanently, one entry per call, even though there is really only one
 * DOM element per id.
 *
 * The fix: track one in-flight `bindAll()` call per scope element. A
 * second `ShinyOutput` sibling whose effect runs while the first one's
 * call for the same element is still pending reuses that same call
 * instead of starting a second, overlapping scan, so there is never more
 * than one scan of a given scope in flight at once.
 */
const pendingBindAll = new WeakMap<HTMLElement, Promise<unknown>>();

function dedupedBindAll(scope: HTMLElement): Promise<unknown> {
  const inFlight = pendingBindAll.get(scope);
  if (inFlight) return inFlight;
  const promise = Promise.resolve(window.Shiny!.bindAll!(scope)).finally(() => {
    if (pendingBindAll.get(scope) === promise) {
      pendingBindAll.delete(scope);
    }
  });
  pendingBindAll.set(scope, promise);
  return promise;
}

/**
 * An in-flight `bindAll(scope)` call only stands in for a *later* one that
 * would see the exact same, unchanged DOM. `Shiny.unbindAll(el, true)` is
 * synchronous and runs as one `ShinyOutput`'s cleanup, immediately before
 * the *next* mount effect that reuses the same `scope` (an id or tagName
 * change: React runs the old effect's cleanup and the new effect back to
 * back). That next effect's own scan needs to see the just-unbound element
 * as unbound again, not reuse a promise for a scan that ran before the
 * unbind happened. So an unbind under `scope` drops any cached promise for
 * it, forcing the next `dedupedBindAll(scope)` call to run a fresh scan.
 */
function invalidateBindAll(scope: HTMLElement): void {
  pendingBindAll.delete(scope);
}

/** @group Components */
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
 * @group Components
 */
export function ShinyOutput({
  id,
  tagName = "div",
  namespace: explicitNamespace,
  ...rest
}: ShinyOutputProps): React.JSX.Element {
  const namespacedId = useNamespacedId(id, explicitNamespace);

  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    const scope = el?.parentElement;
    if (!el || !scope || !window.Shiny?.bindAll) return;

    const logError = (err: unknown, phase: "bindAll" | "unbindAll") => {
      // TODO(future): expose an `onError?: (err, phase) => void` prop so
      // downstream callers can integrate telemetry or React error boundaries.
      console.error(
        `[shinyreact] ShinyOutput "${namespacedId}" ${phase} failed:`,
        { id: namespacedId, phase, error: err },
      );
    };

    try {
      dedupedBindAll(scope).catch((err) => logError(err, "bindAll"));
    } catch (err) {
      logError(err, "bindAll");
    }

    return () => {
      invalidateBindAll(scope);
      try {
        window.Shiny?.unbindAll?.(el, true);
      } catch (err) {
        logError(err, "unbindAll");
      }
    };
  }, [namespacedId, tagName]);

  return React.createElement(tagName, { id: namespacedId, ref, ...rest });
}
