# 14-shinymui — `app.py` pattern with shinymui

Demonstrates the `app.py` pattern using the `shinymui` helper package (under `downstream-prototypes/shinymui/`). The server-side `@reactive_output` returns a `shinyreact.Node` tree built from `shinymui` factories; shinymui's IIFE bundle is loaded via `shinymui.dep()` and renders the catalog entries client-side.

UI: a `Controls` card (TextField, Slider, Button + an echo line) plus a `Filtered data` card holding a DataGrid filtered by the slider's value.

The paired example at `examples/ui-tsx/08-shinymui/` produces the same UI through the `ui.tsx` pattern.

## Run

```bash
# From the repo root — ensure shinymui is installed
(cd downstream-prototypes/shinymui/js && npm install && npm run build)
cp downstream-prototypes/shinymui/js/dist/shinymui.js \
   downstream-prototypes/shinymui/pkg-py/src/shinymui/www/shinymui.js
uv pip install -e downstream-prototypes/shinymui/pkg-py

uv run shiny run --reload examples/app-py/14-shinymui/app.py
```
