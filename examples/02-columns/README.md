# Example 14 — drag-between-columns (ui.tsx-first, no build step)

Three columns of items with ←/→ buttons that move items between columns. The same demo as
a traditional Shiny `render.ui` + dynamic-observer implementation, but rebuilt on the new `shinyreact` package and stripped down to no build step.

## Why it exists

This pattern is the canonical motivating case for the `ui.tsx`-first architecture (see `DESIGN.md` §4 "The dynamic UI problem"). In traditional Shiny the server has to:

- track per-item input IDs,
- spin up and tear down `@reactive.event` observers as items appear/disappear,
- regenerate the column UI on every change via `render.ui`.

In the `ui.tsx`-first model the server only owns the **data**. The client (a plain React app) owns the **UI**. The server gets one event input — `move_item` carrying `{item, from, to}` — applies it to a `reactive.value`, and ships the new column dict back through `@reactive_output`. React reconciles. No dynamic observers, no generated IDs, no UI lifecycle code on the server.

The result: ~20 lines of server logic, versus ~80 lines wrestling with observers in the `render.ui` version.

## Layout

```
examples/02-columns/
├── app.py            # set_react_page() + 1 reactive_output (column_data) + 1 reactive.effect on input.move_item
└── www/
    ├── index.html
    ├── app.js        # raw React.createElement (Column + ItemRow components)
    └── main.css
```

Same 4-file shape as [01-hello](../01-hello/). No `package.json`, no bundler.

## Bridge primitives used

- `from shinyreact import reactive_output, set_react_page` (server)
- `useShinyInput("move_item", null, { debounceMs: 0, priority: "event" })` — sends a `{item, from, to}` event payload on each click; `priority: "event"` is the Shiny pattern for action-button-style inputs.
- `useShinyOutputValue("column_data", null)` — receives the latest `{A:[...], B:[...], C:[...]}` from the server and re-renders.

## Run it

```bash
uv run shiny run examples/02-columns/app.py
```

## When to use this pattern

Anytime the UI is a function of dynamic data (drag-and-drop boards, sortable lists, arbitrary collections) — owning the UI on the client eliminates an entire class of observer-lifecycle bugs that the `app.py` pattern is prone to. For a styled version with shadcn components see [03-columns-shadcn](../03-columns-shadcn/).
