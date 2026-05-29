import React from "react";
import * as ReactDOM from "react-dom/client";
import type { ComponentRegistry, Spec } from "./spec";
import { registerComponents } from "./registry";
import { ShinyreactRenderer } from "./renderer";
import { ShinyOutput } from "./shiny-output";
import { getOrCreateRoot, hasRoot, unmountRoot } from "./roots";
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
  React,
  ReactDOM,
});

// Shiny output binding for .shinyreact-output elements
class ShinyreactOutputBinding extends Shiny.OutputBinding {
  find(scope: Element): ArrayLike<Element> {
    return $(scope).find(".shinyreact-output");
  }

  renderValue(el: Element, data: Spec | null): void {
    if (!data) {
      if (hasRoot(el)) unmountRoot(el);
      return;
    }
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(React.createElement(ShinyreactRenderer, { spec: data }));
  }

  renderError(el: Element, err: { message: string }): void {
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(
      React.createElement(
        "div",
        { style: { color: "red", padding: "8px" } },
        err.message,
      ),
    );
  }
}

// Register with Shiny — Shiny is always loaded before this script
// because HTMLDependency ordering places Shiny's scripts first.
Shiny.outputBindings.register(new ShinyreactOutputBinding(), "shinyreact.output");
