# Material UI for shinyreact

[Material UI](https://mui.com/material-ui/) components wired to Shiny's reactive system through shinyreact. Ships 9 components as a Python package (`shinymui`) and an R package (`shinymui`). Install them, or run straight from a source checkout (`sys.path` for Python, `pkgload::load_all()` for R) with no install.

This is the **npm-library** framework model: MUI is a real npm package, so the bridges in `js/src/components/` import from `@mui/material` (no source copied in). It was built with the `/scaffold-framework` and `/scaffold-component` skills, and is the second framework under `ui-frameworks/` (after `shadcn`).

## Components

| Component | Type | Shiny input value |
|-----------|------|-------------------|
| `button` | Action | click count (integer) |
| `text_field` | Input | current string |
| `slider` | Input | number |
| `switch` | Input | boolean |
| `checkbox` | Input | boolean |
| `select` | Input | selected value (string) |
| `card` | Container | — |
| `alert` | Display | — |
| `dialog` | Overlay | boolean (open state) |

R helpers are the same names prefixed `mui_` (e.g. `mui_button`).

## Build

```bash
cd js
npm install
npm run build       # -> www/mui.js   (MUI styles at runtime via emotion; no CSS file)
```

## Run examples

```bash
# Python (from repo root)
uv run shiny run ui-frameworks/mui/examples/app-py/app.py

# R (from an R console)
shiny::runApp("ui-frameworks/mui/examples/app-r/app.R")
```

## Using in your own app

### Python

```python
import sys
sys.path.insert(0, "path/to/ui-frameworks/mui/pkg-py/src")

import shinymui as mui
import shinyreact
from shiny import App

app_ui = shinyreact.page_react(
    shinyreact.output_react("main", extra_deps=[mui._dep()]),
)

def server(input, output, session):
    @shinyreact.render_react
    def main():
        return mui.card(mui.text_field("name", label="Name"), mui.button("go", "Go"), title="Demo")

app = App(app_ui, server)
```

### R

```r
library(shinyreact)
pkgload::load_all("path/to/ui-frameworks/mui/pkg-r")  # or library(shinymui) once installed

ui <- page_react(output_react("main", extra_deps = list(mui_dep())))

server <- function(input, output, session) {
  output$main <- render_react({
    mui_card(mui_text_field("name", label = "Name"), mui_button("go", "Go"), title = "Demo")
  })
}
shinyApp(ui, server)
```

## Adding a new component

Use `/scaffold-component`. For an npm-library framework like MUI you write a thin bridge in `js/src/components/<name>.jsx` that imports from `@mui/material`, register it in `index.jsx`, then add the Python helper (in `pkg-py/src/shinymui/_<category>.py`, re-exported from `__init__.py`) and the R helper (in `pkg-r/R/<category>.R`, then `roxygen2::roxygenise()`).

## Architecture notes

- **npm-library model** — no source copied; bridges import from `@mui/material`. Emotion (`@emotion/react`/`@emotion/styled`) is MUI's styling engine and is bundled.
- **`react-dom` bundled, not externalized** — MUI's Modal/Select/Popover render through portals (`createPortal`), which `window.shinyreact.ReactDOM` (`react-dom/client`) does not expose. `react`, `react-dom/client`, and `shinyreact` are externalized to the host.
- **No CSS file** — MUI injects styles at runtime via emotion, so the dependency ships only `mui.js`.
- **No Tailwind/Bootstrap compat layer** — unlike shadcn, MUI doesn't use Tailwind utilities, so there's no `styles.css`. Bootstrap/MUI interop quirks, if they surface, would be handled per-component or via an MUI theme.
