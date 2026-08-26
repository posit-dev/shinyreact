import { type EventPriority } from "@posit/shiny/srcts/types/src/inputPolicies";
import { type DebouncedFunction } from "./utils";
export declare class InputRegistryEntry<T> {
    /** Wire-id suffix applied when no explicit `type` is set, so untyped inputs
     * route through shinyreact's server-side handler (clean records on R). */
    private static readonly DEFAULT_TYPE;
    id: string;
    value: T;
    useStateSetValueFns: Set<(value: T) => void>;
    shinySetInputValueDebounced: DebouncedFunction<(value: T) => void>;
    opts: {
        priority?: EventPriority;
        debounceMs: number;
    };
    private type?;
    private typeFinalized;
    constructor(id: string, value: T);
    isEmpty(): boolean;
    private setShinyInputValue;
    updateDebounceDelay(debounceMs: number): void;
    updatePriority(priority: EventPriority): void;
    updateType(type: string | undefined): void;
    addUseStateSetValueFn(fn: (value: T) => void): void;
    removeUseStateSetValueFn(fn: (value: T) => void): void;
    setValue(value: T | ((prev: T) => T)): void;
    getValue(): T;
}
export declare class InputRegistry {
    private inputs;
    private pendingSubscribers;
    /**
     * Get an input registry entry by ID
     */
    get<T>(inputId: string): InputRegistryEntry<T> | undefined;
    /**
     * Check if an input registry entry exists
     */
    has(inputId: string): boolean;
    /**
     * Add a new input registry entry
     */
    add<T>(inputId: string, value: T): InputRegistryEntry<T>;
    /**
     * Get or create an input registry entry
     *
     * Note that value is used only if the entry is created; if it already exists,
     * then the existing entry is returned and the value is unused.
     */
    getOrCreate<T>(inputId: string, value: T): InputRegistryEntry<T>;
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
    subscribe<T>(inputId: string, setFn: (value: T) => void): () => void;
    /**
     * Remove an input registry entry
     */
    remove(inputId: string): boolean;
    /**
     * Get all input IDs
     */
    keys(): IterableIterator<string>;
    /**
     * Get the number of registered inputs
     */
    size(): number;
}
