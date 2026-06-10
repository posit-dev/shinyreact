import type { ComponentRegistry } from "./types";

// Accumulated component registry — populated by downstream packages calling
// window.shinyreact.registerComponents() at page load.
let _registry: ComponentRegistry = {};

/**
 * Register components from a downstream package (e.g. shinyshadcn).
 * Called via window.shinyreact.registerComponents(catalog, registry).
 *
 * @param _catalog - Catalog definition (reserved for future validation)
 * @param registry - Map of component name → React component
 */
function registerComponents(
  _catalog: unknown,
  registry: ComponentRegistry,
): void {
  for (const key of Object.keys(registry)) {
    if (key in _registry) {
      console.warn(
        `[shinyreact] Component "${key}" is being re-registered. ` +
          `The previous registration will be overwritten.`,
      );
    }
  }
  Object.assign(_registry, registry);
}

/**
 * Get the current accumulated registry for use by the renderer.
 */
function getRegistry(): ComponentRegistry {
  return _registry;
}

/**
 * Reset the registry. Test-only; not part of the public API.
 */
function _resetForTests(): void {
  _registry = {};
}

export { registerComponents, getRegistry, _resetForTests };
