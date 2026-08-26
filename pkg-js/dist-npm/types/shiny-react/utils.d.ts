/**
 * Type definition for a debounced function with dynamic delay capabilities
 */
export type DebouncedFunction<T extends (...args: any[]) => any> = {
    (...args: Parameters<T>): void;
    setDelay: (newDelay: number) => void;
    getDelay: () => number;
    cancel: () => void;
};
/**
 * Creates a debounced function with dynamic delay that can be changed at runtime.
 *
 * @param func The function to debounce
 * @param delay The initial number of milliseconds to delay
 * @returns A debounced function with setDelay, getDelay, and cancel methods attached
 */
export declare function createDebouncedFn<T extends (...args: any[]) => any>(func: T, delay: number): DebouncedFunction<T>;
