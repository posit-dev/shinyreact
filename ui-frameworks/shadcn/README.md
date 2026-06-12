# shadcn for shinyreact

shadcn/ui components wired to Shiny's reactive system through shinyreact. Ships 47 components with matching Python and R helpers. Works from both `app.py` and `app.R` today with no installation: `sys.path.insert` the Python package, or `source()` the R file.

Forward-looking goals and open work are tracked in [TODO.md](TODO.md). The milestone-by-milestone history lives in [../CHANGELOG.md](../CHANGELOG.md); the rationale for the initial single-file refactor is in [../updates.md](../updates.md).

## Components

All 47, grouped by role. Names are the Python helper; the R helper is the same name prefixed `shadcn_` (e.g. `button` / `shadcn_button`).

**Inputs** report a value back to the server through a Shiny input id. See the table below for what each one reports.

`button`, `text_input`, `textarea`, `checkbox`, `switch`, `slider`, `select`, `radio_group`, `toggle`, `toggle_group`, `calendar`, `input_otp`, `pagination`, `command`, `carousel`

**Display** render-only, no input:

`alert`, `badge`, `separator`, `label`, `skeleton`, `progress`, `avatar`, `kbd`, `spinner`, `aspect_ratio`, `tooltip`, `hover_card`, `empty`, `chart`, `breadcrumb`, `table`

**Containers and layout** wrap child nodes:

`card`, `tabs`, `accordion`, `collapsible`, `scroll_area`, `resizable`

**Overlays** track an open/close state through an input id (`alert_dialog` instead reports confirm and cancel click counts):

`dialog`, `popover`, `sheet`, `drawer`, `alert_dialog`

**Menus** build their items from data:

`dropdown_menu`, `context_menu`, `menubar`, `navigation_menu`

**Feedback** is pushed from the server, not read as an input:

`toaster` (Sonner), driven by `send_message`

### Reactive inputs

| Helper | Reports to the server |
|--------|------------------------|
| `button` | click count (integer, event input) |
| `text_input` | current string |
| `textarea` | current string |
| `input_otp` | current string |
| `checkbox` | boolean |
| `switch` | boolean |
| `toggle` | boolean |
| `slider` | number |
| `select` | selected value (string) |
| `radio_group` | selected value (string) |
| `toggle_group` | selected value(s), single or multiple |
| `calendar` | selected date as an ISO `"YYYY-MM-DD"` string |
| `pagination` | current page (1-based integer) |
| `command` | selected item value |
| `carousel` | current slide index (0-based) |
| `dialog`, `popover`, `sheet`, `drawer` | open state (boolean) |

## Directory layout

```
shadcn/
  js/
    src/
      components/          one file per component: shadcn source on top, shinyreact bridge below
      lib/
        utils.js           cn() helper (clsx + tailwind-merge)
        button-base.jsx    shadcn Button + buttonVariants, shared by Button and Calendar
        trigger-button.jsx shared trigger for overlay components
      index.jsx            registerComponents entry point (all 47)
      styles.css           Tailwind v4 @theme tokens + the Bootstrap compatibility layer
      shinyreact.d.ts      ambient types for the host hooks imported from "shinyreact"
    scripts/
      prep-component.mjs     strips a shadcn source file to a bridge-ready stub
      finalize-component.mjs wires the stub into the registry + Python + R helpers
    vite.config.js
    package.json
  pkg-py/                  installable Python package "shinyshadcn"
    pyproject.toml         hatchling backend, built with uv
    hatch_build.py         build hook: copies the shared www/ into the wheel
    src/shinyshadcn/       helpers split by category (_inputs, _display, _overlays,
                           _menus, _layout, _feedback, _dep, _types), re-exported
                           from __init__.py
  pkg-r/
    shadcn.R               R helpers (shadcn_badge, shadcn_button, ...)
  examples/                see "Run examples" below
  www/
    shadcn.js              built IIFE bundle (committed)
    style.css              built CSS (committed)
  download-components.sh   fetches new-york-v4 shadcn sources into a gitignored staging dir
```

The host hooks (`useShinyInput`, `useShinyOutputValue`, ...) are not vendored. They are imported from `"shinyreact"`, which the bundler treats as an external mapped to `window.shinyreact`, the same way `react` is externalized. `shinyreact.d.ts` supplies their types for the editor.

## Build

```bash
cd js
npm install
npm run build       # -> www/shadcn.js + www/style.css
npm run dev         # watch mode
```

## Run examples

Each example ships in Python, R, or both.

| Example | What it shows | Languages |
|---------|---------------|-----------|
| `shinyreact-shadcn` | Component Explorer: every component and variant, one at a time | Python, R |
| `gallery` | Showcase grouped into Inputs / Display / Overlays / Navigation / Layout / Feedback | Python, R |
| `app` | Basic demo, a handful of components in one card | Python, R |
| `variants` | Reference sheet of each component across its variants, sizes, and states | Python, R |
| `settings` | A user-preferences panel | Python, R |
| `overlay` | Dialog + Popover + Select | Python, R |
| `dropdown`, `calendar`, `tabs-table`, `toast` | Focused single-component demos | Python |

```bash
# Python (from repo root)
uv run shiny run ui-frameworks/shadcn/examples/shinyreact-shadcn/app.py

# R (from an R console)
shiny::runApp("ui-frameworks/shadcn/examples/shinyreact-shadcn/app.R")
```

## Using in your own app

### Python

Install it (`cd ui-frameworks/shadcn/pkg-py && uv build`, then `pip install dist/*.whl`), or run straight from the source tree by adding `pkg-py/src` to `sys.path` as below.

```python
import sys
sys.path.insert(0, "path/to/ui-frameworks/shadcn/pkg-py/src")

import shinyshadcn as sc
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

## Adding a new component

The fastest path is `/scaffold-component` in Claude Code, which runs the two-phase codegen below. By hand it is three steps:

1. **Prep.** `node js/scripts/prep-component.mjs <name>` strips a downloaded shadcn source to a bridge-ready `js/src/components/<name>.jsx`: TypeScript removed, `"use client"` dropped, shadcn exports neutralized, imports fixed, and a `@shiny`-annotated bridge stub appended.
2. **Fill the bridge.** This is the only step that needs judgment. Map `element.props` into the component and wire Shiny state with the hooks, then name and export it:

   ```jsx
   import { useShinyInput } from "shinyreact";

   // shadcn source (TypeScript stripped) sits above

   function ShinyMyComponent({ element, children }) {
     const { input_id, ...rest } = element.props;
     const [value, setValue] = useShinyInput(input_id, "");
     return <MyComponent value={value} onChange={setValue} {...rest} />;
   }

   export { ShinyMyComponent as MyComponent };
   ```

3. **Finalize.** `node js/scripts/finalize-component.mjs <name>` reads the `@shiny` annotation and idempotently adds the `index.jsx` import + registry entry, the Python helper, and the R helper.

Then `cd js && npm run build`.

## Architecture notes

- **One file per component.** shadcn source and the shinyreact bridge live together. There is no `components/` plus `wrappers/` split. The bridge is named `ShinyFoo` to avoid clashing with the shadcn `Foo` in the same file, and re-exported as `export { ShinyFoo as Foo }`.
- **`react-dom` is bundled, not externalized.** `window.shinyreact.ReactDOM` is `react-dom/client` only and has no `createPortal`. Radix overlays (Dialog, Popover, Select, ...) need it, so `react` and `react-dom/client` stay external while `react-dom` is bundled (about 2 kB gzipped).
- **`class-variance-authority` is kept.** Variant components use shadcn's real `cva(...)`, so default and compound variants stay faithful to upstream.
- **`className` passes through.** Every bridge merges a caller `className` last via `cn(variants(), className)`. Python helpers take `class_`; R helpers take `class`.
- **Bootstrap compatibility layer in `styles.css`.** Shiny loads Bootstrap unlayered, which beats Tailwind's layered utilities. A small compat layer scoped to `.shinyreact-output` resets typography, re-asserts the grid columns, and force-generates layout utilities used only in app files via `@source inline(...)`.
- **Tailwind v4 `@theme`.** Design tokens live in `styles.css`. Add new color tokens there when wrapping a component that needs classes the base theme does not cover.
```
