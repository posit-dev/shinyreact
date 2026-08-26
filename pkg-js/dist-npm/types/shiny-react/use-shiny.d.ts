import { type EventPriority } from "@posit/shiny/srcts/types/src/inputPolicies";
import { type Dispatch, type SetStateAction } from "react";
import { type OutputStatus } from "./output-registry";
/**
 * A React hook for managing a Shiny input value.
 *
 * This hook initializes a state variable with `defaultValue` and returns the
 * current value and a function to update it, similar to `React.useState`.
 *
 * When the component mounts, it waits for Shiny to initialize. Once Shiny is
 * initialized, this hook registers the input with the Shiny React registry and
 * uses debounced updates to send values to the Shiny server via
 * `window.Shiny.setInputValue()`.
 *
 * The hook supports debouncing to optimize performance by batching rapid
 * updates, and allows setting priority levels for input events.
 *
 * Note: This hook only sends data *to* Shiny. It does not automatically update
 * the React state if the input is changed on the server-side (e.g., using
 * `updateTextInput()`). For two-way binding, a custom Shiny input binding would
 * be required.
 *
 * @param id The ID that will be used for the Shiny input (`input$<id>`).
 * @param defaultValue The initial value for the input, used only on first
 * mount (same semantics as `React.useState`'s initial value). Subsequent
 * renders may pass a different value, but it will be ignored. This means
 * inline object/array literals like `{}` or `[]` are safe to pass — they
 * won't cause unnecessary re-renders.
 * @param options Optional configuration object.
 * @param options.debounceMs Debounce delay in milliseconds for input updates
 * (default: 100).
 * @param options.priority Priority level for the input event (from Shiny's
 * EventPriority enum).
 * @param options.type Optional input-handler name appended as `${id}:${type}`
 * when sending to Shiny. Use to route values through a Shiny input handler
 * such as `"shiny.datetime"`. Must be non-empty and contain no whitespace or
 * `:`. The first mount of a given id finalizes the policy (an explicit `type`
 * or the absence of one); a later mount that omits `type` is a no-op, but a
 * later mount that supplies a `type` disagreeing with the finalized policy
 * throws — the handler name is a server-side semantic and must be consistent
 * across every `useShinyInput` / `useSetShinyInput` call for the same id.
 * @returns A tuple containing the current value and a function to set the
 * value: `[value, setValue]`.
 */
export declare function useShinyInput<T>(id: string, defaultValue: T, { debounceMs, priority, namespace: explicitNamespace, type, }?: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
}): [T, Dispatch<SetStateAction<T>>];
/**
 * Hook to subscribe to a Shiny output value.
 *
 * Returns just the current value. Use this when you only need the data —
 * which is most call sites. If you also need the lifecycle status (to drive
 * a skeleton, spinner, or error UI), call `useShinyOutputStatus` alongside it.
 *
 * @param outputId The ID of the Shiny output to subscribe to.
 * @param defaultValue Optional value returned while the server has not yet
 * delivered the first response.
 * @param options Optional configuration object.
 * @param options.namespace Module namespace to apply (or `null` to suppress
 * the surrounding `ShinyModuleProvider` namespace).
 * @returns The current output value.
 */
export declare function useShinyOutputValue<T>(outputId: string, defaultValue?: T | undefined, { namespace: explicitNamespace, }?: {
    namespace?: string | null;
}): T | undefined;
/**
 * Hook to subscribe to the lifecycle status of a Shiny output.
 *
 * One of:
 * - `"pending"` — server has not yet sent a value (initial mount).
 * - `"ready"` — server has sent a value and is not currently recalculating.
 * - `"recalculating"` — server is recomputing this output. The value held by
 *   any sibling `useShinyOutputValue` is the previously delivered result.
 * - `"error"` — the server-side render raised an error.
 *
 * Use this when you need to drive skeleton / spinner / error UI. For just
 * the value, use `useShinyOutputValue`.
 *
 * @param outputId The ID of the Shiny output to subscribe to.
 * @param options Optional configuration object.
 * @param options.namespace Module namespace to apply (or `null` to suppress
 * the surrounding `ShinyModuleProvider` namespace).
 * @returns The current output status.
 */
export declare function useShinyOutputStatus(outputId: string, { namespace: explicitNamespace, }?: {
    namespace?: string | null;
}): OutputStatus;
/**
 * A read-only React hook that subscribes to a Shiny input value created by a
 * separate producer component (typically one that calls `useShinyInput` and
 * holds the setter).
 *
 * Use this when a component only needs to *read* an input value — it makes
 * data flow direction visible at the call site and prevents accidental writes
 * to inputs the component does not own.
 *
 * Mount ordering is handled: if this hook runs before the producer's
 * `useShinyInput` effect attaches, the subscription is queued in the input
 * registry and fires the moment the entry is created.
 *
 * @param id The Shiny input ID to subscribe to (`input$<id>`).
 * @param options Optional configuration object.
 * @param options.namespace Module namespace to apply (or `null` to suppress
 * the surrounding `ShinyModuleProvider` namespace).
 * @returns The current input value, or `undefined` if no producer has
 * registered the ID yet.
 */
export declare function useShinyInputValue<T>(id: string, { namespace: explicitNamespace, }?: {
    namespace?: string | null;
}): T | undefined;
/**
 * A write-only React hook that returns just the setter for a Shiny input.
 *
 * Use this when a component only needs to *write* an input value — typically
 * a button, action handler, or anything that pushes events into the reactive
 * graph but never reads the current value back. Mirrors Jotai's `useSetAtom`
 * pattern: explicit at the call site that this is a producer, not a reader,
 * and avoids the spurious re-renders that `useShinyInput` would incur from
 * subscribing to its own value updates.
 *
 * Same `defaultValue` and options semantics as `useShinyInput` — this hook
 * registers the input on mount, so its `defaultValue` seeds the registry the
 * same way.
 *
 * @param id The Shiny input ID (`input$<id>`).
 * @param defaultValue Initial value for the input, captured on first mount.
 * @param options Optional configuration object.
 * @param options.debounceMs Debounce delay in milliseconds for input updates
 * (default: 100).
 * @param options.priority Priority level for the input event.
 * @param options.namespace Module namespace to apply (or `null` to suppress
 * the surrounding `ShinyModuleProvider` namespace).
 * @param options.type Optional input-handler name appended as `${id}:${type}`
 * when sending to Shiny. Use to route values through a Shiny input handler
 * such as `"shiny.datetime"`. Must be non-empty and contain no whitespace or
 * `:`. The first mount of a given id finalizes the policy (an explicit `type`
 * or the absence of one); a later mount that omits `type` is a no-op, but a
 * later mount that supplies a `type` disagreeing with the finalized policy
 * throws — the handler name is a server-side semantic and must be consistent
 * across every `useShinyInput` / `useSetShinyInput` call for the same id.
 * @returns A function that writes the input value.
 */
export declare function useSetShinyInput<T>(id: string, defaultValue: T, { debounceMs, priority, namespace: explicitNamespace, type, }?: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
}): Dispatch<SetStateAction<T>>;
/**
 * A React hook for handling messages from the Shiny server.
 *
 * This hook registers a message handler with Shiny that will be called when the
 * server sends a message of the specified type using `post_message()` (which is
 * a wrapper for `session.send_custom_message()` with extra functionality.)
 *
 * The hook waits for Shiny to initialize before registering the handler and
 * properly manages the handler lifecycle, re-registering when dependencies
 * change.
 *
 * @param messageType The type/name of the custom message to listen for.
 * @param handler The function to call when a message of this type is received.
 * The handler receives the message data as its parameter. Inline arrow
 * functions are safe to pass — the handler is stored in a ref internally,
 * so a new function reference on each render won't cause the message
 * handler to be deregistered and re-registered.
 */
export declare function useShinyMessageHandler<T = any>(messageType: string, handler: (data: T) => void, { namespace: explicitNamespace, }?: {
    namespace?: string | null;
}): void;
/**
 * A React hook that tracks whether Shiny has been initialized.
 *
 * Reads from a shared lifecycle store (see `lifecycle-store.ts`) so all
 * consumers on the page share a single subscription to `window.Shiny`'s
 * `initializedPromise` / the `"shiny:connected"` DOM event, rather than each
 * mounting its own listener.
 *
 * @returns A boolean indicating whether Shiny has been initialized.
 */
export declare function useShinyInitialized(): boolean;
/**
 * A React hook that tracks whether the Shiny server is currently busy.
 *
 * Reads from a shared lifecycle store (see `lifecycle-store.ts`) so all
 * consumers on the page share a single pair of `shiny:busy` / `shiny:idle`
 * DOM listeners. Returns `false` initially, flips to `true` while a request
 * is in flight, and back to `false` when the server goes idle.
 *
 * @returns A boolean indicating whether the Shiny server is currently busy.
 */
export declare function useShinyBusy(): boolean;
/**
 * Reset the shinyReactInitialized flag. FOR TESTING ONLY.
 * This allows tests to re-run initialization after clearing state.
 */
export declare function _resetShinyReactInitializedForTesting(): void;
