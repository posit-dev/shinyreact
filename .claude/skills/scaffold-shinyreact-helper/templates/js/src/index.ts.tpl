import type { ComponentRegistry } from "./types";
import { {{Stub}} } from "./components/{{Stub}}";

const registry: ComponentRegistry = {
  "{{prefix}}:{{Stub}}": {{Stub}},
};

const catalog = { name: "{{pkg}}", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
