import React from "react";
import * as ReactDOM from "react-dom/client";
import { ShinyOutput } from "./shiny-output";

// Re-export @posit/shiny-react hooks and components.
//
// We bundle @posit/shiny-react and React into this single IIFE so that:
// 1. All code shares a single React instance (React hooks break with multiple Reacts)
// 2. Downstream component authors get hooks via window.shinyreact.*
// 3. Downstream ESM builds can externalize React to window.shinyreact.React/ReactDOM
import {
  useSetShinyInput,
  useShinyBusy,
  useShinyInput,
  useShinyInputValue,
  useShinyOutputError,
  useShinyOutputStatus,
  useShinyOutputValue,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
} from "./shiny-react";

// Extend window with shinyreact's public global API
declare global {
  interface Window {
    shinyreact: {
      useSetShinyInput: typeof useSetShinyInput;
      useShinyBusy: typeof useShinyBusy;
      useShinyInput: typeof useShinyInput;
      useShinyInputValue: typeof useShinyInputValue;
      useShinyOutputError: typeof useShinyOutputError;
      useShinyOutputStatus: typeof useShinyOutputStatus;
      useShinyOutputValue: typeof useShinyOutputValue;
      useShinyMessageHandler: typeof useShinyMessageHandler;
      useShinyInitialized: typeof useShinyInitialized;
      ImageOutput: typeof ImageOutput;
      MISSING: typeof MISSING;
      ShinyModuleProvider: typeof ShinyModuleProvider;
      ShinyReactComponentElement: typeof ShinyReactComponentElement;
      ShinyOutput: typeof ShinyOutput;
      React: typeof React;
      ReactDOM: typeof ReactDOM;
    };
  }
}

/**
 * Expose the public global API at `window.shinyreact`. Called once at bundle
 * boot. Nothing writes the namespace before the bundle runs — server state
 * arrives via the `#shinyreact-config` JSON script tag, not the global — so
 * this is a plain assignment.
 */
export function installGlobal(): void {
  window.shinyreact = {
    useSetShinyInput,
    useShinyBusy,
    useShinyInput,
    useShinyInputValue,
    useShinyOutputError,
    useShinyOutputStatus,
    useShinyOutputValue,
    useShinyMessageHandler,
    useShinyInitialized,
    ImageOutput,
    MISSING,
    ShinyModuleProvider,
    ShinyReactComponentElement,
    ShinyOutput,
    React,
    ReactDOM,
  };
}
