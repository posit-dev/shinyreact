/* eslint-disable @typescript-eslint/no-explicit-any */
import { type EventPriority } from "@posit/shiny/srcts/types/src/inputPolicies";
import { getShiny } from "./get-shiny";
import { MISSING } from "./missing";
import { createDebouncedFn, type DebouncedFunction } from "./utils";

export class InputRegistryEntry<T> {
  /** Wire-id suffix applied when no explicit `type` is set, so untyped inputs
   * route through shinyreact's server-side handler (clean records on R). */
  private static readonly DEFAULT_TYPE = "shinyreact.default";

  id: string; // Shiny input ID
  value: T;
  useStateSetValueFns: Set<(value: T) => void>;
  shinySetInputValueDebounced: DebouncedFunction<(value: T) => void>;
  opts: { priority?: EventPriority; debounceMs: number } = {
    debounceMs: 100,
  };
  // Input-handler type suffix. Set once via updateType(); subsequent
  // mismatches throw. `undefined` is a valid finalized state ("no suffix").
  private type?: string;
  private typeFinalized = false;

  constructor(id: string, value: T) {
    this.id = id;
    this.value = value;
    this.useStateSetValueFns = new Set();
    this.shinySetInputValueDebounced = createDebouncedFn(
      this.setShinyInputValue.bind(this),
      this.opts.debounceMs,
    );
  }

  isEmpty() {
    return this.useStateSetValueFns.size === 0;
  }

  private setShinyInputValue(value: T) {
    const wireId = `${this.id}:${this.type ?? InputRegistryEntry.DEFAULT_TYPE}`;
    getShiny()?.setInputValue?.(wireId, value, this.opts);
  }

  updateDebounceDelay(debounceMs: number) {
    this.shinySetInputValueDebounced.setDelay(debounceMs);
  }

  updatePriority(priority: EventPriority) {
    // Last-writer-wins, deliberately: unlike `type`, priority changes *when*
    // Shiny recalculates, not what the value means, so a disagreement costs a
    // coalesced update rather than a wrong result. Throwing would break the
    // documented action-button pattern, where a reader mounts
    // useShinyInput("count", 0) and a button mounts useSetShinyInput("count",
    // 0, { priority: "event" }) for the same id.
    //
    // But silent last-writer-wins is miserable to debug when two mounts fight
    // over one id, so say something when the value actually changes.
    const previous = this.opts.priority;
    if (previous !== undefined && previous !== priority) {
      console.warn(
        `[shinyreact] Input "${this.id}" priority changed from ` +
          `${JSON.stringify(previous)} to ${JSON.stringify(priority)}. ` +
          `Priority is per-id here, so the most recent mount wins — if two ` +
          `call sites for this id disagree, the winner depends on mount order.`,
      );
    }
    this.opts.priority = priority;
  }

  updateType(type: string | undefined): void {
    if (!this.typeFinalized) {
      this.type = type;
      this.typeFinalized = true;
      return;
    }
    if (type === undefined) return;
    if (this.type !== type) {
      throw new Error(
        `Input "${this.id}" is already registered with type=${
          this.type === undefined
            ? `undefined (wire id "${this.id}:${InputRegistryEntry.DEFAULT_TYPE}")`
            : JSON.stringify(this.type)
        }. ` +
          `A second mount requested type=${JSON.stringify(type)}. ` +
          `An input's handler type changes server-side semantics and must be consistent ` +
          `across every useShinyInput / useSetShinyInput call for the same id.`,
      );
    }
  }

  addUseStateSetValueFn(fn: (value: T) => void) {
    this.useStateSetValueFns.add(fn);
  }

  removeUseStateSetValueFn(fn: (value: T) => void) {
    this.useStateSetValueFns.delete(fn);
  }

  setValue(value: T | ((prev: T) => T)) {
    // Support React-style functional updaters: setValue(prev => next). The
    // setter forwards its argument verbatim to Shiny.setInputValue, so a raw
    // function would be dropped during JSON serialization; resolve it against
    // the current value here instead. (Shiny input values are JSON data, never
    // functions, so a function argument unambiguously means "updater" — same
    // caveat as React's useState.)
    const next =
      typeof value === "function"
        ? (value as (prev: T) => T)(this.value)
        : value;
    this.value = next;
    this.useStateSetValueFns.forEach((fn) => fn(next));
    if ((next as unknown) === MISSING) {
      // MISSING means "not yet set" — update React state only, don't send to
      // Shiny. This keeps the server-side input in its MISSING state (raises
      // SilentException).
      //
      // Cancel any pending debounced send as well: without this, "real value
      // then MISSING" inside the debounce window still delivered the real value
      // ~debounceMs later, so the server held a value the client had already
      // retracted. ImageOutput hits this whenever an element is measured and
      // then hidden — the server would render a plot for dimensions that no
      // longer apply.
      this.shinySetInputValueDebounced.cancel();
      return;
    }
    this.shinySetInputValueDebounced(next);
  }

  getValue(): T {
    return this.value;
  }
}

export class InputRegistry {
  private inputs: Map<string, InputRegistryEntry<any>> = new Map();
  private pendingSubscribers: Map<string, Set<(value: any) => void>> = new Map();

  /**
   * Get an input registry entry by ID
   */
  get<T>(inputId: string): InputRegistryEntry<T> | undefined {
    return this.inputs.get(inputId) as InputRegistryEntry<T> | undefined;
  }

  /**
   * Check if an input registry entry exists
   */
  has(inputId: string): boolean {
    return this.inputs.has(inputId);
  }

  /**
   * Add a new input registry entry
   */
  add<T>(inputId: string, value: T): InputRegistryEntry<T> {
    if (this.inputs.has(inputId)) {
      throw new Error(`Input ${inputId} already exists`);
    }

    const entry = new InputRegistryEntry<T>(inputId, value);
    this.inputs.set(inputId, entry);

    // Drain any consumers that subscribed before the producer mounted.
    const pending = this.pendingSubscribers.get(inputId);
    if (pending) {
      pending.forEach((fn) => {
        entry.addUseStateSetValueFn(fn);
        fn(entry.getValue());
      });
      this.pendingSubscribers.delete(inputId);
    }

    return entry;
  }

  /**
   * Get or create an input registry entry
   *
   * Note that value is used only if the entry is created; if it already exists,
   * then the existing entry is returned and the value is unused.
   */
  getOrCreate<T>(inputId: string, value: T): InputRegistryEntry<T> {
    let entry = this.get<T>(inputId);
    if (!entry) {
      entry = this.add<T>(inputId, value);
    }
    return entry;
  }

  /**
   * Read-only subscription to an input value.
   *
   * If the entry already exists, attaches the subscriber and immediately
   * calls it with the current value (parity with `useState` initial mount
   * semantics). If the entry does not yet exist (consumer mounted before
   * producer), the subscriber is queued and attached when `add()` later
   * creates the entry.
   *
   * @returns A dispose function that detaches the subscriber, whether or
   * not the entry currently exists.
   */
  subscribe<T>(inputId: string, setFn: (value: T) => void): () => void {
    const entry = this.get<T>(inputId);
    if (entry) {
      entry.addUseStateSetValueFn(setFn);
      setFn(entry.getValue());
      return () => {
        const e = this.get<T>(inputId);
        if (e) {
          e.removeUseStateSetValueFn(setFn);
        }
      };
    }

    let pending = this.pendingSubscribers.get(inputId);
    if (!pending) {
      pending = new Set();
      this.pendingSubscribers.set(inputId, pending);
    }
    pending.add(setFn as (v: any) => void);

    return () => {
      // Detach from whichever bucket holds us now.
      const e = this.get<T>(inputId);
      if (e) {
        e.removeUseStateSetValueFn(setFn);
        return;
      }
      const p = this.pendingSubscribers.get(inputId);
      if (p) {
        p.delete(setFn as (v: any) => void);
        if (p.size === 0) {
          this.pendingSubscribers.delete(inputId);
        }
      }
    };
  }

  /**
   * Remove an input registry entry
   */
  remove(inputId: string): boolean {
    const entry = this.inputs.get(inputId);
    if (entry) {
      entry.shinySetInputValueDebounced.cancel();
    }
    return this.inputs.delete(inputId);
  }

  /**
   * Get all input IDs
   */
  keys(): IterableIterator<string> {
    return this.inputs.keys();
  }

  /**
   * Get the number of registered inputs
   */
  size(): number {
    return this.inputs.size;
  }
}
