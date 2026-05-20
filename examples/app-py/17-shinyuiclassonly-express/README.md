# 17 — shinyuiclassonly (Express, `with`-blocks)

End-to-end Shiny **Express** demo of
[shinyuiclassonly](../../../pkg-py/src/shinyuiclassonly), using `with`-block
composition. The same UI tree as
[example 16](../16-shinyuiclassonly-core/), expressed via
`with card(): with accordion(): ...` instead of positional `card(...)` calls.

## Run

```
uv sync --group examples           # one-time, installs matplotlib + numpy
uv run shiny run examples/app-py/17-shinyuiclassonly-express/app.py
```

Requires `matplotlib` and `numpy` (in the repo's `examples` dependency
group). If you already ran `uv sync --all-extras --all-groups` per the
top-level README, they are already installed.

## What this demonstrates

Same delta from [example 15](../15-shinyui-with-blocks/) (`shinyui` Express
form) as example 16 has from example 14:

- Server reads use `input.<id>()`, not `n_slider.value()` /
  `acc.open_panels()` / `card.value_full_screen()` /
  `plot.value_click()`.
- Server updates use `shiny.ui.update_accordion(...)`, not
  `acc.update(...)`.
- **No walrus operators** on input or layout component construction — the
  server reads via `input.<id>()` directly, so there is no reason to bind
  a module-level name on any component instance. Compare to example 15,
  which uses `(n_slider := su.input_slider(...))` so the server can call
  `n_slider.value()`.

The parent-tag context stack inside `shinyuiclassonly` makes the
`with` syntax work — same mechanism as `shinyui`, just without the
session machinery layered on top.

## What to try

Same as [example 16](../16-shinyuiclassonly-core/) — drag the slider,
change the distribution, toggle accordion panels, click/brush the plot.

## See also

- [Example 15](../15-shinyui-with-blocks/) — the same UI in `shinyui`
  (session-aware) Express form.
- [Example 16](../16-shinyuiclassonly-core/) — the Core / positional
  variant of this same UI.
- [`decisions/2026-05-19-class-based-ui-type-system.md`](../../../decisions/2026-05-19-class-based-ui-type-system.md)
  — the "why bother" argument for the class hierarchy.
