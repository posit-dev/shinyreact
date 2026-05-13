# 14 — Unified UI prototype (shinyui Stage A)

End-to-end demo of [shinyui](../../../pkg-py/src/shinyui), the class-per-component
UI hierarchy from issue #69 (umbrella #68). Each UI component is a Python class
that owns its own metadata (handler, serializer, HTML deps, `update()`, server-side
read accessors).

## Run

```
uv run shiny run examples/app-py/14-unified-ui-prototype/app.py
```

Requires `matplotlib` for the placeholder plot (already in this repo's `examples`
extras group).

## What this demonstrates

| Archetype | Class | Demonstrated by |
|---|---|---|
| Simple input | `UiInputSlider` | `n` and `seed` sliders |
| Structured input | `UiInputSelect` | `dist` selector |
| Plain output | `UiOutputCode` | `summary` and `diag` outputs |
| Output with read-only signals | `UiOutputPlot` | `plot` with `click=True, brush=True` |
| Layout with children + state | `UiCard` | `main_card.full_screen_value()`, `main_card.update(full_screen=...)` |
| Layout with state + children | `UiAccordion` | `acc.open_panels()`, `acc.update(open=...)` |
| Layout-as-child | `UiAccordionPanel` | Two panels inside `acc` |

## Class-per-component patterns in the server code

The server uses `su.lookup_component(session, id)` to retrieve typed handles for
each component constructed in `app_ui(request)`. Through those handles, server
code reads input values:

```python
n_slider = cast(su.UiInputSlider, su.lookup_component(session, "n"))

@render.code
def summary():
    return f"n = {n_slider.value()}"
```

…and pushes updates:

```python
@reactive.effect
def _auto_expand_at_high_n():
    if n_slider.value() > 800:
        main_card.update(full_screen=True)
        acc.update(open=("Settings", "Diagnostics"))
```

Each `.value()` / `.full_screen_value()` / `.open_panels()` / `.click_value()` /
`.brush_value()` accessor is a `@reactive.calc` under the hood, so reads inside
reactive contexts establish dependencies correctly.

## What to try

- Drag `n` — `summary` updates immediately.
- Drag past `n=800` — the card auto-expands to full-screen and both accordion
  panels open via `.update()` calls.
- Click or brush on the plot — coordinates appear in the `diag` panel via
  `plot_handle.click_value()` / `plot_handle.brush_value()`.

## Notes on real-app fidelity

- `UiCard.full_screen_value()` reads `input.<card_id>()` — Stage A doesn't wire
  the browser-side push for `full_screen` state, so the value stays `False` in
  a live browser session until the JS binding is added. Unit tests exercise the
  full path with a mocked session.
- Plot click/brush bindings ARE wired by shiny natively — `output_plot(click=True,
  brush=True)` registers the standard shiny.plot bindings, so the JSON-shaped
  values flow into `input.<id>_click` / `input.<id>_brush` as expected.
