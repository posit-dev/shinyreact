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
export declare function subscribeLifecycle(listener: () => void): () => void;
export declare function getInitializedSnapshot(): boolean;
export declare function getBusySnapshot(): boolean;
/**
 * Test-only: reset module-level state and detach DOM listeners installed
 * by `start()`. Intentionally not re-exported from `index.ts`.
 */
export declare function __resetLifecycleStoreForTests(): void;
