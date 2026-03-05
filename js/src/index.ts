import React from "react";
import { createRoot, type Root } from "react-dom/client";
import type { Spec } from "@json-render/core";
import type { ComponentRegistry } from "@json-render/react";
import { registerComponents } from "./registry";
import { ShinyjsonRenderer } from "./renderer";
import "./shinyjson.css";

// Extend window with shinyjson's public global API
declare global {
  interface Window {
    shinyjson: {
      registerComponents: (catalog: unknown, registry: ComponentRegistry) => void;
    };
  }
}

// Expose global API — called by downstream packages at page load
window.shinyjson = { registerComponents };

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
  find(scope: Element): NodeListOf<Element> {
    return scope.querySelectorAll(".shinyjson-output");
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
