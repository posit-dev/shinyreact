export type ErrorsMessageValue = {
    message: string;
    call: string[];
    type?: string[];
};
export type OutputStatus = "pending" | "ready" | "recalculating" | "error";
export declare class OutputRegistryEntry<T> {
    id: string;
    private status;
    private hasValue;
    private lastValue;
    private lastError;
    private useStateSetValueFns;
    private useStateSetStatusFns;
    private useStateSetErrorFns;
    constructor(id: string);
    hasReceivedValue(): boolean;
    getLastValue(): T | undefined;
    getLastError(): ErrorsMessageValue | null;
    addUseStateSetValueFn(fn: (value: T) => void): void;
    removeUseStateSetValueFn(fn: (value: T) => void): void;
    addUseStateSetStatusFn(fn: (status: OutputStatus) => void): void;
    removeUseStateSetStatusFn(fn: (status: OutputStatus) => void): void;
    addUseStateSetErrorFn(fn: (err: ErrorsMessageValue | null) => void): void;
    removeUseStateSetErrorFn(fn: (err: ErrorsMessageValue | null) => void): void;
    getStatus(): OutputStatus;
    private setStatus;
    setValue(value: T): void;
    setRecalculating(recalculating: boolean): void;
    setError(err: ErrorsMessageValue): void;
    isEmpty(): boolean;
}
export declare class OutputRegistry {
    private outputs;
    private bindAllScheduled;
    private container;
    constructor();
    add<T>(outputId: string, setValue: (value: T) => void, setStatus: (status: OutputStatus) => void, setError: (err: ErrorsMessageValue | null) => void): () => void;
    has(outputId: string): boolean;
    get(outputId: string): OutputRegistryEntry<any> | undefined;
    private scheduleCleanup;
    /**
     * Schedules a Shiny binding operation to run after DOM updates are complete.
     *
     * Note: I'm not sure if this is 100% reliable. I believe we need to avoid
     * overlapping calls to bindAll(), and am not sure if requestAnimationFrame()
     * will provide perfect reliability for this.
     */
    private scheduleBindAll;
}
/**
 * Create and register the React output binding when Shiny is available
 */
export declare function createReactOutputBinding(): void;
