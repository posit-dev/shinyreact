/**
 * Shared external store for Shiny RUNTIME-GLOBAL lifecycle state
 * (`initialized`, `busy`, `connected`).
 *
 * Why this exists: `initialized`, `busy` and `connected` are properties of the surrounding
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
import { onShinyEvent } from "./shiny-events";

let initialized = false;
let busy = false;
let connected = false;

const listeners = new Set<() => void>();
let started = false;

// Kept so `__resetLifecycleStoreForTests` can detach the event listeners
// cleanly between tests. In production they are never removed.
let stopListening: (() => void)[] = [];

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

function setConnected(next: boolean): void {
  if (connected === next) return;
  connected = next;
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
  // Seed `connected` the same way, for a consumer mounting after the socket
  // opened. `shinyapp` is absent before Shiny initializes; `false` is right.
  const shiny = getShiny();
  connected = shiny?.shinyapp?.isConnected() ?? false;

  // Shiny fires these through jQuery; `onShinyEvent` explains why that
  // matters. `shiny:connected` fires again after every reconnect.
  stopListening = [
    onShinyEvent("shiny:busy", () => setBusy(true)),
    onShinyEvent("shiny:idle", () => setBusy(false)),
    onShinyEvent("shiny:connected", () => setConnected(true)),
    onShinyEvent("shiny:disconnected", () => setConnected(false)),
  ];

  if (shiny) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    shiny.initializedPromise.then(markInitialized);
    return;
  }

  // Shiny loads after the React tree mounted: wait for it to connect. One
  // shot — the first `shiny:connected` either finds `window.Shiny` or never
  // will, which is the "stays false" case FEATURES.md pins.
  const stopWaiting = onShinyEvent("shiny:connected", () => {
    stopWaiting();
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    getShiny()?.initializedPromise.then(markInitialized);
  });
  stopListening.push(stopWaiting);
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

export function getConnectedSnapshot(): boolean {
  return connected;
}

/**
 * Test-only: reset module-level state and detach DOM listeners installed
 * by `start()`. Intentionally not re-exported from `index.ts`.
 */
export function __resetLifecycleStoreForTests(): void {
  stopListening.forEach((stop) => stop());
  stopListening = [];
  initialized = false;
  busy = false;
  connected = false;
  listeners.clear();
  started = false;
}
