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
 * Nested scopes reach that same window a second way. Two `ShinyOutput`s
 * whose parents are one inside the other — a card body holding outputs,
 * with a `div` of controls nested in that same card body — pass two
 * DIFFERENT scope elements, so keying on the scope element alone does not
 * stop them overlapping, and `bindAll` is descendants-only, so the outer
 * scan walks the inner element too. Both then get past the
 * `.shiny-bound-output` check before either has added the class, and both
 * register it. Catching that needs a check against the in-flight scopes
 * that genuinely overlap this one rather than an exact match, which is
 * what `overlappingPasses` below does.
 *
 * The fix: track one call per scope element, never let a second one start
 * while it is still in flight, and queue a scan behind any in-flight scan
 * whose scope contains or is contained by its own. A `ShinyOutput` sibling
 * whose effect runs in the same commit as another one's call for the same
 * element reuses that same call — but only if that call's scan covers it. One that
 * started before this element existed scanned a DOM without it, so it binds
 * it never and says nothing about it; such a `ShinyOutput` queues a pass of
 * its own instead. An unbind under that scope (an id or tagName
 * change, an unmount, or React StrictMode's synthetic mount-cleanup-mount
 * double invoke) queues a fresh scan for *after* the current one settles,
 * rather than starting one right away: starting one immediately, while an
 * earlier real call for the same scope is still unsettled, is exactly the
 * overlap this exists to prevent, whichever `ShinyOutput` happens to
 * trigger it. A first version of this fix deleted the cached call
 * outright on every unbind, which let a later caller start a second,
 * genuinely concurrent scan while the first was still running: safe for
 * an unbind after the earlier call had already settled, but not for one
 * mid-flight, and StrictMode's double invoke reaches that mid-flight
 * window every time, even for one `ShinyOutput` with no siblings at all.
 */
interface BindAllPass {
  promise: Promise<unknown>;
  /**
   * The scope's children when this pass started scanning them — the only
   * elements it can bind. `null` for a pass that is queued but has not
   * started: it will scan whatever is there when it does.
   */
  covers: WeakSet<Element> | null;
  /** Whether some mounted `ShinyOutput` is waiting on (and will log) it. */
  consumed: boolean;
}

const pendingBindAll = new WeakMap<HTMLElement, BindAllPass>();

/**
 * The same scopes as `pendingBindAll`, in something iterable.
 *
 * Keying by scope element dedupes calls for the SAME element, which leaves
 * NESTED scopes overlapping: one `ShinyOutput` inside a card body and
 * another inside a `div` nested in that same card body pass two different
 * parents, so both scans run and both walk the inner element.
 * `bindOutputs()` checks `.shiny-bound-output` before its own `await` and
 * adds the class only after it, so both get past that check and register
 * the element, which Shiny reports as a duplicate id. Spotting those
 * overlaps needs the in-flight scopes to be walkable, and a WeakMap is not.
 *
 * This is a strong reference where the map's is weak, so be honest about
 * what that costs: an entry is deleted when its pass settles, which is
 * every real case, but for as long as a scan is in flight this pins its
 * scope element even if React has already dropped it, and a `bindAll` that
 * somehow never settled would pin it for good. The map alone never could.
 * That is judged acceptable because the window is one bind pass and the
 * entry count is the number of concurrently scanning scopes, not the number
 * of outputs. If a hung `bindAll` ever turns out to be reachable, this
 * needs a different structure, not a bigger comment.
 */
const inFlightScopes = new Set<HTMLElement>();

function track(
  scope: HTMLElement,
  promise: Promise<unknown>,
  covers: WeakSet<Element> | null,
): BindAllPass {
  const pass: BindAllPass = {
    promise: promise.finally(() => {
      if (pendingBindAll.get(scope) === pass) {
        pendingBindAll.delete(scope);
        inFlightScopes.delete(scope);
      }
    }),
    covers,
    consumed: false,
  };
  pendingBindAll.set(scope, pass);
  inFlightScopes.add(scope);
  return pass;
}

/**
 * In-flight passes whose scope contains, or is contained by, `scope`: the
 * scans that can reach the same elements this one would. An identical scope
 * is not counted, since the map lookup already handles that case, and can
 * share the running pass outright rather than queue behind it.
 */
function overlappingPasses(scope: HTMLElement): BindAllPass[] {
  const found: BindAllPass[] = [];
  for (const other of inFlightScopes) {
    if (other === scope) continue;
    if (!other.contains(scope) && !scope.contains(other)) continue;
    const pass = pendingBindAll.get(other);
    if (pass) found.push(pass);
  }
  return found;
}

function runBindAll(scope: HTMLElement): Promise<unknown> {
  // Re-read rather than reusing the mount-time reference: a queued pass runs
  // later, and Shiny may be gone by then.
  const bindAll = window.Shiny?.bindAll;
  if (!bindAll) return Promise.resolve();
  // Every ShinyOutput passes its own parent as scope, so the elements this
  // call can bind are among scope's children as they are right now.
  const covers = new WeakSet<Element>(Array.from(scope.children));
  // A synchronous throw here propagates before anything is stored, so a
  // failing call is never shared.
  return track(scope, Promise.resolve(bindAll(scope)), covers).promise;
}

function queueBindAll(
  scope: HTMLElement,
  after: Promise<unknown>,
): BindAllPass {
  // Queue behind the in-flight call rather than deleting it: deleting would
  // let whichever ShinyOutput asks next start a second, overlapping scan
  // while this one is still running.
  const pass = track(
    scope,
    after.catch(() => {}).then(() => runBindAll(scope)),
    null,
  );
  pass.promise.catch((err) => {
    // Queued passes are fire-and-forget, so an unmount-triggered one can
    // fail with nothing mounted to report it — and its rejection must be
    // handled here either way, or it surfaces as an unhandled rejection.
    if (!pass.consumed) {
      console.error("[shinyreact] ShinyOutput bindAll failed:", err);
    }
  });
  return pass;
}

function dedupedBindAll(el: HTMLElement, scope: HTMLElement): Promise<unknown> {
  const pending = pendingBindAll.get(scope);
  if (!pending) {
    // No scan for this exact scope, but a nested one (an ancestor's or a
    // descendant's) can still be walking these same elements. Wait for all
    // of them rather than just the first: queueing behind one still leaves
    // this scan overlapping the others.
    const overlapping = overlappingPasses(scope);
    if (overlapping.length === 0) return runBindAll(scope);
    const pass = queueBindAll(
      scope,
      Promise.allSettled(overlapping.map((p) => p.promise)),
    );
    pass.consumed = true;
    return pass.promise;
  }
  // Only share a running pass that scanned `el`. One that started before
  // `el` mounted binds it never, and reports nothing about it — a silent
  // unbound output, the failure mode this dedupe must not introduce.
  const pass =
    !pending.covers || pending.covers.has(el)
      ? pending
      : queueBindAll(scope, pending.promise);
  pass.consumed = true;
  return pass.promise;
}

function refreshBindAll(scope: HTMLElement): void {
  const pending = pendingBindAll.get(scope);
  if (!pending) return;
  queueBindAll(scope, pending.promise);
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
 *     Once a call has settled this is safe to repeat: Shiny skips elements
 *     already marked `.shiny-bound-output` / `.shiny-bound-input`, so
 *     re-binding the parent does not re-bind sibling outputs. Calls that
 *     would overlap are coalesced by `dedupedBindAll` above (#298).
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
      dedupedBindAll(el, scope).catch((err) => logError(err, "bindAll"));
    } catch (err) {
      logError(err, "bindAll");
    }

    return () => {
      refreshBindAll(scope);
      try {
        window.Shiny?.unbindAll?.(el, true);
      } catch (err) {
        logError(err, "unbindAll");
      }
    };
  }, [namespacedId, tagName]);

  return React.createElement(tagName, { id: namespacedId, ref, ...rest });
}
