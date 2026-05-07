# `client-ui` vs `ui-object`: Choosing a `shinyreact` App Pattern

`shinyreact` ships two first-class app patterns. Both are valid Shiny apps. The difference is *where the UI is defined* and *what travels over the websocket*. This page explains the distinction and helps you decide which pattern fits your app.

The naming is borrowed from [Shiny's "Build your entire UI with HTML"](https://shiny.posit.co/r/articles/build/html-ui/) framing. Shiny describes the same architectural split as **UI object** vs **HTML UI**; in `shinyreact` the two patterns are **`ui-object`** and **`client-ui`**.

---

## 1. Framing — what's actually different

Shiny has always supported two app shapes:

- **UI defined as an object in the app file** — `app.py` (or `app.R`) builds the UI as a Python/R object (`ui.page_fluid(...)`, or `shinyreact.page_react(...)`) alongside the server logic. The server ships rendered HTML (and matched JS) over the websocket and patches it into the page.
- **UI defined in a client codebase** — a static `www/index.html` is the entry point; the app file is server-only. Core Shiny supports this today with raw HTML; `shinyreact` extends it with React.

`shinyreact` adopts the second shape but changes *what crosses the websocket*. Instead of fully-formed DOM fragments plus JavaScript, the server sends **only JSON data**. The UI logic — which component to render, how to lay it out, how interaction maps to state — lives entirely in the client (`www/index.html` + `www/app.js` or a Vite-built `www/index.tsx`). This is the novel piece: not the file layout, but the shift of UI authorship to the client.

Both patterns coexist in `shinyreact`. A `client-ui` app can be one piece of a larger system; the `ui-object` pattern continues to work exactly as before.

---

## 2. Side-by-side file layout

### `ui-object` pattern

```
my-app/
  app.py            # UI defined in Python + server logic
```

A minimal example:

```python
# app.py (ui-object)
from shiny import App, ui
import shinyreact

app_ui = shinyreact.page_react(
    shinyreact.ui_output("my_output"),
)

def server(input, output, session):
    @shinyreact.reactive_output
    def my_output():
        return shinyreact.Spec(
            root="card",
            elements={"card": shinyreact.Element(type="Card", props={"title": "Hello"})},
        )

app = App(app_ui, server)
```

See a complete example: [`examples/ui-object/01-hello-world/`](../examples/ui-object/01-hello-world/)

For a richer `ui-object` app with drag-and-drop columns: [`examples/ui-object/10-columns/`](../examples/ui-object/10-columns/)

### `client-ui` pattern

```
my-app/
  app.py            # Server logic only — no UI definitions
  www/
    index.html      # Static entry point
    app.js          # React client (hand-written or Vite-built from src/index.tsx)
```

A minimal example:

```python
# app.py (client-ui — Shiny Express)
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()

@reactive_output
def greeting():
    return {"message": f"Hello, {input.name()}"}
```

`set_react_page()` configures the Express app to serve `www/index.html` as the page body and auto-discovers `HTMLDependency` objects from any traditional Shiny renderers in the module.

```js
// www/app.js
const { useShinyOutput } = window.shinyreact;
function App() {
    const data = useShinyOutput("greeting");
    return React.createElement("p", null, data?.message ?? "...");
}
```

See a complete example: [`examples/client-ui/01-hello/`](../examples/client-ui/01-hello/)

For the same drag-and-drop columns demo in `client-ui` style: [`examples/client-ui/02-columns/`](../examples/client-ui/02-columns/)

---

## 3. What goes over the websocket

| Direction | `ui-object` | `client-ui` |
|-----------|-------------|-------------|
| Client → Server | Input values via standard Shiny inputs | Input values via `useShinyInput(id, default)` |
| Server → Client | HTML/JS output fragments (`render.ui`, output bindings producing markup) | Pure JSON data via `@reactive_output`; client decides how to render |
| Server → Client (push) | `send_message()` custom messages | `send_message()` consumed by `useShinyMessageHandler` |

In the `ui-object` pattern, the server both computes data *and* decides how to present it — the output binding ships pre-built HTML. In the `client-ui` pattern, the server sends only the data; the React client decides what to render and how.

Implications for the `client-ui` pattern:
- Smaller, structured payloads — no markup in the wire format
- The wire format is inspectable JSON (useful for debugging and AI tooling)
- The client can re-render without a server round-trip
- No server-driven DOM patching

---

## 4. Two output paradigms within a `client-ui` app

Within a `client-ui` app, there are two ways to ship server-side output to the page. Both are valid and they coexist in the same app.

| | `@reactive_output` + `useShinyOutput` | `@render.<x>` + `<ShinyOutput>` |
|---|---|---|
| Wire payload | Pure data (JSON) | Whatever the binding sends — often pre-rendered HTML or widget state |
| UI ownership | React | The traditional Shiny output binding |
| Best for | Custom UI built from data: dashboards, custom plots, tables built from rows | Existing widgets: `@render.data_frame`, `@render_plotly`/`@render_widget`, htmlwidgets, third-party output bindings |

**Prefer `@reactive_output` + client rendering when possible** — that's the principle the `client-ui` pattern is built on (server owns data, client owns UI; minimal data over the wire). But the existing Shiny widget ecosystem is large and battle-tested, and rewriting widgets like `@render.data_frame` or `@render_plotly` as React components would be a major undertaking. `<ShinyOutput>` is the legitimate path for embedding those widgets without rewriting them:

```js
// www/app.js
const { ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
    return h("div", null,
        // Custom UI rendered by React from JSON data
        h(MyChart, { data: useShinyOutput("chart_data") }),
        // Existing data-frame binding owns this subtree
        h(ShinyOutput, { id: "my_table", tagName: "shiny-data-frame" }),
        // Plotly via shinywidgets
        h(ShinyOutput, { id: "scatter", className: "shiny-ipywidget-output shiny-report-size" }),
    );
}
```

`set_react_page()` automatically discovers the `HTMLDependency` objects each `@render.<x>` needs and injects them into the page — no manual dep wiring.

See [`examples/client-ui/06-data-frame/`](../examples/client-ui/06-data-frame/) and [`examples/client-ui/07-plotly/`](../examples/client-ui/07-plotly/) for working examples.

---

## 5. Dev workflow

### `ui-object`

1. Edit `app.py` (UI and server logic together)
2. Reload the app
3. No JS toolchain required

### `client-ui` — no-build path

1. Edit `app.py` (server logic) and `www/app.js` (React client using `React.createElement`)
2. Reload the app
3. Still no JS toolchain required

See [`examples/client-ui/01-hello/`](../examples/client-ui/01-hello/) and [`examples/client-ui/02-columns/`](../examples/client-ui/02-columns/) for the no-build path.

### `client-ui` — JSX + Vite path

1. Edit `app.py` and `src/index.tsx` (or `App.jsx`)
2. Run `npm run build` (or `make watch`) to bundle `src/` → `www/`
3. Reload the app

The Vite build externalizes React to `window.shinyreact`, so the bundled client shares the same React instance as the `shinyreact` bridge hooks.

See [`examples/client-ui/03-columns-shadcn/`](../examples/client-ui/03-columns-shadcn/) and [`examples/client-ui/04-shadcn/`](../examples/client-ui/04-shadcn/) for the Vite path.

---

## 6. Tradeoffs

### `ui-object` strengths

- Zero JS required — define the full UI in Python (or R)
- Terse for forms, reports, and dashboards with mostly static layout
- Mature Shiny ecosystem: `render.ui`, `ui.input_*`, `ui.output_*` all work as-is
- Server-side rendering on first paint — the HTML is ready before the websocket connects

### `ui-object` weaknesses

- Dynamic UI (drag-and-drop, sortable lists, per-item controls) requires observer-lifecycle bookkeeping: generated IDs, observer creation/destruction, race conditions
- Every interaction that changes UI is a server round-trip — even purely visual changes
- UI and data are tightly coupled in `render.ui`, making it hard to separate presentation from logic

### `client-ui` strengths

- Client owns UI state — no observer churn for drag/sort/filter operations
- Lower-latency interactions: client-side state changes happen instantly, server is involved only when it has something the client doesn't
- Full React ecosystem: any component library (shadcn/ui, Tailwind, Recharts, etc.) works without framework support
- The wire format is pure data — easier to inspect, test, and reason about
- AI-friendly: the client is a standard React app that AI can generate and modify reliably

### `client-ui` weaknesses

- Requires reading/writing React (or trusting an AI to generate it)
- Introduces a client/server split to reason about: two files, two execution contexts
- More moving parts for trivial apps (a simple label change needs both a server update and a client render)
- No built-in Shiny UI helpers on the client side — layout, inputs, and outputs are all your React code

---

## 7. "Pick this if…" guidance

**Choose the `ui-object` pattern if:**
- Your app is primarily forms, reports, or dashboards with mostly static layout
- Your team has no JS experience and doesn't want to write any
- You want to use the full Shiny input/output ecosystem (`ui.input_slider`, `render.table`, etc.)
- You're building a quick prototype and want the fastest path to a working app

**Choose the `client-ui` pattern if:**
- Your app has rich client-side interactivity: drag-and-drop, live filtering, custom animations
- You want to use shadcn/ui, Tailwind, or another modern React component library
- Client responsiveness matters — you want interactions to feel instant, not dependent on a server round-trip
- You want the wire format to be inspectable data, not markup
- You're building an app that AI will generate or maintain — the `client-ui` pattern gives AI a clear React target

---

## 8. Migration note

The two patterns coexist in `shinyreact`. You do not have to choose one for your entire codebase:

- A `client-ui` app serves one Python (or R) module alongside one React client — but that module can still use `reactive.value`, `reactive.calc`, `@reactive.effect`, and all standard Shiny reactive primitives.
- Within a `client-ui` app, you can mix `@reactive_output` + `useShinyOutput` with traditional `@render.<x>` + `<ShinyOutput>` (see section 4).
- You can run a `ui-object` `shinyreact` app today and migrate individual output slots to the `client-ui` pattern incrementally.
- There is no deprecation of the `ui-object` pattern. Both are first-class in `shinyreact`.

For the R package (not yet implemented), the same two patterns will apply — the client side is language-agnostic React.
