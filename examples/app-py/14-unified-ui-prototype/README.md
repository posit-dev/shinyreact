# 14 — Unified UI prototype (shinyui Stage A)

End-to-end Shiny Express demo of [shinyui](../../../pkg-py/src/shinyui), the
class-per-component UI hierarchy from issue #69 (umbrella #68). Each UI
component is a Python class that owns its own metadata (handler, serializer,
HTML deps, `update()`, server-side read accessors).

## Run

```
uv run shiny run examples/app-py/14-unified-ui-prototype/app.py
```

Requires `matplotlib` and `numpy` (already in the repo's `examples` extras).

## What this demonstrates

| Archetype | Class | Demonstrated by |
|---|---|---|
| Simple input | `input_slider` | `n` and `seed` sliders |
| Structured input | `input_select` | `dist` selector |
| Action input | `input_action_button` | `Open all panels` / `Close all panels` |
| Plain output | `output_code` | `summary` and `diag` outputs |
| Output with read-only signals | `output_plot` | `plot` with `click=True, brush=True` |
| Layout with children + state | `card` | `main_card.full_screen_value()`, `main_card.update(full_screen=...)` |
| Layout with state + children | `accordion` | `acc.open_panels()`, `acc.update(open=...)` |
| Layout-as-child | `accordion_panel` | `Settings` and `Diagnostics` panels |

## Class-per-component patterns in the server code

Components are constructed at module level so they're shared between the
top-level Express layout and the server-side renderers via closure. Each
class accessor reads a wire-side input value reactively:

```python
n_slider = su.input_slider("n", "Sample size", 10, 1000, 100)

@render.code
def summary():
    return f"n = {n_slider.value()}"
```

…and `.update()` pushes state back to the client. The Open all / Close all
action buttons drive `accordion.update()`:

```python
@reactive.effect
@reactive.event(open_all_btn.clicked, ignore_init=True)
def _open_all_panels():
    acc.update(open=("Settings", "Diagnostics"))


@reactive.effect
@reactive.event(close_all_btn.clicked, ignore_init=True)
def _close_all_panels():
    acc.update(open=False)
```

Each `.value()` / `.clicked()` / `.full_screen_value()` / `.open_panels()` /
`.click_value()` / `.brush_value()` accessor is a `@reactive.calc` under the
hood, so reads inside reactive contexts establish dependencies correctly.

## What to try

- Drag `n`, change `dist`, or change `seed` — the scatter plot redraws and
  `summary` updates immediately.
- Click **Open all panels** / **Close all panels** — the accordion expands
  or collapses via `acc.update(open=...)`.
- Click or brush on the plot — coordinates appear in the `diag` panel via
  `plot.click_value()` / `plot.brush_value()` (the renderer object created
  by `@su.render_plot(click=True, brush=True)`).

## Notes on real-app fidelity

- `card.full_screen_value()` reads `input.<card_id>_full_screen` — that's
  the wire id shiny's card binding pushes when the user toggles full-screen
  mode. Stage A doesn't ship the browser-side JS for `card.update(full_screen=)`
  to flip the card from the server, so server-driven full-screen changes are
  out of scope for this demo. Unit tests exercise the full accessor path
  with a mocked session.
- Plot click/brush bindings ARE wired by shiny natively — `output_plot(click=True,
  brush=True)` registers the standard shiny.plot bindings, so the JSON-shaped
  values flow into `input.<id>_click` / `input.<id>_brush` as expected.
