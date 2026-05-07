# Example 11 — Drag-between-columns (traditional Shiny)

The classic "items move between columns" demo built with **traditional Shiny only** — no `shinyreact*`, no React. Stays here as the "before" picture for the `client-ui`-first sales pitch in `DESIGN.md` §4.

## What it shows

- Three columns of items with ←/→ buttons to move items between them.
- The complete observer-lifecycle dance the `client-ui`-first model is designed to *avoid*:
  - Generated per-item input IDs (`move_apple_a_right`, etc.).
  - A `_observers: list[reactive.Effect_]` registry tracking dynamically created `@reactive.event` observers.
  - Manual destroy-and-recreate of those observers every time the data changes.
  - `render.ui` re-rendering the column UI on every mutation.

The whole file is ~80 lines of server logic, almost all of it bookkeeping for the dynamic UI.

## Compared to the client-ui versions

- [Example 12](../12-columns-spa/) — same demo with the **legacy** `shinyreact` client-ui prototype. Server drops to ~20 lines.
- [Example 14](../14-columns-new-spa/) — same demo with the **new** `shinyreact` package, no build step.
- [Example 15](../15-columns-shadcn/) — same demo with shadcn/ui styling (Vite build).

The point of preserving this file is to show what `DESIGN.md` means by "the dynamic UI problem" — server-managed UI for collection-style interactions is genuinely hard, even for experienced Shiny developers, and the `client-ui`-first model dissolves it.

## Run it

```bash
uv run shiny run examples/11-columns-traditional/app.py
```
