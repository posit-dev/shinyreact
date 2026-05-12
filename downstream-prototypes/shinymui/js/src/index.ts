import type { ComponentRegistry } from "./types";
import { Button } from "./components/Button";
import { Card } from "./components/Card";
import { Slider } from "./components/Slider";
import { TextField } from "./components/TextField";

const registry: ComponentRegistry = {
  "mui:Button": Button,
  "mui:Card": Card,
  "mui:Slider": Slider,
  "mui:TextField": TextField,
};

const catalog = { name: "shinymui", version: "0.0.0-prototype" };

window.shinyreact.registerComponents(catalog, registry);
