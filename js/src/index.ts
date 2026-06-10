import React from "react";
import * as ReactDOM from "react-dom/client";
import type { ComponentRegistry } from "./types";
import { registerComponents } from "./registry";
import { ShinyOutput } from "./shiny-output";
import { installInlineSpecSeeding, seedInlineSpecs } from "./inline-spec";
import { registerShinyreactOutputBinding } from "./output-binding";
import "./shinyreact.css";

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
      registerComponents: (
        catalog: unknown,
        registry: ComponentRegistry,
      ) => void;
      useSetShinyInput: typeof useSetShinyInput;
      useShinyBusy: typeof useShinyBusy;
      useShinyInput: typeof useShinyInput;
      useShinyInputValue: typeof useShinyInputValue;
      useShinyOutputStatus: typeof useShinyOutputStatus;
      useShinyOutputValue: typeof useShinyOutputValue;
      useShinyMessageHandler: typeof useShinyMessageHandler;
      useShinyInitialized: typeof useShinyInitialized;
      ImageOutput: typeof ImageOutput;
      MISSING: typeof MISSING;
      ShinyModuleProvider: typeof ShinyModuleProvider;
      ShinyReactComponentElement: typeof ShinyReactComponentElement;
      ShinyOutput: typeof ShinyOutput;
      seedInlineSpecs: typeof seedInlineSpecs;
      React: typeof React;
      ReactDOM: typeof ReactDOM;
    };
  }
}

// Expose global API — called by downstream packages at page load.
// Preserve any pre-bundle assignment (e.g. window.shinyreact._restore set
// by the head <script> emitted from Python's _restore_script_tag).
window.shinyreact = Object.assign(window.shinyreact || {}, {
  registerComponents,
  useSetShinyInput,
  useShinyBusy,
  useShinyInput,
  useShinyInputValue,
  useShinyOutputStatus,
  useShinyOutputValue,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
  ShinyOutput,
  seedInlineSpecs,
  React,
  ReactDOM,
});

registerShinyreactOutputBinding();

// Render any static Node specs embedded in page chrome (inline JSON scripts).
installInlineSpecSeeding();
