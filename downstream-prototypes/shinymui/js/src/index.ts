import type { ComponentRegistry } from "./types";
import { Button } from "./components/Button";

const registry: ComponentRegistry = {
  "mui:Button": Button,
};

const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
