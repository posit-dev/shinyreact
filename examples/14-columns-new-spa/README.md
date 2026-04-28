# Example 14 — drag-between-columns (SPA-first, no build step)

Three columns of items with ←/→ buttons that move items between columns. The same demo as
[example 11](../11-columns-traditional/) (traditional Shiny with `render.ui` + dynamic observers) and [example 12](../12-columns-spa/) (the previous-shinyjson SPA prototype), but rebuilt on the new `shinyjson` package and stripped down to no build step.

## Why it exists

This pattern is the canonical motivating case for the SPA-first architecture (see `DESIGN.md` §4 "The dynamic UI problem"). In traditional Shiny the server has to:

- track per-item input IDs,
- spin up and tear down `@reactive.event` observers as items appear/disappear,
- regenerate the column UI on every change via `render.ui`.

In the SPA-first model the server only owns the **data**. The client (a plain React app) owns the **UI**. The server gets one event input — `move_item` carrying `{item, from, to}` — applies it to a `reactive.value`, and ships the new column dict back through `@render_json`. React reconciles. No dynamic observers, no generated IDs, no UI lifecycle code on the server.

Compare `examples/14-columns-new-spa/app.py` (~20 lines of server logic) to `examples/11-columns-traditional/app.py` (~80 lines wrestling with observers).

## Layout

```
examples/14-columns-new-spa/
├── app.py            # SpaApp + 1 render_json (column_data) + 1 reactive.effect on input.move_item
└── www/
    ├── index.html
    ├── app.js        # raw React.createElement (Column + ItemRow components)
    └── main.css
```

Same 4-file shape as [example 13](../13-spa-hello/). No `package.json`, no bundler.

## Bridge primitives used

- `from shinyjson import SpaApp, render_json` (server)
- `useShinyInput("move_item", null, { debounceMs: 0, priority: "event" })` — sends a `{item, from, to}` event payload on each click; `priority: "event"` is the Shiny pattern for action-button-style inputs.
- `useShinyOutput("column_data", null)` — receives the latest `{A:[...], B:[...], C:[...]}` from the server and re-renders.

## Run it

```bash
uv run shiny run examples/14-columns-new-spa/app.py
```

## When to use this pattern

Anytime the UI is a function of dynamic data (drag-and-drop boards, sortable lists, arbitrary collections) — owning the UI on the client eliminates an entire class of observer-lifecycle bugs that the traditional pattern is prone to. For a styled version with shadcn components see [example 15](../15-columns-shadcn/).
