# Example `hello-shinyreact` — Shiny Express + shinyreact

A minimal **Shiny Express** app that mixes traditional Express UI (`ui.input_text`, `ui.input_slider`, `ui.layout_sidebar`) with one custom `shinyreact` output that renders a Card containing Badges and a Button.

> **Note:** Uses `shinyreact` and the **Express** mode of Shiny (where the script body itself is the UI). This is mostly a "smallest possible custom-component" demo — it's older than the numbered examples and uses a different Shiny entry point.

## What it shows

- Subclassing `shinyreact.render_react` with `extra_deps` to inject the custom-components JS bundle.
- A `Card` / `Badge` / `Button` component trio registered in `demo_components.js`.
- Reactive updates: typing in the sidebar text box and moving the slider both retrigger the `@render_demo` function, which returns a fresh `Node` tree.

## Layout

```
examples/hello-shinyreact/
├── app.py                # Shiny Express app: imports shinyreact + custom render subclass
└── demo_components.js    # JS bundle: Card / Badge / Button
```

## Run it

```bash
uv run shiny run examples/hello-shinyreact/app.py
```
