/**
 * Type contract for the shinyreact host API.
 *
 * The host page injects `window.shinyreact` at runtime. This bundle externalizes
 * the `"shinyreact"` module specifier to that global (see vite.config.js), so
 * `import { useShinyInput } from "shinyreact"` compiles to a property access on
 * `window.shinyreact`. These declarations give component authors editor types
 * for that contract.
 *
 * Long-term, these declarations should be owned and shipped by the core
 * shinyreact package (which is fully TypeScript) rather than re-declared in each
 * downstream framework. This local copy is the interim contract.
 */
declare module "shinyreact" {
  /** Options accepted by the input-writing hooks. */
  export interface ShinyInputOptions {
    /** Debounce delay in ms before the value is sent. Use 0 for events. */
    debounceMs?: number;
    /** Mark as an event input ("event") vs. a value input (default). */
    priority?: "event" | "immediate" | "deferred";
    /** Append `:type` to the wire id to opt into a server input handler. */
    type?: string;
  }

  /** Status of a Shiny output channel. */
  export type ShinyOutputStatus =
    | "pending"
    | "ready"
    | "recalculating"
    | "error";

  /** Full input hook: read + write a Shiny input value. */
  export function useShinyInput<T>(
    id: string,
    defaultValue: T,
    options?: ShinyInputOptions,
  ): [T, (value: T) => void];

  /** Read-only: subscribe to a Shiny input value. `undefined` until it registers. */
  export function useShinyInputValue<T>(id: string): T | undefined;

  /** Write-only: get a setter for a Shiny input. `defaultValue` seeds the registry on mount. */
  export function useSetShinyInput<T>(
    id: string,
    defaultValue: T,
    options?: ShinyInputOptions,
  ): (value: T) => void;

  /** Read-only: subscribe to a Shiny output value. `undefined` before a producer registers. */
  export function useShinyOutputValue<T>(
    id: string,
    defaultValue?: T,
  ): T | undefined;

  /** Read-only: subscribe to a Shiny output's status. */
  export function useShinyOutputStatus(id: string): ShinyOutputStatus;

  /** Register a handler for a server-pushed custom message. */
  export function useShinyMessageHandler(
    type: string,
    handler: (data: unknown) => void,
  ): void;

  /** True once the Shiny session has finished initializing. */
  export function useShinyInitialized(): boolean;

  /** True while Shiny is busy recomputing. */
  export function useShinyBusy(): boolean;
}
