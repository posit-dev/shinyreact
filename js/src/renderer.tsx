import React, { type ReactNode } from "react";
import type { ComponentRegistry, Element, Spec } from "./types";
import { getRegistry } from "./registry";

// A node's explicit React key, if the wire props carry a usable one; otherwise
// fall back to the positional index. Narrowed (not cast) since props.key is
// `unknown` on the wire.
function resolveKey(
  props: Record<string, unknown>,
  fallback: React.Key,
): React.Key {
  const k = props.key;
  return typeof k === "string" || typeof k === "number" ? k : fallback;
}

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
      const key = resolveKey(el.props, fallbackKey);
      const children = (el.children ?? []).map((c, i) =>
        renderNode(c, i, registry),
      );
      return React.createElement(el.name, { ...el.props, key }, ...children);
    }
    case "react": {
      const key = resolveKey(el.props, fallbackKey);
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
      // Unlike intrinsic tags, registered components receive their rendered
      // children via props.children and own how they place them.
      return React.createElement(Registered, { element: el, children, key });
    }
    default: {
      const _exhaustive: never = el;
      throw new Error(
        `[shinyreact] Unknown node type: ${JSON.stringify(_exhaustive)}`,
      );
    }
  }
}

interface ShinyreactRendererProps {
  spec: Spec;
}

/**
 * Walks a wire tree (single node or array of sibling nodes) and renders it as
 * a React tree. The registry is read at render time so any components
 * registered before the render lands are picked up.
 */
function ShinyreactRenderer({ spec }: ShinyreactRendererProps) {
  const registry = getRegistry();
  const nodes = Array.isArray(spec) ? spec : [spec];
  return <>{nodes.map((n, i) => renderNode(n, i, registry))}</>;
}

export { ShinyreactRenderer };
