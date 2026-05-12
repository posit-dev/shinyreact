# shinymui (prototype)

**Status:** throwaway prototype. Not published. Validates conventions in the
[helper-packages RFC](../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md).

Exposes 5 MUI components to `shinyreact`:

- `Button` (basic factory + slot API + controlled-event input)
- `TextField` (controlled string input)
- `Slider` (controlled numeric input)
- `Card` (children / composition)
- `DataGrid` (specialized component, server-pushed data)

Once the conventions are validated, this prototype is replaced by a real
`shinymui` package (see the follow-up umbrella issue spawned by the RFC).

## Run the example

```bash
cd downstream-prototypes/shinymui
(cd js && npm install && npm run build)  # builds js/dist/shinymui.js
cp js/dist/shinymui.js pkg-py/src/shinymui/www/shinymui.js
uv pip install -e pkg-py
uv run shiny run --reload example/app.py
```
