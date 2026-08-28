---
name: shinyreact-build-app
description: Build a Shiny app whose UI is a React client (the ui.tsx pattern) using shinyreact for Python or R. Use when the user asks to build, extend, or debug a Shiny app with a React front end, mentions shinyreact, set_react_page(), page_react(), reactive_output, or the useShinyInput / useShinyOutputValue hooks, or wants a Shiny server that returns JSON to a client-owned UI instead of rendering HTML.
---

# Building a shinyreact app

shinyreact is a bridge, not a component library. The Shiny server holds
**only reactive computation** and returns JSON; a React client the app author
owns holds **all** of the UI. They meet at named inputs and outputs.

If the task is porting an *existing* Shiny app to this pattern, use the
`shinyreact-convert-app` skill instead — it starts by describing the app, which
is the step that decides whether the port is correct.

**This skill covers Python and R together.** shinyreact is one API in two
languages, so anything unmarked below holds in both; `[py]` and `[r]` mark the
few places they genuinely differ, and the client half is the same either way.
Skim past the language you are not using rather than assuming it has no
counterpart.

## The shape of every app

```
app.py / app.R      server logic only: reactive_output, reactive.effect, calc
src/ui.tsx          the React client you edit  (no-build tier: skip src/)
www/ui.js           what the server serves — a Vite build output, or the
                    hand-written client on the no-build tier
www/ui.css          optional, discovered the same way
```

There is no `ui.output_*()` placeholder anywhere. The page function discovers
`www/ui.js` + `www/ui.css` next to the app and serves them; the client appends
its own mount container to `<body>`.

## Step 1 — pick the tier: build unless you cannot

**Default to a real Vite build.** JSX, TypeScript, a component library, and
`npm` are worth having, and the cost of a `package.json` is a one-time
`npm install` — trivial if you have a terminal. Hand-writing
`React.createElement` trees to avoid a build step trades a few seconds of setup
for an app nobody wants to edit.

| Tier | Use when | Entry |
|---|---|---|
| **Vite** (default) | anything real: JSX, Tailwind, shadcn/ui, npm packages, TypeScript | `src/ui.tsx` → built to `www/ui.js` |
| **No build** | you cannot run `npm` (no toolchain, locked-down host), or the app must ship as one editable file | write `www/ui.js` directly |

Both produce the same thing — a classic script at `www/ui.js` — so the server
side and every hook below are identical, and you can move between tiers later
without touching `app.py` / `app.R`.

### The Vite tier

```
package.json      "build": "vite build",  "dev": "vite build --watch"
vite.config.js
src/ui.tsx        entry: mounts <App/>
src/App.tsx       your components
www/ui.js         BUILD OUTPUT — never edit, and gitignore it
www/ui.css        BUILD OUTPUT
```

The build **must** externalize React to the global so the app shares the
instance that owns the hooks:

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

**Two React copies is the single most common failure mode**, and it presents as
"hooks return nothing" rather than as an error. If you skip `external` /
`globals`, Vite bundles its own React and every hook silently stops working.

`src/ui.tsx` is the entry, and it is short — the page has no mount container,
so the app makes its own:

```jsx
import "@/index.css";
import App from "@/App";

const { React, ReactDOM } = window.shinyreact;

const root = ReactDOM.createRoot(
  document.body.appendChild(document.createElement("div")),
);
root.render(<App />);
```

Hooks come off the same global: `const { useShinyInput } = window.shinyreact;`.
(An npm-tier app that installs `@posit/shinyreact` imports them instead and
externalizes React the same way; reach for that only when you are publishing a
component library, not for an app.)

Run `npm run build` after every client change, or leave
`npm run dev` (`vite build --watch`) running. **A stale `www/ui.js` is the
second-most-common confusion** — the source looks right and the browser
disagrees.

### Install libraries; do not hand-roll UI

The second reason to take the build tier is that it gives you npm. **Reach for
an established library before writing a component**, especially for anything
with accessibility, keyboard handling, or edge cases — a date picker, a data
table, a combobox, a chart. Hand-rolled equivalents are the bulk of what goes
wrong in an agent-built app: they are the code with no upstream tests, no
issue tracker, and no one else reading it, and every line is one more thing
the user has to review.

| Need | Reach for |
|---|---|
| components, theming | **shadcn/ui + Tailwind** — the default; components are copied into your source, so they stay editable |
| icons | `lucide-react` |
| charts | `recharts` for ordinary business charts; `plotly.js`/`visx`/`d3` when you need their specifics |
| tables | `@tanstack/react-table` (headless — pair with shadcn's table) |
| forms | `react-hook-form` + `zod` |
| dates | `date-fns` |
| drag and drop | `@dnd-kit/core` |

Two shinyreact-specific caveats:

- **Never install `react` or `react-dom` as real dependencies** you bundle.
  They stay `external` and come from `window.shinyreact` — see the config
  above. A library listing React as a *peer* dependency is fine and normal.
- **A widget that already exists on the Shiny side does not need a React port.**
  A data frame, a plotly figure, a leaflet map: keep the render function and
  host it with `ShinyOutput` (Step 3). Re-implementing it in React is work you
  can simply not do.

Write a component from scratch when it is genuinely app-specific — the
histogram that draws *your* data shape, the layout of *your* dashboard. That is
the part a library cannot know.

### The no-build tier

If you truly cannot run `npm`, everything comes off the global and `h` stands
in for JSX. Nesting `React.createElement` gets unreadable fast, which is the
reason this is the fallback. See
[`references/no-build.md`](references/no-build.md).

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
  marker) uses `page_react_html()`; `[py]` `ReactApp` discovers that case too,
  `[r]` pass it to `shinyApp(ui = ...)` yourself.
- Assets are served mtime-versioned, so an edited `ui.js` is never stale in
  the browser cache.
- Dependencies of traditional renderers are discovered for you either way, so
  there is nothing to wire. `[py]` `set_react_page()` finds the
  `HTMLDependency` objects and injects them into `<head>`; `[r]` the page is
  rendered before `server()` runs, so they are pushed to the client after the
  flush instead.
- `[py]` paths resolve against the calling module; `[r]` against the working
  directory. Same zero-config result, different rule if you pass one
  explicitly.

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

- **Fact table → one shared reactive → one output per card.** Every input
  filters the shared `[py]` `@reactive.calc` / `[r]` `reactive()`; each card
  aggregates from it. Static pre-aggregated tables produce a dashboard where
  half the filters visibly do nothing.
- Traditional renderers still work and are readable from
  `useShinyOutputValue` with no placeholder. Reach for `reactive_output` when
  the client draws, and a traditional renderer when the server draws
  (`[py]` `@render.plot` / `[r]` `renderPlot()`, hosted by `ImageOutput`) or a
  widget owns the DOM (`[py]` `@render.data_frame`, `@render_plotly` /
  `[r]` `DT::renderDT()`, `plotly::renderPlotly()`, hosted by `ShinyOutput`).
- `send_message(session, id, data)` pushes a one-off message to
  `useShinyMessageHandler(id, fn)` — for things that are events, not state.

### Hosting a traditional renderer

A widget that already works does not need a React port. Keep the render
function and host it client-side — no `*Output()` placeholder on the server:
`ShinyOutput` for something that owns its own DOM (data frames, plotly, DT,
leaflet), `ImageOutput` for a server-drawn image (`[py]` `@render.plot`,
`[r]` `renderPlot()`). Both are in
[`references/shiny-outputs.md`](references/shiny-outputs.md), including the
part you cannot guess: how to spell the element each binding looks for.

Reach for `reactive_output` plus your own chart whenever the client *could*
draw it — you get a real React component instead of a server-rendered PNG.

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

**Shiny modules** — when the same server code runs more than once on a page,
wrap each instance in `ShinyModuleProvider` and the hooks inside it namespace
their ids to match the module server. Components stay written as if they owned
their ids outright. See [`references/modules.md`](references/modules.md) for the
resolution rules, the `null` vs. omitted distinction, and the pitfalls.

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
```r
output$response <- reactive_output({
  # ignore the initial 0 the client sends at mount -- NULL, not req(), for the
  # same reason as above
  if (is.null(input$go) || input$go == 0) return(NULL)
  ...
})
```

`debounceMs: 0` so rapid clicks are not coalesced by the 100 ms default;
`priority: "event"` so Shiny treats it as an event.

**Loading vs. recalculating** — never collapse the four statuses into one
boolean:

```jsx
const data = useShinyOutputValue("foo");
const status = useShinyOutputStatus("foo");

// WRONG: unmounts the chart on every input change, tearing down and rebuilding
// its DOM — the user sees a skeleton flash between every result.
if (!data || status !== "ready") return <Skeleton/>;

// CORRECT: skeleton only before the FIRST value; afterwards keep the chart
// mounted and dim it while the server recomputes.
if (!data) return <Skeleton/>;
return <Chart className={status === "recalculating" ? "recalculating" : ""} data={data}/>;
```

with `.recalculating { opacity: .6; transition: opacity 200ms }`.
`"pending"` is the only state where you have no data yet; `"recalculating"`
means the previous result is still valid, so show it.

**Gate the first paint** on `useShinyInitialized()` (`if (!initialized) return
null`) so the UI does not flash empty defaults during connection setup.

**App-wide activity** — `useShinyBusy()` is a boolean that tracks Shiny's
`shiny:busy` / `shiny:idle` events, i.e. whether the server is working on
*anything*:

```jsx
const busy = useShinyBusy();
<div className={busy ? "app busy" : "app"}>…</div>   // e.g. a top progress bar
```

It seeds `true` if the page is already busy when the component mounts, so a
component that appears mid-request is not stuck showing "idle". Use it for one
global cue — a progress bar, a dimmed toolbar. It is the wrong tool for
per-card state, because *any* output recomputing makes it `true`: use
`useShinyOutputStatus(id)` there, as above.

**Bookmarking** — opt in on the server (`[py]`
`ReactApp(server, bookmark_store="url")`, `[r]` `enableBookmarking = "url"`
with a per-request UI function) and the client needs no code at all:
restored values seed `useShinyInput` initial values before the first paint.
See [`references/bookmarking.md`](references/bookmarking.md).

**Typed inputs** — `useShinyInput(id, default, { type: "shiny.datetime" })`
appends `:type` to the wire id and routes through Shiny's input handler, so the
server sees a real date-time (`[py]` `input.when()` is a `datetime` /
`[r]` `input$when` is a `POSIXct`) instead of the unix seconds the client sent.
The id/type pairing is a contract: a later mount that disagrees throws.

Untyped values go through shinyreact's own `shinyreact.default` handler, which
keeps R and Python agreeing about the same JSON: `[]` stays empty rather than
becoming `NULL`, and `[[1, 2], [3, 4]]` keeps its nesting. The one deliberate
difference is that `[r]` flattens a scalar array to an atomic vector
(`[0, 100]` → `c(0, 100)`), because that is what R code wants; `[py]` leaves it
a list. Use `type: "shinyreact.asis"` for the parsed value untouched.

## Known pitfalls

- **`defaultValue` is captured on first mount only**, like `useState`. Inline
  `{}` / `[]` are safe — stabilized internally.
- **Inline arrow handlers are safe** for `useShinyMessageHandler` — stored in a
  ref.
- **Input ids are global per page.** Two mounts of one id share state; that is
  the feature (a button writes, a card reads), but disagreeing on `type`
  throws and disagreeing on `priority` warns and last-writer-wins.
- **Inputs arrive asynchronously and independently after mount.** An event
  input with `debounceMs: 0` can reach the server before sibling inputs'
  initial values (which sit on the 100 ms default), so a handler that reads
  them at event time sees `NULL` / `None` on the first flush. Give those
  inputs `debounceMs: 0` too, and keep the initial-0 guard shown above.
- **Terminology**: this is the `ui.tsx` pattern. Never call it an "SPA".

## Verify it

Do not stop at "the code is written". Three steps, in order:

1. **Factor pure logic out of the app file** — binning, formatting,
   conversions go in a module beside the app. Logic inside `app.py` /
   `app.R` next to the page call cannot be reached by a test at all.
2. **Write down what the app does, in plain English, before the tests.** An
   agent that writes the client and then writes the client's tests is
   agreeing with itself — both encode the same misunderstanding. A
   description a human can falsify at a glance is what breaks that loop.
3. **Test against that description**, at the cheapest layer that can see the
   behavior. Tests go in `tests/` beside the app and must run **from the app
   directory** — `pytest`, or `[r]` `shiny::runTests()`, which needs the
   `tests/testthat.R` + `tests/testthat/` layout.

`[r]` `shiny::testServer()` drives the reactive graph with no browser:
`session$setInputs(bins = 9)` then assert on `output$dist_data`, which is the
JSON value the client would have received. **`[py]` has no equivalent**, so
factoring logic into an importable module matters more there.

[`references/testing.md`](references/testing.md) has the four layers, the test
layout for each language, `testServer()` for plain and module servers, how to
mount the real `www/ui.js` against a fake Shiny, and the traps that cost time
(React ignores raw `change` events; debounce coalesces within a tick even at
`debounceMs: 0`).

## Debugging

When something does not work, the four diagnostic hooks
(`useShinyInitialized`, `useShinyOutputStatus`, `useShinyBusy`,
`useShinyInputValue`) and a symptom-to-cause table are in
[`references/debugging.md`](references/debugging.md). The first two entries
cover most of it: every hook returning nothing means two React copies, and
unchanged behavior in the browser means a stale `www/ui.js`.

## Worked examples

[`examples/`](https://github.com/posit-dev/shinyreact/tree/main/examples) is the
reference, each a runnable app: `01-hello` (no-build, SVG chart), `02-columns`
(event inputs), `03`/`04` (Vite + shadcn/ui — start here for a real build),
`06`/`07` (`ShinyOutput` hosting a data frame / plotly widget), `08` (typed
inputs), `09` (Vite HMR against a running Shiny), `10` (bookmarking).

[`01-hello`](https://github.com/posit-dev/shinyreact/tree/main/examples/01-hello)
and
[`07-plotly`](https://github.com/posit-dev/shinyreact/tree/main/examples/07-plotly)
each ship an `app.R` **and** an `app.py` over one shared `www/` client. That is
a demonstration device, not something to copy — a real app has one server — but
reading the two side by side shows how little of an app is language-specific.
