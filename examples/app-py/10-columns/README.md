# Example 11 — Drag-between-columns (traditional Shiny)

The classic "items move between columns" demo built with **traditional Shiny only** — no `shinyreact*`, no React. Stays here as the "before" picture for the `ui.tsx`-first sales pitch in `DESIGN.md` §4.

## What it shows

- Three columns of items with ←/→ buttons to move items between them.
- The complete observer-lifecycle dance the `ui.tsx`-first model is designed to *avoid*:
  - Generated per-item input IDs (`move_apple_a_right`, etc.).
  - A `_observers: list[reactive.Effect_]` registry tracking dynamically created `@reactive.event` observers.
  - Manual destroy-and-recreate of those observers every time the data changes.
  - `render.ui` re-rendering the column UI on every mutation.

The whole file is ~80 lines of server logic, almost all of it bookkeeping for the dynamic UI.

## Compared to the ui.tsx versions

- [02-columns](../../ui-tsx/02-columns/) — same demo with the **new** `shinyreact` package, no build step.
- [03-columns-shadcn](../../ui-tsx/03-columns-shadcn/) — same demo with shadcn/ui styling (Vite build).

The point of preserving this file is to show what `DESIGN.md` means by "the dynamic UI problem" — server-managed UI for collection-style interactions is genuinely hard, even for experienced Shiny developers, and the `ui.tsx`-first model dissolves it.

## Run it

```bash
uv run shiny run examples/app-py/10-columns/app.py
```
