import { Renderer } from "@json-render/react";
import type { Spec } from "@json-render/core";
import { getRegistry } from "./registry";

interface ShinyjsonRendererProps {
  spec: Spec;
}

/**
 * React component that renders a json-render Spec using all registered components.
 * The registry is read at render time, capturing all components registered via
 * window.shinyjson.registerComponents() before this render was triggered.
 */
function ShinyjsonRenderer({ spec }: ShinyjsonRendererProps) {
  return <Renderer spec={spec} registry={getRegistry()} />;
}

export { ShinyjsonRenderer };
