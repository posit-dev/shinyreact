/**
 * Sentinel value representing a "not yet set" state for Shiny inputs.
 *
 * Mirrors Shiny Python's `MISSING` type. When a `useShinyInput` value is
 * `MISSING`, the value is held in React state but is **not** sent to the
 * server via `Shiny.setInputValue()`. This keeps the server-side reactive
 * input in its initial `MISSING` state, which raises `SilentException`
 * when read — the standard Shiny mechanism for "wait until a real value
 * arrives."
 *
 * Typical use: `ImageOutput` dimension inputs that should not fire
 * `renderImage()` until the element has been measured by `ResizeObserver`.
 */
export declare const MISSING: unique symbol;
export type MISSING = typeof MISSING;
