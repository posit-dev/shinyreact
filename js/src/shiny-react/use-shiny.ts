/* eslint-disable @typescript-eslint/no-explicit-any */

import { type EventPriority } from "@posit/shiny/srcts/types/src/inputPolicies";
import {
  type Dispatch,
  type SetStateAction,
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { applyRestoredValues } from "./bookmark";
import { getShiny } from "./get-shiny";
import { type InputRegistryEntry } from "./input-registry";
import {
  getBusySnapshot,
  getInitializedSnapshot,
  subscribeLifecycle,
} from "./lifecycle-store";
import { initializeMessageRegistry } from "./message-registry";
import { MISSING } from "./missing";
import {
  createReactOutputBinding,
  type OutputStatus,
} from "./output-registry";
import { getReactRegistry, initializeReactRegistry } from "./react-registry";
import { useNamespacedId } from "./ShinyModuleContext";

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
export function useShinyInput<T>(
  id: string,
  defaultValue: T,
  {
    debounceMs = 100,
    priority,
    namespace: explicitNamespace,
    type,
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
  } = {},
): [T, Dispatch<SetStateAction<T>>] {
  ensureShinyReactInitialized();

  if (type !== undefined && !/^[^\s:]+$/.test(type)) {
    throw new Error(
      `useShinyInput("${id}"): invalid type=${JSON.stringify(type)}. ` +
        `Must be non-empty and contain no whitespace or ':' characters.`,
    );
  }

  const namespacedId = useNamespacedId(id, explicitNamespace);

  // NOTE: It's a little odd that debounceMs and priority passed this way; the
  // debounceMs is associated with the specific input name, and in Shiny's API,
  // priority is associated with each individual call to setInputValue(). But
  // here they're both associated with the input name, and also if there are
  // multiple calls to useShinyInput("foo"), then the priority will be from the
  // most recent call. This all should be straightened out in the future.

  // Stabilize defaultValue across renders. Callers often pass inline literals
  // like `{}` or `[]` which create a new reference every render. Since
  // defaultValue is in the useEffect dependency array, an unstable reference
  // would cause the effect to re-run every render — and with priority:"event"
  // that creates an infinite render→send→update→render loop. Capturing the
  // first value in a ref makes this safe regardless of how it's called.
  const stableDefaultRef = useRef<T>(defaultValue);
  const stableDefault = stableDefaultRef.current;

  let startValue: T = stableDefault;
  const reactRegistry = getReactRegistry();
  const inputRegistryEntry = reactRegistry.inputs.get(
    namespacedId,
  ) as InputRegistryEntry<T>;

  if (inputRegistryEntry) {
    // If the input registry entry already exists, use its value as the start
    // value. We have to do this because if the input registry entry for this ID
    // was created in the past and there's some (non-default) value in it
    // already, then we don't want to override it with the default value passed
    // to this hook. This situation could happen when there are multiple calls to
    // useShinyInput("foo") in different places, or when the component that calls
    // useShinyInput("foo") is dynamically generated (and so React won't know that
    // the useState below is for the same input).
    startValue = inputRegistryEntry.getValue();
  }
  const [value, setValue] = useState<T>(startValue);
  const shinyInitialized = useShinyInitialized();

  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }

    // Make sure the input registry entry exists for this Shiny input ID
    const reactRegistry = getReactRegistry();
    const inputRegistryEntry = reactRegistry.inputs.getOrCreate<T>(
      namespacedId,
      stableDefault,
    );

    if (debounceMs !== undefined) {
      inputRegistryEntry.updateDebounceDelay(debounceMs);
    }
    if (priority) {
      inputRegistryEntry.updatePriority(priority);
    }
    inputRegistryEntry.updateType(type);

    inputRegistryEntry.addUseStateSetValueFn(setValue);
    // TODO: This is awkward. Maybe just add a trigger method?
    inputRegistryEntry.setValue(inputRegistryEntry.getValue());

    return () => {
      inputRegistryEntry.removeUseStateSetValueFn(setValue);

      // The registry entry will still exist even if it no longer has any
      // useStateSetValueFns. This preserves the value of the input when the
      // count drops to zero, which will happen on most re-renders as this
      // useEffect will be called again. If someone wants to really get rid of
      // the registry entry, they will have to do so manually.
    };
  }, [namespacedId, shinyInitialized, debounceMs, priority, stableDefault, type]);

  const setValueWrapped = useCallback(
    (value: SetStateAction<T>) => {
      if (!shinyInitialized) {
        return;
      }

      const reactRegistry = getReactRegistry();
      const inputRegistryEntry = reactRegistry.inputs.get(namespacedId);
      if (!inputRegistryEntry) {
        console.error(`Input ${namespacedId} not found`);
        return;
      }
      inputRegistryEntry.setValue(value);
    },
    [namespacedId, shinyInitialized],
  );

  return [value, setValueWrapped];
}

// A stable no-op for output-registry callbacks the hook doesn't care about.
// Passing this instead of a real `useState` setter keeps unused channels from
// triggering re-renders when the underlying entry's status/error changes.
const NOOP_SETTER = () => {};

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
export function useShinyOutputValue<T>(
  outputId: string,
  defaultValue: T | undefined = undefined,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string | null;
  } = {},
): T | undefined {
  const [value, setValue] = useState<T | undefined>(defaultValue);
  const shinyInitialized = useShinyInitialized();

  ensureShinyReactInitialized();

  const namespacedOutputId = useNamespacedId(outputId, explicitNamespace);

  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }
    const reactRegistry = getReactRegistry();
    const dispose = reactRegistry.outputs.add<T>(
      namespacedOutputId,
      setValue,
      NOOP_SETTER,
      NOOP_SETTER,
    );
    return dispose;
  }, [namespacedOutputId, shinyInitialized]);

  return value;
}

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
export function useShinyOutputStatus(
  outputId: string,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string | null;
  } = {},
): OutputStatus {
  const [status, setStatus] = useState<OutputStatus>("pending");
  const shinyInitialized = useShinyInitialized();

  ensureShinyReactInitialized();

  const namespacedOutputId = useNamespacedId(outputId, explicitNamespace);

  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }
    const reactRegistry = getReactRegistry();
    const dispose = reactRegistry.outputs.add<unknown>(
      namespacedOutputId,
      NOOP_SETTER,
      setStatus,
      NOOP_SETTER,
    );
    return dispose;
  }, [namespacedOutputId, shinyInitialized]);

  return status;
}

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
export function useShinyInputValue<T>(
  id: string,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string | null;
  } = {},
): T | undefined {
  ensureShinyReactInitialized();

  const namespacedId = useNamespacedId(id, explicitNamespace);

  const [value, setValue] = useState<T | undefined>(() => {
    const entry = getReactRegistry().inputs.get<T>(namespacedId);
    if (!entry) return undefined;
    const v = entry.getValue();
    return (v as unknown) === MISSING ? undefined : v;
  });
  const shinyInitialized = useShinyInitialized();

  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }
    const reactRegistry = getReactRegistry();
    const dispose = reactRegistry.inputs.subscribe<T>(namespacedId, (v) => {
      // Map MISSING sentinel to undefined for consumer ergonomics.
      setValue((v as unknown) === MISSING ? undefined : v);
    });
    return dispose;
  }, [namespacedId, shinyInitialized]);

  return value;
}

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
export function useSetShinyInput<T>(
  id: string,
  defaultValue: T,
  {
    debounceMs = 100,
    priority,
    namespace: explicitNamespace,
    type,
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
  } = {},
): Dispatch<SetStateAction<T>> {
  ensureShinyReactInitialized();

  if (type !== undefined && !/^[^\s:]+$/.test(type)) {
    throw new Error(
      `useSetShinyInput("${id}"): invalid type=${JSON.stringify(type)}. ` +
        `Must be non-empty and contain no whitespace or ':' characters.`,
    );
  }

  const namespacedId = useNamespacedId(id, explicitNamespace);

  // Stabilize defaultValue — same reasoning as useShinyInput.
  const stableDefaultRef = useRef<T>(defaultValue);
  const stableDefault = stableDefaultRef.current;

  const shinyInitialized = useShinyInitialized();

  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }
    const reactRegistry = getReactRegistry();
    const inputRegistryEntry = reactRegistry.inputs.getOrCreate<T>(
      namespacedId,
      stableDefault,
    );
    if (debounceMs !== undefined) {
      inputRegistryEntry.updateDebounceDelay(debounceMs);
    }
    if (priority) {
      inputRegistryEntry.updatePriority(priority);
    }
    inputRegistryEntry.updateType(type);
    // Re-broadcast the current value through the registry so Shiny sees the
    // input on first mount (matches useShinyInput's behavior).
    inputRegistryEntry.setValue(inputRegistryEntry.getValue());

    // Intentionally NO addUseStateSetValueFn — this is a write-only hook;
    // value updates from elsewhere (other producers, server-side updates)
    // must not re-render the component using this hook.
  }, [namespacedId, shinyInitialized, debounceMs, priority, stableDefault, type]);

  return useCallback(
    (value: SetStateAction<T>) => {
      if (!shinyInitialized) {
        return;
      }
      const reactRegistry = getReactRegistry();
      const inputRegistryEntry = reactRegistry.inputs.get(namespacedId);
      if (!inputRegistryEntry) {
        console.error(`Input ${namespacedId} not found`);
        return;
      }
      inputRegistryEntry.setValue(value);
    },
    [namespacedId, shinyInitialized],
  );
}

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
export function useShinyMessageHandler<T = any>(
  messageType: string,
  handler: (data: T) => void,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string | null;
  } = {},
): void {
  const shinyInitialized = useShinyInitialized();

  ensureShinyReactInitialized();

  const namespacedMessageType = useNamespacedId(messageType, explicitNamespace);

  // Stabilize handler reference: callers often pass inline arrow functions
  // which create a new reference every render, causing unnecessary
  // deregister/re-register cycles. Use a ref so the effect only re-runs
  // when the message type changes, not on every render.
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    if (!shinyInitialized || !namespacedMessageType) {
      return;
    }
    const shiny = getShiny();
    if (!shiny) {
      return;
    }

    // Wrap in a stable function that delegates to the latest handler ref
    const stableHandler = (data: T) => handlerRef.current(data);

    // Register the message handler with our dedicated message registry
    shiny.messageRegistry.addHandler(namespacedMessageType, stableHandler);

    // Cleanup function that removes the handler when component unmounts
    // or when messageType changes
    return () => {
      shiny.messageRegistry.removeHandler(namespacedMessageType, stableHandler);
    };
  }, [shinyInitialized, namespacedMessageType]);
}

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
export function useShinyInitialized(): boolean {
  return useSyncExternalStore(
    subscribeLifecycle,
    getInitializedSnapshot,
    getInitializedSnapshot,
  );
}

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
export function useShinyBusy(): boolean {
  return useSyncExternalStore(
    subscribeLifecycle,
    getBusySnapshot,
    getBusySnapshot,
  );
}

let shinyReactInitialized = false;
function ensureShinyReactInitialized() {
  if (shinyReactInitialized) {
    return;
  }

  initializeReactRegistry();
  // Adopt any bookmark-restored input values BEFORE the output binding
  // begins consuming server messages, so the registry already holds the
  // restored values by the first useShinyInput mount.
  applyRestoredValues(getReactRegistry().inputs);
  createReactOutputBinding();
  initializeMessageRegistry();

  shinyReactInitialized = true;
}

/**
 * Reset the shinyReactInitialized flag. FOR TESTING ONLY.
 * This allows tests to re-run initialization after clearing state.
 */
export function _resetShinyReactInitializedForTesting(): void {
  shinyReactInitialized = false;
}
