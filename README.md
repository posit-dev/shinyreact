# shinyjson

JSON-driven React rendering infrastructure for [Shiny](https://shiny.posit.co/py/). shinyjson provides the plumbing that lets downstream packages (like `shinyshadcn`) deliver React component trees from Python — it ships zero UI components itself.

Not sure whether to use the traditional pattern or the SPA pattern? See [`docs/spa-vs-traditional.md`](docs/spa-vs-traditional.md).

## How it works

1. Python server code builds a **Spec** — a flat map of elements with a root ID
2. shinyjson serializes the Spec as JSON and sends it to the browser via a Shiny output binding
3. The JS bundle renders the JSON into a live React component tree using [`@json-render/react`](https://github.com/vercel-labs/json-render)
4. Downstream packages register their own React components so the renderer knows how to resolve `type` strings like `"Card"` or `"Button"`

## Installation

```bash
pip install shinyjson
```

## Usage

### Python (app developer)

```python
from shiny import App, ui
import shinyjson

app_ui = ui.page_fillable(
    shinyjson.ui("greeting"),
)

def server(input, output, session):
    @shinyjson.render
    def greeting():
        return shinyjson.Spec(
            root="card",
            elements={
                "card": shinyjson.Element(
                    type="Card",
                    props={"title": "Hello from shinyjson"},
                ),
            },
        )

app = App(app_ui, server)
```

`shinyjson.render` also accepts raw JSON-serializable values (dicts, lists, etc.) for use with `useShinyOutput()` hooks on the React side.

### Sending messages to React components

Use `post_message` to push data from the server to client-side React hooks:

```python
@reactive.effect
async def notify():
    await shinyjson.post_message(
        session, "notification", {"text": "Done!", "level": "info"}
    )
```

On the JS side, consume with `useShinyMessageHandler("notification", handler)`.

## Extending shinyjson (package authors)

shinyjson is designed to be extended by downstream packages that supply their own React components. The pattern has three parts:

### 1. JS bundle — register components

Build your own IIFE that calls `registerComponents` at load time:

```js
const { registerComponents } = window.shinyjson;

const catalog = { Button, Card, Dialog /* ... */ };
const registry = (type) => catalog[type] ?? null;

registerComponents(catalog, registry);
```

### 2. Python UI — inject your HTMLDependency

```python
shinyjson.ui("my_output", extra_deps=[my_html_dependency()])
```

### 3. Python render subclass

```python
class render(shinyjson.render):
    extra_deps = [my_html_dependency()]

    async def transform(self, value: MyComponent) -> Any:
        return value.to_spec().to_dict()
```

### JS hooks available via `window.shinyjson`

Downstream component authors can use these re-exported hooks from `@posit/shiny-react`:

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, opts)` | Read/write a Shiny input from React |
| `useShinyOutput(id)` | Consume arbitrary data sent by `@shinyjson.render` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |

Shared `React` and `ReactDOM` instances are also available at `window.shinyjson.React` / `window.shinyjson.ReactDOM` — externalize to these in your build to avoid duplicate React.

## Architecture

- **JS bundle** (`js/dist/shinyjson.js`): Self-contained IIFE bundling React 19, `@json-render/react`, and vendored `@posit/shiny-react`. Registers a Shiny `OutputBinding` for `.shinyjson-output` elements.
- **Python package** (`pkg-py/`): `Spec` / `Element` data model, `render` decorator (a `Renderer[Any]` subclass), `ui()` output helper, and `post_message()` for server-to-client communication.
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
