# Example 1 — Hello world (shinyreact)

The smallest end-to-end example using the **JSON-spec** package (`shinyreact`). The Python server describes a UI tree as a `shinyreact.Node`, sends it as JSON, and a small client-side JavaScript bundle renders it with React.

> **Note:** This example uses `shinyreact` — the original server-driven-UI approach. For the SPA-first replacement, see [example 13](../13-spa-hello/).

## What it shows

- A `Card` containing a `TextInput`, a `Divider`, and an `InputDisplay` that echoes the typed value.
- The bridge round-trip: `useShinyInput` on the client → reactive on the server → re-rendered `Node` tree → React reconciles.
- The downstream-package extension pattern: `hello_world.js` registers `Card`, `TextInput`, `Divider`, and `InputDisplay` via `window.shinyreact.registerComponents(...)`; `app.py` references them by `type` name through `shinyreact.Node`.

## Layout

```
examples/1-hello-world/
├── app.py                # Server: composes Node tree, returns it from @shinyreact.reactive_output
├── hello_world.js        # JS bundle: registers Card / TextInput / Divider / InputDisplay
└── styles.css
```

The JS bundle is loaded as an `HTMLDependency`, version-stamped with the file's mtime so the browser picks up edits in dev.

## Run it

```bash
uv run shiny run examples/1-hello-world/app.py
```
