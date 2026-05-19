# 16 — shinyuiclassonly (Core, positional)

End-to-end Shiny **Core** demo of
[shinyuiclassonly](../../../pkg-py/src/shinyuiclassonly) — the structure-only
sibling of [shinyui](../../../pkg-py/src/shinyui). Each UI component is a
Python class with `tagify()`, but with **no** session-bound machinery
(`.value()`, `.update()`, `.click_value()`, per-session id registry, input
handler registration, bookmark serializer).

The equivalent Express `with`-block variant lives in
[`../17-shinyuiclassonly-express/`](../17-shinyuiclassonly-express/).

## Run

```
uv sync --group examples           # one-time, installs matplotlib + numpy
uv run shiny run examples/app-py/16-shinyuiclassonly-core/app.py
```

Requires `matplotlib` and `numpy` (in the repo's `examples` dependency
group). If you already ran `uv sync --all-extras --all-groups` per the
top-level README, they are already installed.

## What this demonstrates

Same UI tree as [example 14](../14-unified-ui-prototype/) (`shinyui` Core
form), with the server-side accessor layer stripped away:

| What                                  | `shinyui` (example 14)                      | `shinyuiclassonly` (this example)         |
|---------------------------------------|---------------------------------------------|-------------------------------------------|
| Read slider value                     | `n_slider.value()`                          | `input.n()`                               |
| Read accordion open panels            | `acc.open_panels()`                         | `tuple(input.acc() or ())`                |
| Read card full-screen state           | `main_card.full_screen_value()`             | `bool(input.main_card_full_screen())`     |
| Read plot click / brush coordinates   | `plot.click_value()` / `plot.brush_value()` | `input.plot_click()` / `input.plot_brush()` |
| Update accordion from server          | `acc.update(open=...)`                      | `shiny.ui.update_accordion("acc", show=...)` |
| Event trigger on action button        | `@reactive.event(open_all_btn.value, ...)`  | `@reactive.event(input.open_all, ...)`    |
| Walrus bindings on inputs / layouts   | required (server reads class accessors)     | not used (server reads via `input.<id>()`)|

Plot interaction flags and `@su.render_plot(click=True, brush=True)`
auto-placement still work — those are not session-bound.

## What to try

- Drag `n`, change `dist`, change `seed` — the scatter plot redraws and the
  `summary` panel updates immediately.
- Click **Open all panels** / **Close all panels** — the accordion expands or
  collapses via `shiny.ui.update_accordion(...)`.
- Click or brush on the plot — coordinates appear in the `diag` panel,
  read via `input.plot_click()` / `input.plot_brush()`.

## See also

- [Example 14](../14-unified-ui-prototype/) — the same UI in `shinyui`
  (session-aware) Core form. Diff against this file shows what the
  session-bound accessor layer adds on top.
- [Example 17](../17-shinyuiclassonly-express/) — the same UI tree
  expressed with `with`-blocks in Shiny Express.
- [`decisions/2026-05-19-class-based-ui-type-system.md`](../../../decisions/2026-05-19-class-based-ui-type-system.md)
  — the "why bother" argument for the class hierarchy.
