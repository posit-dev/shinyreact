# Example 13 — SPA hello world (no build step)

The smallest possible SPA-first Shiny app: a Python server that contains only reactive logic, plus a static React client served from `www/`. No JSX, no bundler, no `package.json`. Edit `app.js` and reload.

## What it shows

A name-input form and click counter rendered twice for direct comparison:

- **Client card** — `Hello, {name}!` and `Count: {clickCount}` computed locally in React state. Updates on every keystroke / click with no roundtrip.
- **Server card** — same two values, but routed through Shiny: `useShinyInput("name")` → `@reactive.calc greeting` → `@reactive_output txtout_title` → `useShinyOutput("txtout_title")`. Updates lag by the websocket round-trip.

The point is that the same data shows up on both cards but the latency is visibly different — the client card is instantaneous, the server card has the websocket delay you'd expect.

## Layout

```
examples/13-spa-hello/
├── app.py            # SpaApp + 2 reactive_output outputs (greeting, click count)
└── www/
    ├── index.html    # 3 lines: stylesheet, #root div, script
    ├── app.js        # raw React.createElement (with `h` shorthand)
    └── main.css      # body reset
```

Four files. No `node_modules`, no Vite, no build script.

## Bridge primitives used

- `from shinyreact import SpaApp, reactive_output` (server)
- `window.shinyreact.useShinyInput(id, default, options?)` for the name field and click counter
- `window.shinyreact.useShinyOutput(id, default)` for the server-computed title and count
- `window.shinyreact.useShinyInitialized()` to suppress the placeholder UI during connection setup

`window.shinyreact.React` and `window.shinyreact.ReactDOM` are pulled in directly so the SPA shares the React instance that owns the shinyreact hooks.

## Run it

```bash
uv run shiny run examples/13-spa-hello/app.py
```

Open the URL printed by Shiny.

## When to use this pattern

Good fit for SPA-first apps that are small enough to not need JSX or component libraries — proof of concept, internal tools, anything where the cost of running a build is more than the cost of writing `React.createElement` calls. As soon as you want shadcn or Tailwind utility classes, see [example 15](../15-columns-shadcn/) and [example 16](../16-shadcn/) for the Vite-based setup.
