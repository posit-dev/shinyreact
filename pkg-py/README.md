# shinyreact (Python)

JSON-driven React rendering infrastructure for [Shiny for Python](https://shiny.posit.co/py/). `shinyreact` provides the plumbing that lets downstream packages (like `shinyshadcn`) deliver React component trees from Python — it ships zero UI components itself.

This is the Python package. See the [repo root](https://github.com/posit-dev/shinyreact) for the language-agnostic overview and the R package.

## Installation

`shinyreact` is pre-release and not yet on PyPI. Install from GitHub:

```bash
pip install "git+https://github.com/posit-dev/shinyreact.git"
```

## How it works

`shinyreact` ships two first-class patterns:

**`app.py` pattern** — UI defined as Python objects in the Shiny app file:
1. Server code builds a **Spec** — a flat map of elements with a root ID
2. `shinyreact` serializes the Spec as JSON and sends it to the browser via a Shiny output binding
3. The JS bundle renders the JSON into a live React component tree
4. Downstream packages register their own React components so the renderer resolves `type` strings like `"Card"` or `"Button"`

**`ui.tsx` pattern** — UI defined in a client codebase whose entry conventionally lives in `ui.tsx` (or `App.jsx`, or `app.js` for no-build):
1. The Python server contains only reactive computation; it calls `set_react_page()`
2. A static `www/index.html` + client bundle serve as the React app
3. Client and server communicate via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler` hooks

## Usage

### `app.py` pattern

```python
from shiny import App, ui
import shinyreact

app_ui = shinyreact.page_react(
    shinyreact.output_react("greeting"),
)

def server(input, output, session):
    @shinyreact.render_react
    def greeting():
        return shinyreact.Spec(
            root="card",
            elements={
                "card": shinyreact.Element(
                    type="Card",
                    props={"title": "Hello from shinyreact"},
                ),
            },
        )

app = App(app_ui, server)
```

`@shinyreact.render_react` walks a `Spec` / `Node` / htmltools content into the JSON wire tree and renders it into the matching `output_react()` placeholder. To send raw JSON-serializable data (dicts, lists, etc.) for `useShinyOutputValue()` hooks instead — with no placeholder — use `@shinyreact.reactive_output` (the `ui.tsx` pattern below).

### `ui.tsx` pattern

```python
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()

@reactive_output
def greeting():
    return {"message": f"Hello, {input.name()}"}
```

Pair with a `www/index.html` that loads your React client (no-build `app.js` or a built bundle from `src/ui.tsx`). See [`docs/app-py-vs-ui-tsx.md`](../docs/app-py-vs-ui-tsx.md) for the file layout and dev workflow.

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

## Extending shinyreact (package authors)

`shinyreact` is designed to be extended by downstream packages that supply their own React components. Three parts:

### 1. JS bundle — register components

```js
const { registerComponents } = window.shinyreact;

const catalog = { Button, Card, Dialog /* ... */ };
const registry = (type) => catalog[type] ?? null;

registerComponents(catalog, registry);
```

### 2. Python UI — inject your HTMLDependency

```python
shinyreact.output_react("my_output", extra_deps=[my_html_dependency()])
```

### 3. Python render subclass

```python
class render(shinyreact.render_react):
    async def transform(self, value: MyComponent) -> Any:
        return value.to_spec().to_dict()
```

Inject your package's `HTMLDependency` on the UI side via `shinyreact.output_react(id, extra_deps=[...])` (see step 2) — `render_react` does not read an `extra_deps` class attribute.

### JS hooks available via `window.shinyreact`

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

## Also in this wheel

The `shinyreact` wheel also ships two experimental prototypes — `shinyui` and `shinyuiclassonly` — that explore a class-per-component UI hierarchy. They are not part of the supported API; see the [repo](https://github.com/posit-dev/shinyreact) for details.
