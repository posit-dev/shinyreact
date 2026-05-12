import type { ComponentType, ReactNode } from "react";

// Mirrors shinyreact's RegisteredComponentProps and ComponentRegistry from
// js/src/spec.ts. Kept local to avoid cross-project relative imports.

export interface Element {
  type: string;
  props: Record<string, unknown>;
  children?: string[];
}

export interface RegisteredComponentProps {
  element: Element;
  children: ReactNode;
}

export type ComponentRegistry = Record<
  string,
  ComponentType<RegisteredComponentProps>
>;

declare global {
  interface Window {
    shinyreact: {
      registerComponents: (
        catalog: unknown,
        registry: ComponentRegistry,
      ) => void;
      // priority values match Shiny's input event priorities used by
      // @posit/shiny-react. Stable strings in the wire protocol.
      useShinyInput: <T>(
        id: string,
        defaultValue: T,
        options?: { debounceMs?: number; priority?: "immediate" | "deferred" | "event" },
      ) => [T, (value: T) => void];
      useShinyOutputValue: <T>(id: string, defaultValue?: T) => T;
      // Other hooks exist (useSetShinyInput, useShinyMessageHandler, ...) but
      // are not used by the scaffold; add them as needed.
      React: typeof import("react");
      ReactDOM: unknown;
    };
  }
}

export {};
