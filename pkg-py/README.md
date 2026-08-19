# shinyreact (Python)

<!-- badges: start -->
[![check-py](https://github.com/posit-dev/shinyreact/actions/workflows/check-py.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-py.yaml)
[![check-js](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml)
<!-- badges: end -->

React UI infrastructure for [Shiny for Python](https://shiny.posit.co/py/). The Shiny server contains only reactive computation; the UI is a React client you own. `shinyreact` provides the bridge — it ships zero UI components itself.

This is the Python package. See the [repo root](https://github.com/posit-dev/shinyreact) for the language-agnostic overview and the R package.

## Installation

`shinyreact` is pre-release and not yet on PyPI. Install from GitHub:

```bash
pip install "git+https://github.com/posit-dev/shinyreact.git"
```

## How it works

`shinyreact` implements the **`ui.tsx` pattern** — UI defined in a client codebase whose entry conventionally lives in `ui.tsx` (or `App.jsx`, or `app.js` for no-build):

1. The Python server contains only reactive computation; it calls `set_react_page()` (Express) or uses `page_react_html()` as the `ui` argument (Core)
2. A static `www/index.html` + client bundle serve as the React app
3. Client and server communicate via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler` hooks

## Usage

```python
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def greeting():
    return {"message": f"Hello, {input.name()}"}
```

Pair with a `www/index.html` that loads your React client (no-build `app.js` or a built bundle from `src/ui.tsx`). See the [examples catalog](../examples/README.md) for file layouts and dev workflows, from no-build to Vite + HMR.

In Core mode, use `page_react_html()`. Core apps must also mount `www/`
themselves — Shiny Express does this automatically, `App()` does not, and
without it the page loads and then 404s on its own scripts and stylesheets:

```python
from pathlib import Path
from shiny import App
import shinyreact

app = App(
    shinyreact.page_react_html("www/index.html"),
    server,
    static_assets={"/": Path(__file__).parent / "www"},
)
```

### Sending messages to React components

Use `send_message` to push data from the server to client-side React hooks:

```python
@reactive.effect
async def notify():
    await shinyreact.send_message(
        session, "notification", {"text": "Done!", "level": "info"}
    )
```

On the JS side, consume with `useShinyMessageHandler("notification", handler)`.

## Examples

Runnable apps live in [`examples/`](../examples/) — see the
[examples catalog](../examples/README.md) for the full list.

## JS hooks available via `window.shinyreact`

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, default, opts)` | Read/write a Shiny input — full `[value, setValue]` |
| `useShinyInputValue(id)` | Read-only consumer for an input that another component produces |
| `useSetShinyInput(id, default, opts)` | Write-only producer — registers an input and returns just the setter |
| `useShinyOutputValue(id, default?)` | Consume arbitrary data sent by `@shinyreact.reactive_output` |
| `useShinyOutputStatus(id)` | Output lifecycle status — `"pending" \| "ready" \| "recalculating" \| "error"` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |
| `useShinyBusy()` | Whether the Shiny server is currently processing a request |

Shared `React` and `ReactDOM` instances are available at `window.shinyreact.React` / `window.shinyreact.ReactDOM` — externalize to these in your build to avoid duplicate React.
