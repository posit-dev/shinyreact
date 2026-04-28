# Example `hello-shinyjson` — Shiny Express + shinyjsonold

A minimal **Shiny Express** app that mixes traditional Express UI (`ui.input_text`, `ui.input_slider`, `ui.layout_sidebar`) with one custom `shinyjsonold` output that renders a Card containing Badges and a Button.

> **Note:** Uses `shinyjsonold` and the **Express** mode of Shiny (where the script body itself is the UI). This is mostly a "smallest possible custom-component" demo — it's older than the numbered examples and uses a different Shiny entry point.

## What it shows

- Subclassing `shinyjsonold.render` with `extra_deps` to inject the custom-components JS bundle.
- A `Card` / `Badge` / `Button` component trio registered in `demo_components.js`.
- Reactive updates: typing in the sidebar text box and moving the slider both retrigger the `@render_demo` function, which returns a fresh `Node` tree.

## Layout

```
examples/hello-shinyjson/
├── app.py                # Shiny Express app: imports shinyjsonold + custom render subclass
└── demo_components.js    # JS bundle: Card / Badge / Button
```

## Run it

```bash
uv run shiny run examples/hello-shinyjson/app.py
```
