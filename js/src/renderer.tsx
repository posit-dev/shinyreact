import React, { type ReactNode } from "react";
import type { ComponentRegistry, Element, Spec } from "./spec";
import { getRegistry } from "./registry";

function renderNode(
  id: string,
  spec: Spec,
  registry: ComponentRegistry,
): ReactNode {
  const el: Element | undefined = spec.elements[id];
  if (!el) return null;

  const childIds = el.children ?? [];
  const children = childIds.map((cid) => (
    <React.Fragment key={cid}>
      {renderNode(cid, spec, registry)}
    </React.Fragment>
  ));

  const Registered = registry[el.type];
  if (Registered) {
    return React.createElement(Registered, { element: el, children });
  }

  return React.createElement(el.type, el.props, ...children);
}

interface ShinyjsonRendererProps {
  spec: Spec;
}

/**
 * Walks a Spec and renders it as a React tree. The component registry is read
 * at render time so any components registered before the render lands are
 * picked up.
 */
function ShinyjsonRenderer({ spec }: ShinyjsonRendererProps) {
  const registry = getRegistry();
  return <>{renderNode(spec.root, spec, registry)}</>;
}

export { ShinyjsonRenderer };
