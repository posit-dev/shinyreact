import React, { type ReactNode } from "react";
import type { ComponentRegistry, Element, Spec } from "./spec";
import { getRegistry } from "./registry";

function renderNode(
  el: Element,
  fallbackKey: React.Key,
  registry: ComponentRegistry,
): ReactNode {
  switch (el.type) {
    case "text":
      return el.value;
    case "html":
      return React.createElement("span", {
        key: fallbackKey,
        dangerouslySetInnerHTML: { __html: el.html },
      });
    case "tag": {
      const key = (el.props.key as React.Key) ?? fallbackKey;
      const children = (el.children ?? []).map((c, i) =>
        renderNode(c, i, registry),
      );
      return React.createElement(el.name, { ...el.props, key }, ...children);
    }
    case "react": {
      const key = (el.props.key as React.Key) ?? fallbackKey;
      const children = (el.children ?? []).map((c, i) =>
        renderNode(c, i, registry),
      );
      const Registered = registry[el.name];
      if (!Registered) {
        throw new Error(
          `[shinyreact] Unknown component "${el.name}". Register it via ` +
            `window.shinyreact.registerComponents() before rendering.`,
        );
      }
      return React.createElement(Registered, { element: el, children, key });
    }
  }
}

interface ShinyreactRendererProps {
  spec: Spec;
}

/**
 * Walks a wire tree (single node or array of sibling nodes) and renders it as
 * a React tree. The registry is read at render time so components registered
 * before the render lands are picked up.
 */
function ShinyreactRenderer({ spec }: ShinyreactRendererProps) {
  const registry = getRegistry();
  const nodes = Array.isArray(spec) ? spec : [spec];
  return <>{nodes.map((n, i) => renderNode(n, i, registry))}</>;
}

export { ShinyreactRenderer };
