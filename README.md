# shinyreact <img src="logo/shiny-react.png" align="right" height="138" alt="shinyreact logo" />

React UI infrastructure for [Shiny](https://shiny.posit.co/). With `shinyreact`, the Shiny server (**Python or R**) contains only reactive computation, and the UI is a React client you own — `shinyreact` provides the bridge between the two and ships zero UI components itself.

One JavaScript bundle backs both languages, so the same React client works identically against an `app.py` or `app.R` server.

This repo ships per-language packages:

| Language | Source | Landing page |
|---|---|---|
| Python | [`pkg-py/`](pkg-py/) | [`pkg-py/README.md`](pkg-py/README.md) |
| R | [`pkg-r/`](pkg-r/) | [`pkg-r/README.md`](pkg-r/README.md) · [pkgdown](https://posit-dev.github.io/shinyreact/r) |

## How it works

`shinyreact` implements the **`ui.tsx` pattern**: UI defined in a client codebase whose entry conventionally lives in `ui.tsx` (or `App.jsx`, or `app.js` for no-build):

1. The Shiny server contains only reactive computation; it bootstraps a static page — `set_react_page()` (Express) or `page_react_html()` (Core) in Python, `page_react_html()` in R
2. A static `www/index.html` plus your React client serve the UI
3. Client and server communicate via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler` hooks; the server publishes data with `reactive_output` and pushes messages with `send_message()`

See each package's README for runnable code, and [`examples/`](examples/) for working apps.

## JS hooks available via `window.shinyreact`

The bundle re-exports these hooks from `@posit/shiny-react`:

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, default, opts)` | Read/write a Shiny input — full `[value, setValue]` |
| `useShinyInputValue(id)` | Read-only consumer for an input that another component produces |
| `useSetShinyInput(id, default, opts)` | Write-only producer — registers an input and returns just the setter |
| `useShinyOutputValue(id, default?)` | Consume arbitrary data sent by `reactive_output` |
| `useShinyOutputStatus(id)` | Output lifecycle status — `"pending" \| "ready" \| "recalculating" \| "error"` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |
| `useShinyBusy()` | Whether the Shiny server is currently processing a request |

`ImageOutput`, `ShinyModuleProvider`, and `ShinyOutput` components are exposed the same way. Shared `React` and `ReactDOM` instances are available at `window.shinyreact.React` / `window.shinyreact.ReactDOM` — externalize to these in your build to avoid duplicate React.

## Architecture

- **JS bundle** (`pkg-js/dist/shinyreact.js`): Self-contained IIFE bundling React 19 and vendored `@posit/shiny-react`, exposing the hook API at `window.shinyreact`. Shared by both language packages.
- **Python package** (`pkg-py/`): `set_react_page()` / `page_react_html()` page entry points, the `reactive_output` renderer, `send_message()`, built-in input handlers, and bookmark restore support.
- **R package** (`pkg-r/`): `page_react_html()`, `reactive_output()`, `send_message()`, the same input handlers and bookmark support. Same JS bundle as Python.

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
