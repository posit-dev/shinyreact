# Example 9 — Blending shinyjsonold with traditional Shiny (shinyjsonold)

Demonstrates that `shinyjsonold` can coexist with traditional Shiny outputs on the same page. Some panels are rendered through the JSON-spec bridge (custom React components), and others use stock `@render.plot` / `@render.text` / `@render.table` against vanilla Shiny output containers.

> **Note:** Uses `shinyjsonold`. This blended approach is mostly a migration aid — once you're committed to SPA-first, the entire page lives on the client.

## What it shows

- A page that is partly a `shinyjsonold.Node` tree (cards with custom interactive components) and partly a Shiny `ui.layout_*` block hosting a regular matplotlib plot via `@render.plot`.
- A shared filter (cylinder count) drives both worlds — the React component reads `useShinyInput("cyl")`, the Python plot reads `input.cyl()`.
- Same data (`mtcars` subset), two rendering paths, one reactive graph.

## Layout

```
examples/9-blended/
├── app.py        # Server: shinyjson.render outputs + traditional render.plot
├── blended.js    # JS bundle: custom cards
└── styles.css
```

## Run it

```bash
uv run shiny run examples/9-blended/app.py
```
