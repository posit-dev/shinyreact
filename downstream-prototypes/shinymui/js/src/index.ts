import type { ComponentRegistry } from "./types";

// Components will be added one per task; registry starts empty.
const registry: ComponentRegistry = {};

// Catalog is reserved for future validation in shinyreact (currently unused).
const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
