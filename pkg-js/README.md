# @posit-dev/shinyreact

<!-- badges: start -->

[![check-js](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml)
[![npm](https://img.shields.io/npm/v/@posit-dev/shinyreact)](https://www.npmjs.com/package/@posit-dev/shinyreact)
<!-- badges: end -->

React hooks and components for [Shiny](https://shiny.posit.co/). The Shiny server — [Python](https://posit-dev.github.io/shinyreact/py/) or [R](https://posit-dev.github.io/shinyreact/r/) — contains only reactive computation, and the UI is a React client you own. This package is the bridge, and it ships zero UI components: no buttons, no layout, no theme. You bring the component library.

One React client works against an `app.py` or an `app.R` server unchanged. The [full site](https://posit-dev.github.io/shinyreact/) covers all three packages.

## Do you need this package?

Only if you use a bundler. shinyreact apps come in two tiers:

- **No build step** — the server serves the same runtime as an IIFE and the client reads it off `window.shinyreact`. Nothing to install; you can stop reading.
- **Bundler** (Vite, esbuild, webpack) — `npm install` this package and `import` the hooks. You get types, tree-shaking, a development React with Fast Refresh, and your own dependency graph.

Both tiers are built from the same source and speak the same protocol version.

## Installation

```bash
npm install @posit-dev/shinyreact react react-dom
```

React 19 is a peer dependency, resolved by your bundler.

Then tell the page entry point that the client brings its own copy, so the server does not also serve the IIFE:

```python
set_react_page(shinyreact_js="client")   # or page_react(), page_react_html(), ReactApp()
```

```r
page_react(shinyreact_js = "client")
```

Skip that and the app still works — the registries are page-scoped, so both copies share one set of inputs, outputs, and message handlers — but the page downloads and parses a second React for nothing. The bundle logs a `console.warn` when it detects this.

## Usage

```jsx
import { useShinyInput, useShinyOutputValue } from "@posit-dev/shinyreact";
import "@posit-dev/shinyreact/styles";
import { createRoot } from "react-dom/client";

function App() {
  const [name, setName] = useShinyInput("name", "world");
  const greeting = useShinyOutputValue("greeting");

  return (
    <div>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <p>{greeting}</p>
    </div>
  );
}

// The page entry points emit no mount container, so make one.
createRoot(document.body.appendChild(document.createElement("div"))).render(
  <App />,
);
```

`useShinyInput` writes to `input.name()` / `input$name` on the server; `useShinyOutputValue` reads whatever the matching `reactive_output` returned:

```python
@reactive_output
def greeting():
    return f"Hello, {input.name()}!"
```

```r
output$greeting <- reactive_output({
  paste0("Hello, ", input$name, "!")
})
```

The `"./styles"` export is only needed for components that ship CSS (`ImageOutput`'s placeholder spinner); the hooks have no styles of their own.

## API

|                |                                                                        |
| -------------- | ---------------------------------------------------------------------- |
| **Inputs**     | `useShinyInput` · `useShinyInputValue` · `useSetShinyInput`            |
| **Outputs**    | `useShinyOutputValue` · `useShinyOutputStatus` · `useShinyOutputError` |
| **Messaging**  | `useShinyMessageHandler`                                               |
| **Session**    | `useShinyInitialized` · `useShinyBusy`                                 |
| **Components** | `ShinyOutput` · `ImageOutput` · `ShinyModuleProvider`                  |
| **Utilities**  | `MISSING` · `PROTOCOL_VERSION`                                         |

Pick the narrowest hook that fits the call site: a button that pushes events but never reads its own state wants `useSetShinyInput`, not `useShinyInput` with a discarded value.

`ShinyOutput` renders a traditional Shiny output element — a `shiny-data-frame`, a plotly widget — inside a React tree, and handles binding for you.

Full signatures and types: [JS API reference](https://posit-dev.github.io/shinyreact/js/).

## Try it

```bash
git clone https://github.com/posit-dev/shinyreact
cd shinyreact/examples/11-npm-local
shiny run app.py                 # builds the client bundle on first run
```

## Learn more

- [Get started](https://posit-dev.github.io/shinyreact/) walks through the `ui.tsx` pattern: inputs, outputs, messages, and embedding traditional Shiny renderers.
- [TSX files and JavaScript build tools](https://posit-dev.github.io/shinyreact/articles/tsx-and-build-tools.html) explains `.tsx`, JSX, TypeScript, and what `npm run build` does.
- [Client hooks](https://posit-dev.github.io/shinyreact/articles/hooks.html) documents every hook in detail.
- The [examples catalog](https://github.com/posit-dev/shinyreact/blob/main/examples/README.md) lists runnable apps from no-build to Vite + HMR.

## License

MIT © Posit Software, PBC
