# shadcn for shinyreact

shadcn/ui components wired to Shiny's reactive system via shinyreact. Ships 47 components, a Python helper package, and an R helper file. Usable from both `app.py` and `app.R` today without any installation — just `sys.path.insert` (Python) or `source()` (R) the helpers.

Forward-looking goals and open work are tracked in [TODO.md](TODO.md).

---

## Components

| Component | Type | Shiny input value |
|-----------|------|-------------------|
| `Alert` | Display | — |
| `Badge` | Display | — |
| `Card` | Container | — |
| `Separator` | Display | — |
| `Button` | Input | click count (integer) |
| `Input` | Input | current string |
| `Checkbox` | Input | boolean |
| `Switch` | Input | boolean |
| `Slider` | Input | number |
| `Select` | Input | selected string |
| `Dialog` | Overlay | boolean (open state) |
| `Popover` | Overlay | boolean (open state) |

---

## Directory layout

```
shadcn/
  js/
    src/
      components/       ← shadcn source + shinyreact bridge, one file per component
      lib/
        utils.js        ← cn() helper (clsx + tailwind-merge)
        trigger-button.jsx  ← shared trigger button for overlay components
      hooks.js          ← single destructure of window.shinyreact hooks
      index.jsx         ← registerComponents entry point
      styles.css        ← Tailwind v4 @theme tokens + Bootstrap compatibility layer
    vite.config.js
    package.json
  pkg-py/
    shadcn/__init__.py  ← Python helper functions (badge, button, card, ...)
  pkg-r/
    shadcn.R            ← R helper functions (shadcn_badge, shadcn_button, ...)
  examples/
    app-py/             ← Basic demo: all 12 components in one card (Python)
    app-r/              ← Same in R
    settings-py/        ← User preferences panel demo (Python)
    settings-r/         ← Same in R
    overlay-py/         ← Dialog + Popover + Select demo (Python)
    overlay-r/          ← Same in R
  www/
    shadcn.js           ← Built IIFE bundle (committed)
    style.css           ← Built CSS (committed)
```

---

## Build

```bash
cd js
npm install
npm run build       # → www/shadcn.js + www/style.css
```

Watch mode for development:

```bash
npm run dev
```

---

## Run examples

### Python

```bash
# from repo root
uv run shiny run ui-frameworks/shadcn/examples/app-py/app.py
uv run shiny run ui-frameworks/shadcn/examples/settings-py/app.py
uv run shiny run ui-frameworks/shadcn/examples/overlay-py/app.py
```

### R

```r
# from R console
shiny::runApp("ui-frameworks/shadcn/examples/app-r/app.R")
shiny::runApp("ui-frameworks/shadcn/examples/settings-r/app.R")
shiny::runApp("ui-frameworks/shadcn/examples/overlay-r/app.R")
```

---

## Using in your own app

### Python

```python
import sys
sys.path.insert(0, "path/to/ui-frameworks/shadcn/pkg-py")

import shadcn as sc
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("main", extra_deps=[sc._dep()]),
        style="max-width:480px; margin:2rem auto;",
    )
)

def server(input, output, session):
    @shinyreact.render_react
    def main():
        return sc.card(
            sc.text_input("name", placeholder="Your name…", label="Name"),
            sc.slider("age", min=18, max=99, value=30, label="Age"),
            sc.button("submit", "Submit"),
            title="Profile",
        )

app = App(app_ui, server)
```

### R

```r
source("path/to/ui-frameworks/shadcn/pkg-r/shadcn.R")
library(shinyreact)

ui <- page_react(
  output_react("main", extra_deps = list(shadcn_dep("path/to/ui-frameworks/shadcn/www")))
)

server <- function(input, output, session) {
  output$main <- render_react({
    shadcn_card(
      shadcn_input("name", placeholder = "Your name…", label = "Name"),
      shadcn_slider("age", min = 18, max = 99, value = 30, label = "Age"),
      shadcn_button("submit", "Submit"),
      title = "Profile"
    )
  })
}

shinyApp(ui, server)
```

---

## Adding a new component

Four files to touch. Use `/scaffold-component` in Claude Code to do this automatically.

**1. `js/src/components/<name>.jsx`** — shadcn source (TypeScript stripped) at the top, shinyreact bridge at the bottom:

```jsx
import { useShinyInput } from "shinyreact";

// --- shadcn source ---
function MyComponent({ className, ...props }) { /* exact shadcn source */ }

// --- shinyreact bridge ---
function ShinyMyComponent({ element, children }) {
  const { input_id, ...rest } = element.props;
  const [value, setValue] = useShinyInput(input_id, "");
  return <MyComponent value={value} onChange={setValue} />;
}

export { ShinyMyComponent as MyComponent };
```

**2. `js/src/index.jsx`** — add import and register:

```jsx
import { MyComponent } from "@/components/my-component";
// in registerComponents:
"shadcn:MyComponent": MyComponent,
```

**3. `pkg-py/shadcn/__init__.py`** — add Python helper:

```python
def my_component(input_id: str, ...) -> shinyreact.Node:
    return shinyreact.Node(type="shadcn:MyComponent", props={"input_id": input_id, ...})
```

**4. `pkg-r/shadcn.R`** — add R helper:

```r
shadcn_my_component <- function(input_id, ...) {
  node("shadcn:MyComponent", props = list(input_id = input_id, ...))
}
```

Then rebuild: `cd js && npm run build`.

---

## Architecture notes

- **Single-file per component** — shadcn source and shinyreact bridge live in the same file. No `components/` + `wrappers/` split.
- **`export { ShinyFoo as Foo }`** — internal bridge function uses `Shiny` prefix to avoid naming clash with the shadcn source function of the same name in the same file; exported under the clean name.
- **`react-dom` bundled, not externalized** — `window.shinyreact.ReactDOM` is `react-dom/client` only and lacks `createPortal`. Radix overlay components (Dialog, Select, Popover) need `createPortal`, so `react-dom` is bundled (~2 kB gzip). Only `react` and `react-dom/client` are externalized.
- **Tailwind v4 `@theme`** — design tokens live in `styles.css`. Add new color tokens here when wrapping components that use Tailwind classes not covered by the base theme.
