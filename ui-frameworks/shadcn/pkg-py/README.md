# shinyshadcn (Python)

Python helpers for the shadcn/ui component library on [shinyreact](https://github.com/posit-dev/shinyreact). Each helper returns a `shinyreact.Node` that renders a registered shadcn component.

```python
import shinyshadcn as sc
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    shinyreact.output_react("main", extra_deps=[sc._dep()]),
)

def server(input, output, session):
    @shinyreact.render_react
    def main():
        return sc.card(sc.button("go", "Go"), title="Demo")

app = App(app_ui, server)
```

`sc._dep()` provides the bundled JS/CSS as an `HTMLDependency`. The component catalog and reactive-input contracts are documented in the [package README](../README.md).

## Build

```bash
uv build        # wheel + sdist; bundles the shared ../www assets
```
