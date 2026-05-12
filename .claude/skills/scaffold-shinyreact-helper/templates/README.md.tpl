# {{pkg}} (prototype)

**Status:** scaffold from `scaffold-shinyreact-helper`. Validates conventions in the [helper-packages RFC](../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md).

Exposes `{{upstream_pkg}}` components to `shinyreact`. Currently scaffolded with one stub component (`{{Stub}}`); add more by following the pattern in `downstream-prototypes/shinymui/`.

## Run the example

```bash
cd {{target_dir}}
(cd js && npm install && npm run build)
cp js/dist/{{pkg}}.js pkg-py/src/{{pkg}}/www/{{pkg}}.js
uv pip install -e pkg-py
uv run shiny run --reload example/app.py
```
