import type { ComponentRegistry } from "@json-render/react";

// Accumulated component registry — populated by downstream packages calling
// window.shinyjson.registerComponents() at page load.
let _registry: ComponentRegistry = {};

/**
 * Register components from a downstream package (e.g. shinyshadcn).
 * Called via window.shinyjson.registerComponents(catalog, registry).
 *
 * @param _catalog - Catalog definition (reserved for future validation)
 * @param registry - Map of component name → React component
 */
function registerComponents(
  _catalog: unknown,
  registry: ComponentRegistry,
): void {
  Object.assign(_registry, registry);
}

/**
 * Get the current accumulated registry for use by the renderer.
 */
function getRegistry(): ComponentRegistry {
  return _registry;
}

export { registerComponents, getRegistry };
