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
 * The fix: track one call per scope element, and never let a second one
 * start while it is still in flight. A `ShinyOutput` sibling whose effect
 * runs in the same commit as another one's call for the same element
 * reuses that same call — but only if that call's scan covers it. One that
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

function track(
  scope: HTMLElement,
  promise: Promise<unknown>,
  covers: WeakSet<Element> | null,
): BindAllPass {
  const pass: BindAllPass = {
    promise: promise.finally(() => {
      if (pendingBindAll.get(scope) === pass) {
        pendingBindAll.delete(scope);
      }
    }),
    covers,
    consumed: false,
  };
  pendingBindAll.set(scope, pass);
  return pass;
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

function queueBindAll(scope: HTMLElement, pending: BindAllPass): BindAllPass {
  // Queue behind the in-flight call rather than deleting it: deleting would
  // let whichever ShinyOutput asks next start a second, overlapping scan
  // while this one is still running.
  const pass = track(
    scope,
    pending.promise.catch(() => {}).then(() => runBindAll(scope)),
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
  if (!pending) return runBindAll(scope);
  // Only share a running pass that scanned `el`. One that started before
  // `el` mounted binds it never, and reports nothing about it — a silent
  // unbound output, the failure mode this dedupe must not introduce.
  const pass =
    !pending.covers || pending.covers.has(el)
      ? pending
      : queueBindAll(scope, pending);
  pass.consumed = true;
  return pass.promise;
}

function refreshBindAll(scope: HTMLElement): void {
  const pending = pendingBindAll.get(scope);
  if (!pending) return;
  queueBindAll(scope, pending);
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
