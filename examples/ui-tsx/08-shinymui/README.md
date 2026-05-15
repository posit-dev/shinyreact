# 08-shinymui — `ui.tsx` pattern with shinymui

Demonstrates loading the `shinymui` IIFE bundle via `shinymui.dep()` from a `ui.tsx`-pattern app, then having the server-rendered Specs flow into hand-written React via shinyreact's existing `.shinyreact-output` binding.

UI: same as `examples/app-py/14-shinymui/` — a Controls card (TextField, Slider, Button + echo) and a Filtered data card (DataGrid). The difference is *where* the layout lives: in `src/App.jsx` here, in `app.py` over there.

## How the shinymui catalog reaches the page

1. `app.py` defines a thin subclass `shinymui_output(reactive_output)` whose `auto_output_ui()` returns `ui_output(..., extra_deps=[shinymui.dep()])`. This is the RFC §4.4 "subclass when there's package-specific transform/dep logic" pattern.
2. `set_react_page()` walks every `Renderer` in the app and collects HTMLDependencies from their `auto_output_ui()`. The shinymui dep gets injected into the page once (Shiny dedupes).
3. The shinymui IIFE bundle calls `window.shinyreact.registerComponents(catalog, registry)` at load, populating the `mui:*` entries.
4. `App.jsx` renders `<ShinyOutput id="controls_card" className="shinyreact-output" />` for each spec region. `ShinyOutput` (from `window.shinyreact`) creates the DOM and runs `Shiny.bindAll`, which finds the existing `.shinyreact-output` OutputBinding registered by shinyreact's main bundle.
5. The OutputBinding receives the server-side Spec (from `@shinymui_output def controls_card(): return shinymui.card(...)`) and renders it via `ShinyreactRenderer`, which looks up `mui:Card`, `mui:Button`, etc. in the registry and instantiates them.

## Build & run

```bash
# Ensure shinymui is built and installed
(cd downstream-prototypes/shinymui/js && npm install && npm run build)
cp downstream-prototypes/shinymui/js/dist/shinymui.js \
   downstream-prototypes/shinymui/pkg-py/src/shinymui/www/shinymui.js
uv pip install -e downstream-prototypes/shinymui/pkg-py

# Build this example's React client bundle
cd examples/ui-tsx/08-shinymui
npm install
npm run build      # writes www/app.js

cd ../../..
uv run shiny run --reload examples/ui-tsx/08-shinymui/app.py
```
