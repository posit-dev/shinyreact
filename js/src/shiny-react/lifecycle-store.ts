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
  started = true;

  if (typeof document === "undefined") {
    return;
  }

  // Seed `busy` from the DOM. Shiny toggles `.shiny-busy` on <html> while a
  // request is in flight; if the first consumer mounts mid-request we want
  // the current state, not a stale `false`.
  if (document.documentElement.classList.contains("shiny-busy")) {
    busy = true;
  }
  document.addEventListener("shiny:busy", () => setBusy(true));
  document.addEventListener("shiny:idle", () => setBusy(false));

  const shiny = getShiny();
  if (shiny) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    shiny.initializedPromise.then(markInitialized);
    return;
  }

  document.addEventListener(
    "shiny:connected",
    () => {
      const s = getShiny();
      if (s) {
        // eslint-disable-next-line @typescript-eslint/no-floating-promises
        s.initializedPromise.then(markInitialized);
      }
    },
    { once: true },
  );
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
 * Test-only: reset the module-level state so each test starts from a known
 * baseline. Intentionally not re-exported from `index.ts`.
 *
 * Note: we do not detach the DOM listeners installed by `start()`. They keep
 * pointing at `setBusy` / `markInitialized`, which read the (now-reset)
 * module variables, so behavior remains correct after reset.
 */
export function __resetLifecycleStoreForTests(): void {
  initialized = false;
  busy = false;
  listeners.clear();
  started = false;
}
