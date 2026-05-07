# Example 8 — Shiny modules (shinyreact)

Demonstrates Shiny's `@module.server` integration with the JSON-spec bridge. Multiple instances of the same component (a counter) live on one page, each with its own namespaced inputs and outputs.

> **Note:** Uses `shinyreact`. The module/namespace machinery is implemented in the vendored `shiny-react` (via `ShinyModuleProvider` and `useShinyModuleNamespace`) and works in both the JSON-spec and `client-ui`-first models.

## What it shows

- A `WidgetsGrid` containing three `ModuleCounter` instances, each tagged with a different `namespace` prop ("a", "b", "c").
- `useShinyInput`/`useShinyOutput` calls inside the React component automatically prefix their IDs with the surrounding namespace, so `counter` becomes `a-counter`, `b-counter`, `c-counter` on the wire.
- Server-side: a single `@module.server` function defines the counter logic once and is invoked three times with matching namespace IDs.

The point is that you can build a reusable React component that talks to Shiny without hard-coding output IDs — namespacing keeps multiple instances independent.

## Layout

```
examples/8-modules/
├── app.py        # Server: counter_module_server invoked 3x with different namespaces
├── modules.js    # JS bundle: AppLayout / WidgetsGrid / ModuleCounter / InfoSection
└── styles.css
```

## Run it

```bash
uv run shiny run examples/8-modules/app.py
```
