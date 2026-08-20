/**
 * Shared external store for Shiny RUNTIME-GLOBAL lifecycle state
 * (`initialized`, `busy`).
 *
 * Why this exists: `initialized` and `busy` are properties of the surrounding
 * Shiny runtime, not of any one React component. A single subscription per
 * page avoids N duplicate DOM listeners and N redundant state writes per
 * `shiny:busy` / `shiny:idle` tick when many components use Shiny hooks.
 *
 * Scope: this pattern is ONLY appropriate for hooks that derive a single
 * page-global value from runtime events. Per-id hooks
 * (`useShinyInput`, `useShinyOutput`, `useShinyMessageHandler`) already share
 * state through their own id-keyed registries (input-registry,
 * output-registry, message-registry) and must not be folded into this store.
 *
 * Lifecycle: subscriptions to the underlying DOM events are installed lazily
 * the first time a consumer subscribes, and intentionally never torn down —
 * they belong to the page, not to any one React tree. This sidesteps races
 * around mount/unmount and avoids re-subscribe churn under StrictMode.
 */

import { getShiny } from "./get-shiny";

let initialized = false;
let busy = false;

const listeners = new Set<() => void>();
let started = false;

// Handler refs are kept so `__resetLifecycleStoreForTests` can detach them
// cleanly between tests. In production these never get removed.
let onBusyEvent: (() => void) | undefined;
let onIdleEvent: (() => void) | undefined;
let onConnectedEvent: (() => void) | undefined;

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

function markInitialized(): void {
  if (initialized) return;
  initialized = true;
  emit();
}

function setBusy(next: boolean): void {
  if (busy === next) return;
  busy = next;
  emit();
}

function start(): void {
  if (started) return;

  // Defer setting `started` until we have confirmed a DOM is available.
  // Otherwise a non-DOM render in the same runtime (e.g. react-test-renderer)
  // would latch the flag and prevent a later DOM-available render from ever
  // installing listeners.
  if (typeof document === "undefined") {
    return;
  }
  started = true;

  // Seed `busy` from the DOM. Shiny toggles `.shiny-busy` on <html> while a
  // request is in flight; if the first consumer mounts mid-request we want
  // the current state, not a stale `false`.
  if (document.documentElement.classList.contains("shiny-busy")) {
    busy = true;
  }
  onBusyEvent = () => setBusy(true);
  onIdleEvent = () => setBusy(false);
  document.addEventListener("shiny:busy", onBusyEvent);
  document.addEventListener("shiny:idle", onIdleEvent);

  const shiny = getShiny();
  if (shiny) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    shiny.initializedPromise.then(markInitialized);
    return;
  }

  onConnectedEvent = () => {
    const s = getShiny();
    if (s) {
      // eslint-disable-next-line @typescript-eslint/no-floating-promises
      s.initializedPromise.then(markInitialized);
    }
  };
  document.addEventListener("shiny:connected", onConnectedEvent, {
    once: true,
  });
}

export function subscribeLifecycle(listener: () => void): () => void {
  start();
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getInitializedSnapshot(): boolean {
  return initialized;
}

export function getBusySnapshot(): boolean {
  return busy;
}

/**
 * Test-only: reset module-level state and detach DOM listeners installed
 * by `start()`. Intentionally not re-exported from `index.ts`.
 */
export function __resetLifecycleStoreForTests(): void {
  if (typeof document !== "undefined") {
    if (onBusyEvent) {
      document.removeEventListener("shiny:busy", onBusyEvent);
    }
    if (onIdleEvent) {
      document.removeEventListener("shiny:idle", onIdleEvent);
    }
    if (onConnectedEvent) {
      // No-op if `shiny:connected` already fired (registered with `once: true`).
      document.removeEventListener("shiny:connected", onConnectedEvent);
    }
  }
  onBusyEvent = undefined;
  onIdleEvent = undefined;
  onConnectedEvent = undefined;
  initialized = false;
  busy = false;
  listeners.clear();
  started = false;
}
