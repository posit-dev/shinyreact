# shinyreact

JSON-driven React rendering infrastructure for [Shiny](https://shiny.posit.co/py/). `shinyreact` provides the plumbing that lets downstream packages (like `shinyshadcn`) deliver React component trees from Python — it ships zero UI components itself.

Not sure whether to use the traditional pattern or the SPA pattern? See [`docs/spa-vs-traditional.md`](docs/spa-vs-traditional.md).

## How it works

`shinyreact` ships two first-class patterns:

**Traditional pattern** — server describes UI as a JSON spec:
1. Python server code builds a **Spec** — a flat map of elements with a root ID
2. `shinyreact` serializes the Spec as JSON and sends it to the browser via a Shiny output binding
3. The JS bundle renders the JSON into a live React component tree
4. Downstream packages register their own React components so the renderer knows how to resolve `type` strings like `"Card"` or `"Button"`

**SPA pattern** — client owns the UI:
1. Python server contains only reactive computation (no UI definitions)
2. A static `www/index.html` + `www/app.js` serve as the React client
3. Client and server communicate via `useShinyInput` / `useShinyOutput` / `useShinyMessageHandler` hooks

## Installation

```bash
pip install shinyreact
```

## Usage

### Traditional pattern

```python
from shiny import App, ui
import shinyreact

app_ui = shinyreact.page_react(
    shinyreact.ui_output("greeting"),
)

def server(input, output, session):
    @shinyreact.reactive_output
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

`@shinyreact.reactive_output` also accepts raw JSON-serializable values (dicts, lists, etc.) for use with `useShinyOutput()` hooks on the React side.

### SPA pattern

```python
import shinyreact

def server(input, output, session):
    @shinyreact.reactive_output
    def greeting():
        return {"message": f"Hello, {input.name()}"}

app = shinyreact.ReactApp(server)
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

## Extending shinyreact (package authors)

`shinyreact` is designed to be extended by downstream packages that supply their own React components. The pattern has three parts:

### 1. JS bundle — register components

Build your own IIFE that calls `registerComponents` at load time:

```js
const { registerComponents } = window.shinyreact;

const catalog = { Button, Card, Dialog /* ... */ };
const registry = (type) => catalog[type] ?? null;

registerComponents(catalog, registry);
```

### 2. Python UI — inject your HTMLDependency

```python
shinyreact.ui_output("my_output", extra_deps=[my_html_dependency()])
```

### 3. Python render subclass

```python
class render(shinyreact.reactive_output):
    async def transform(self, value: MyComponent) -> Any:
        return value.to_spec().to_dict()
```

Inject your package's `HTMLDependency` on the UI side via `shinyreact.ui_output(id, extra_deps=[...])` (see step 2).

### JS hooks available via `window.shinyreact`

Downstream component authors can use these re-exported hooks from `@posit/shiny-react`:

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, opts)` | Read/write a Shiny input from React |
| `useShinyOutput(id)` | Consume arbitrary data sent by `@shinyreact.reactive_output` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |

Shared `React` and `ReactDOM` instances are also available at `window.shinyreact.React` / `window.shinyreact.ReactDOM` — externalize to these in your build to avoid duplicate React.

## Architecture

- **JS bundle** (`js/dist/shinyreact.js`): Self-contained IIFE bundling React 19 and vendored `@posit/shiny-react`. Registers a Shiny `OutputBinding` for `.shinyreact-output` elements.
- **Python package** (`pkg-py/`): `Spec` / `Element` / `Node` data model, `reactive_output` decorator, `ui_output()` + `page_react()` helpers, `ReactApp` wrapper, and `send_message()` for server-to-client communication.
- **R package** (`pkg-r/`): Placeholder — not yet implemented.

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
