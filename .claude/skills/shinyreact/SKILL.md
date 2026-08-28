---
name: shinyreact
description: Build a Shiny app whose UI is a React client (the ui.tsx pattern) using shinyreact for Python or R. Use when the user asks to build, extend, or debug a Shiny app with a React front end, mentions shinyreact, set_react_page(), page_react(), reactive_output, or the useShinyInput / useShinyOutputValue hooks, or wants a Shiny server that returns JSON to a client-owned UI instead of rendering HTML.
---

# Building a shinyreact app

shinyreact is a bridge, not a component library. The Shiny server holds
**only reactive computation** and returns JSON; a React client the app author
owns holds **all** of the UI. They meet at named inputs and outputs.

If the task is porting an *existing* Shiny app to this pattern, use the
`shinyreact-convert-app` skill instead — it starts by describing the app, which
is the step that decides whether the port is correct.

## The shape of every app

```
app.py / app.R      server logic only: reactive_output, reactive.effect, calc
www/ui.js           the React client (or src/ui.tsx built to www/ui.js)
www/ui.css          optional, discovered the same way
```

There is no `ui.output_*()` placeholder anywhere. The page function discovers
`www/ui.js` + `www/ui.css` next to the app and serves them; the client appends
its own mount container to `<body>`.

## Step 1 — pick the tier, and pick the smaller one

| Tier | Use when | Entry |
|---|---|---|
| **No build** | plain React, no JSX, no component library | write `www/ui.js` directly, `React.createElement` via an `h` shorthand |
| **Vite** | JSX, Tailwind, shadcn/ui, npm packages | `src/ui.tsx` → build to `www/ui.js` |

Start at no-build. A `package.json` is a permanent cost; add it when the app
actually needs JSX or a dependency, not in anticipation.

For the Vite tier, the build **must** externalize React to the global so the
app shares the instance that owns the hooks:

```js
build: {
  outDir: "www", emptyOutDir: false, cssCodeSplit: false,
  lib: { entry: "src/ui.tsx", formats: ["iife"], fileName: () => "ui.js" },
  rollupOptions: {
    external: ["react", "react-dom", "react-dom/client"],
    output: {
      assetFileNames: "ui.[ext]",   // Vite lib mode emits style.css otherwise
      globals: {
        react: "window.shinyreact.React",
        "react-dom": "window.shinyreact.ReactDOM",
        "react-dom/client": "window.shinyreact.ReactDOM",
      },
    },
  },
}
```

Two React copies is the single most common failure mode, and it presents as
"hooks return nothing" rather than as an error.

## Step 2 — the page entry point

```python
# Python, Express
from shinyreact import set_react_page
set_react_page()                 # discovers www/ui.js + www/ui.css

# Python, Core
from shinyreact import ReactApp
app = ReactApp(server)           # add bookmark_store="url" for bookmarking
```

```r
# R
ui <- page_react()               # discovers www/ui.js + www/ui.css
shinyApp(ui, server)
```

- All of them are zero-argument. Do not hand-wire an `HTMLDependency`.
- An app that owns a complete `index.html` (with a `{{ headContent() }}`
  marker) uses `page_react_html()`; `ReactApp` discovers that case too.
- Assets are served mtime-versioned, so an edited `ui.js` is never stale in
  the browser cache.
- `set_react_page()` additionally discovers `HTMLDependency` objects from
  traditional renderers (`@render.data_frame`, `@render_plotly`) and injects
  them. R does the same thing by pushing them after the flush — either way, no
  wiring.

## Step 3 — the server returns JSON

```python
import shinyreact
from shiny.express import input

@shinyreact.reactive_output
def dist_data():
    return {"breaks": [...], "counts": [...]}   # any JSON-able value
```

```r
output$dist_data <- reactive_output({
  # input$bins is NULL until the client's first message — return NULL, not
  # req(): req()'s silent error still reaches the client console.
  n <- input$bins
  if (is.null(n)) return(NULL)
  list(breaks = I(breaks), counts = I(counts))  # I() keeps length-1 as arrays
})
```

Server-side rules that matter:

- **Fact table → one shared `@reactive.calc` → one output per card.** Every
  input filters the shared calc; each card aggregates from it. Static
  pre-aggregated tables produce a dashboard where half the filters visibly do
  nothing.
- Traditional renderers still work and are readable from
  `useShinyOutputValue` with no placeholder. Reach for `reactive_output` when
  the client draws, and a traditional renderer when the server draws
  (`@render.plot` + `ImageOutput`) or a widget owns the DOM
  (`@render.data_frame`, `@render_plotly` + `ShinyOutput`).
- `shinyreact.send_message(session, id, data)` pushes a one-off message to
  `useShinyMessageHandler(id, fn)` — for things that are events, not state.

## Step 4 — the client reads and writes named channels

Everything is on `window.shinyreact` (or imported from `@posit/shinyreact` in
an npm-tier build).

| | Full | Read-only | Write-only |
|---|---|---|---|
| **Input** | `useShinyInput(id, default)` → `[value, setValue]` | `useShinyInputValue(id)` | `useSetShinyInput(id, default)` |
| **Output** | — | `useShinyOutputValue(id, default?)` | — |
| **Status** | | `useShinyOutputStatus(id)` → `"pending" \| "ready" \| "recalculating" \| "error"` | |

Plus `useShinyInitialized()`, `useShinyBusy()`, `useShinyMessageHandler()`, and
the components `ImageOutput`, `ShinyOutput`, `ShinyModuleProvider`.

**Pick the narrowest hook that fits the call site.** A button that pushes and
never reads uses `useSetShinyInput`; a card that only displays uses
`useShinyInputValue` / `useShinyOutputValue`. This makes data-flow direction
visible and avoids re-renders from channels the component never observes.

### The patterns worth copying verbatim

**Action button** — the Shiny idiom, start at 0 and increment:

```js
const [count, setCount] = useShinyInput("go", 0, { debounceMs: 0, priority: "event" });
```
```python
@shinyreact.reactive_output
@reactive.event(input.go, ignore_init=True)   # ignore the initial 0 from mount
def response(): ...
```

`debounceMs: 0` so rapid clicks are not coalesced by the 100 ms default;
`priority: "event"` so Shiny treats it as an event.

**Loading vs. recalculating** — never collapse the four statuses into one
boolean:

```jsx
const data = useShinyOutputValue("foo");
const status = useShinyOutputStatus("foo");
if (!data) return <Skeleton/>;                            // only before the FIRST value
return <Chart className={status === "recalculating" ? "recalculating" : ""} data={data}/>;
```

with `.recalculating { opacity: .6; transition: opacity 200ms }`. Gating on
`status !== "ready"` unmounts the chart on every input change, destroying and
rebuilding its DOM.

**Gate the first paint** on `useShinyInitialized()` (`if (!initialized) return
null`) so the UI does not flash empty defaults during connection setup.

**Typed inputs** — `useShinyInput(id, default, { type: "shiny.datetime" })`
appends `:type` to the wire id and routes through Shiny's input handler, so
`input.when()` is a `datetime`. The id/type pairing is a contract: a later
mount that disagrees throws.

Untyped values go through shinyreact's own `shinyreact.default` handler, which
keeps R and Python agreeing about the same JSON (`[]` stays `list()`, nested
arrays keep their shape). Use `type: "shinyreact.asis"` for the parsed value
untouched.

## Things that bite

- **`defaultValue` is captured on first mount only**, like `useState`. Inline
  `{}` / `[]` are safe — stabilized internally.
- **Inline arrow handlers are safe** for `useShinyMessageHandler` — stored in a
  ref.
- **Input ids are global per page.** Two mounts of one id share state; that is
  the feature (a button writes, a card reads), but disagreeing on `type`
  throws and disagreeing on `priority` warns and last-writer-wins.
- **Terminology**: this is the `ui.tsx` pattern. Never call it an "SPA".

## Verify it

Do not stop at "the code is written". At minimum:

1. Factor pure logic (binning, formatting, conversions) into a module beside
   the app so it is importable and testable — logic inside `app.py` next to
   `set_react_page()` cannot be unit tested.
2. Write down what the app does, in plain English, as a `FEATURES.md` behavior
   tree beside the app — one atomically checkable claim per leaf.
3. Test against that description. In the shinyreact repo,
   `.claude/references/verifying-ui-code.md` describes the jsdom harness that
   mounts the real `www/ui.js` against a fake Shiny, and the traps (React
   ignores raw `change` events; debounce coalesces within a tick even at
   `debounceMs: 0`).

## Worked examples

The shinyreact repo's `examples/` directory is the reference, each with a
`FEATURES.md` describing it leaf by leaf: `01-hello` (no-build, SVG chart,
Python + R servers), `02-columns` (event inputs), `03`/`04` (Vite + shadcn/ui),
`06`/`07` (`ShinyOutput` hosting a data frame / plotly widget), `08` (typed
inputs), `09` (Vite HMR against a running Shiny), `10` (bookmarking).
