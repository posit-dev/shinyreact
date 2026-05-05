import React from "react";
import * as ReactDOM from "react-dom/client";
import { createRoot, type Root } from "react-dom/client";
import type { ComponentRegistry, Spec } from "./spec";
import { registerComponents } from "./registry";
import { ShinyjsonRenderer } from "./renderer";
import "./shinyjson.css";

// Re-export @posit/shiny-react hooks and components.
//
// We bundle @posit/shiny-react and React into this single IIFE so that:
// 1. All code shares a single React instance (React hooks break with multiple Reacts)
// 2. Downstream component authors get hooks via window.shinyjson.*
// 3. Downstream ESM builds can externalize React to window.shinyjson.React/ReactDOM
import {
  useShinyBusy,
  useShinyInput,
  useShinyOutput,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
} from "./shiny-react";

// Extend window with shinyjson's public global API
declare global {
  interface Window {
    shinyjson: {
      registerComponents: (
        catalog: unknown,
        registry: ComponentRegistry,
      ) => void;
      useShinyBusy: typeof useShinyBusy;
      useShinyInput: typeof useShinyInput;
      useShinyOutput: typeof useShinyOutput;
      useShinyMessageHandler: typeof useShinyMessageHandler;
      useShinyInitialized: typeof useShinyInitialized;
      ImageOutput: typeof ImageOutput;
      MISSING: typeof MISSING;
      ShinyModuleProvider: typeof ShinyModuleProvider;
      ShinyReactComponentElement: typeof ShinyReactComponentElement;
      React: typeof React;
      ReactDOM: typeof ReactDOM;
    };
  }
}

// Expose global API — called by downstream packages at page load
window.shinyjson = {
  registerComponents,
  useShinyBusy,
  useShinyInput,
  useShinyOutput,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
  React,
  ReactDOM,
};

// React root cache: one React root per output DOM element
const roots = new WeakMap<Element, Root>();

function getOrCreateRoot(el: HTMLElement): Root {
  if (!roots.has(el)) {
    roots.set(el, createRoot(el));
  }
  return roots.get(el)!;
}

// Shiny output binding for .shinyjson-output elements
class ShinyjsonOutputBinding extends Shiny.OutputBinding {
  find(scope: Element): ArrayLike<Element> {
    return $(scope).find(".shinyjson-output");
  }

  renderValue(el: Element, data: Spec | null): void {
    if (!data) {
      const existing = roots.get(el);
      if (existing) {
        existing.unmount();
        roots.delete(el);
      }
      return;
    }
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(React.createElement(ShinyjsonRenderer, { spec: data }));
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
Shiny.outputBindings.register(new ShinyjsonOutputBinding(), "shinyjson.output");
