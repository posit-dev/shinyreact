# shinyreact <img src="logo/shiny-react.png" align="right" height="138" alt="shinyreact logo" />

JSON-driven React rendering infrastructure for [Shiny](https://shiny.posit.co/). `shinyreact` provides the plumbing that lets downstream packages (like `shinyshadcn`) deliver React component trees from **Python or R** — it ships zero UI components itself.

One JSON wire format and one JavaScript bundle back both languages, so a React component registered once renders identically from `app.py` and `app.R`.

This repo ships per-language packages:

| Language | Source | Landing page |
|---|---|---|
| Python | [`pkg-py/`](pkg-py/) | [`pkg-py/README.md`](pkg-py/README.md) |
| R | [`pkg-r/`](pkg-r/) | [`pkg-r/README.md`](pkg-r/README.md) · [pkgdown](https://posit-dev.github.io/shinyreact/r) |

Not sure whether to use the `app.py`/`app.R` pattern or the `ui.tsx` pattern? See [`docs/app-py-vs-ui-tsx.md`](docs/app-py-vs-ui-tsx.md).

## How it works

`shinyreact` ships two first-class patterns, both available in Python and R:

**`app.py` / `app.R` pattern** — UI defined as Python or R objects in the Shiny app file:
1. Server code builds a component tree — a `Spec` of `Element`s in Python, a `node()` tree in R (which may interleave htmltools tags)
2. `shinyreact` serializes the tree as JSON and sends it to the browser via a Shiny output binding
3. The JS bundle renders the JSON into a live React component tree
4. Downstream packages register their own React components so the renderer can resolve `type` strings like `"Card"` or `"Button"`

**`ui.tsx` pattern** — UI defined in a client codebase whose entry conventionally lives in `ui.tsx` (or `App.jsx`, or `app.js` for no-build):
1. The Shiny server contains only reactive computation; it bootstraps a static page — `set_react_page()` in Python, `page_react_html()` in R
2. A static `www/index.html` plus your React client serve the UI
3. Client and server communicate via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler` hooks

See each package's README for runnable code, and [`examples/`](examples/) for working apps in both languages and both patterns.

## Extending shinyreact (package authors)

Downstream packages supply their own React components. The pattern has two halves:

### 1. JS bundle — register components

Build your own IIFE that calls `registerComponents` at load time:

```js
const { registerComponents } = window.shinyreact;

const catalog = { Button, Card, Dialog /* ... */ };
const registry = (type) => catalog[type] ?? null;

registerComponents(catalog, registry);
```

### 2. Server — render your components + inject your dependency

**Python** — subclass `reactive_output` and inject your `HTMLDependency` on the UI side:

```python
class render(shinyreact.reactive_output):
    async def transform(self, value: MyComponent) -> Any:
        return value.to_spec().to_dict()

shinyreact.ui_output("my_output", extra_deps=[my_html_dependency()])
```

**R** — build `node("YourComponent", ...)` trees and inject your `htmlDependency` via `ui_output_react()`:

```r
ui_output_react("my_output", extra_deps = list(my_html_dependency()))
```

### JS hooks available via `window.shinyreact`

Downstream component authors can use these re-exported hooks from `@posit/shiny-react`:

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, default, opts)` | Read/write a Shiny input — full `[value, setValue]` |
| `useShinyInputValue(id)` | Read-only consumer for an input that another component produces |
| `useSetShinyInput(id, default, opts)` | Write-only producer — registers an input and returns just the setter |
| `useShinyOutputValue(id, default?)` | Consume arbitrary data sent by the server renderer |
| `useShinyOutputStatus(id)` | Output lifecycle status — `"pending" \| "ready" \| "recalculating" \| "error"` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |
| `useShinyBusy()` | Whether the Shiny server is currently processing a request |

Shared `React` and `ReactDOM` instances are also available at `window.shinyreact.React` / `window.shinyreact.ReactDOM` — externalize to these in your build to avoid duplicate React.

## Architecture

- **JS bundle** (`js/dist/shinyreact.js`): Self-contained IIFE bundling React 19 and vendored `@posit/shiny-react`. Registers a Shiny `OutputBinding` for `.shinyreact-output` elements. Shared by both language packages.
- **Python package** (`pkg-py/`): `Spec` / `Element` / `Node` data model, `reactive_output` decorator, `ui_output()` + `page_react()` helpers, `set_react_page()` for the `ui.tsx` pattern, and `send_message()` for server-to-client communication.
- **R package** (`pkg-r/`): `node()` tree data model, `render_react()` renderer, `ui_output_react()` + `page_react()` helpers, `page_react_html()` for the `ui.tsx` pattern, and `send_message()`. Same wire format and JS bundle as Python.

## Development

### Setup

```bash
make setup
```

This installs Python dependencies (`uv sync`), JS dependencies (`npm install`), and pre-commit hooks.

### Common commands

```bash
make update-dist       # Build JS + copy to pkg-py/www/ and pkg-r/inst/lib/
make py-check          # Format check + type check + tests
make py-check-tox      # Full matrix: Python 3.10-3.14
make r-check           # R format + tests + R CMD check
make js-build-watch    # JS watch mode
```

Run `make help` to see all targets.
