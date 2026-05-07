/* eslint-disable @typescript-eslint/no-explicit-any */

import { type EventPriority } from "@posit/shiny/srcts/types/src/inputPolicies";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { getShiny } from "./get-shiny";
import { type InputRegistryEntry } from "./input-registry";
import {
  getBusySnapshot,
  getInitializedSnapshot,
  subscribeLifecycle,
} from "./lifecycle-store";
import { initializeMessageRegistry } from "./message-registry";
import { createReactOutputBinding } from "./output-registry";
import { getReactRegistry, initializeReactRegistry } from "./react-registry";
import {
  applyNamespace,
  useShinyModuleNamespace,
} from "./ShinyModuleContext";

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
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
  } = {},
): [T, (value: T) => void] {
  ensureShinyReactInitialized();

  // Apply namespace: explicit option wins over context. Pass `false` to opt out.
  const contextNamespace = useShinyModuleNamespace();
  const namespace =
    explicitNamespace !== undefined ? explicitNamespace : contextNamespace;
  const namespacedId = applyNamespace(id, namespace);

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
  }, [namespacedId, shinyInitialized, debounceMs, priority, stableDefault]);

  const setValueWrapped = useCallback(
    (value: T) => {
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

/**
 * Hook to receive and subscribe to Shiny output values from the server. Creates
 * a hidden DOM element and registers a custom Shiny output binding to receive
 * reactive data updates for the specified outputId.
 *
 * @param outputId The ID of the Shiny output to subscribe to.
 * @param defaultValue Optional default value to use before the first server
 * update.
 * @returns A tuple containing [value, recalculating] where:
 *   - value: The current value of the Shiny output
 *   - recalculating: Boolean indicating if the server is currently
 *     recalculating this output
 */
export function useShinyOutput<T>(
  outputId: string,
  defaultValue: T | undefined = undefined,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string | null;
  } = {},
): [T | undefined, boolean] {
  const [value, setValue] = useState<T | undefined>(defaultValue);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const shinyInitialized = useShinyInitialized();

  ensureShinyReactInitialized();

  // Apply namespace: explicit option wins over context. Pass `false` to opt out.
  const contextNamespace = useShinyModuleNamespace();
  const namespace =
    explicitNamespace !== undefined ? explicitNamespace : contextNamespace;
  const namespacedOutputId = applyNamespace(outputId, namespace);

  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }

    const reactRegistry = getReactRegistry();
    const dispose = reactRegistry.outputs.add(
      namespacedOutputId,
      setValue,
      setRecalculating,
    );
    return dispose;
  }, [namespacedOutputId, shinyInitialized]);

  return [value, recalculating];
}

// TODO: Also get error value?

// Note: useShinyOutputValue and useShinyOutputRecalculating are already supported
// via destructuring: `let [value, recalculating] = useShinyOutput(outputId, defaultValue)`

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

  // Apply namespace: explicit option wins over context. Pass `false` to opt out.
  const contextNamespace = useShinyModuleNamespace();
  const namespace =
    explicitNamespace !== undefined ? explicitNamespace : contextNamespace;
  const namespacedMessageType = applyNamespace(messageType, namespace);

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
  createReactOutputBinding();
  initializeMessageRegistry();

  shinyReactInitialized = true;
}
