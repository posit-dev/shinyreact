import type { ComponentRegistry } from "./types";
import { Button } from "./components/Button";
import { TextField } from "./components/TextField";

const registry: ComponentRegistry = {
  "mui:Button": Button,
  "mui:TextField": TextField,
};

const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
