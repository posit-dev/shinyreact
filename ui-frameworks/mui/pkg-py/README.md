# shinymui (Python)

Python helpers for the Material UI component library on [shinyreact](https://github.com/posit-dev/shinyreact). Each helper returns a `shinyreact.Node` that renders a registered MUI component.

```python
import shinymui as mui
import shinyreact
from shiny import App

app_ui = shinyreact.page_react(
    shinyreact.output_react("main", extra_deps=[mui._dep()]),
)

def server(input, output, session):
    @shinyreact.render_react
    def main():
        return mui.card(mui.button("go", "Go"), title="Demo")

app = App(app_ui, server)
```

`mui._dep()` provides the bundled JS as an `HTMLDependency` (MUI styles itself at runtime via emotion, so there is no separate CSS file). See the [package README](../README.md) for the component list.

## Build

```bash
uv build        # wheel + sdist; bundles the shared ../www/mui.js
```
