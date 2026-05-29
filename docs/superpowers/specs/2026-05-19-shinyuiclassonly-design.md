# shinyuiclassonly — class hierarchy without session machinery

**Date:** 2026-05-19
**Status:** Design — sibling prototype to `shinyui`, for team comparison
**Related:** `docs/superpowers/specs/2026-05-06-unified-ui-component-class-design.md` (umbrella),
`docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md` (full prototype)

## Summary

`shinyuiclassonly` is a third top-level Python package in this repo (sibling to
`shinyreact` and `shinyui`). It carries the **class hierarchy** half of the
`shinyui` prototype with **none of the session-bound machinery**. Same
component vocabulary as `shinyui` (`card`, `accordion`, `input_slider`,
`output_plot`, …); same `UiComponent` / `UiInput` / `UiOutput` / `UiLayout`
roles; same `AllowsChildren` mixin and parent-tag context stack; no
`.value()` / `.update()` / `.click_value()` accessors, no `_session` capture,
no input-handler or bookmark registration.

Two examples (`examples/app-py/16-shinyuiclassonly-core/app.py` and
`examples/app-py/17-shinyuiclassonly-express/app.py`) mirror the existing
shinyui examples 14/15 line-for-line so the team can read the diff in one
sitting.

## Motivation

The `shinyui` prototype bundles two independent ideas:

1. **Structural** — every UI component is a `Tagifiable` class with a clear
   inheritance position (`UiInput`, `UiOutput`, `UiLayout`), an
   `AllowsChildren` mixin that drives a parent-tag context stack, and
   `@overload` signatures that work in both Core (positional) and Express
   (`with`-block) styles.
2. **Server-side ergonomics** — components capture the active session at
   construction, expose typed reactive accessors (`slider.value()`,
   `acc.open_panels()`, `card.full_screen_value()`, `plot.click_value()`),
   support server-driven `update(...)`, own their input handler and
   bookmark serializer, and ship a session-aware `render_plot` decorator.

Showing the team both at once makes it hard to evaluate the structural
half on its own merits. `shinyuiclassonly` carves out the structural half
as a standalone package: the cheapest possible step from `ui.card(...)` →
`card(...)`. The full-fat `shinyui` package remains as the eventual
target. The pair lets the team answer two questions independently:

- "Is the *class hierarchy* an improvement over function-returning factories?"
- "Are the session-bound *accessors and `update()` methods* worth their
  cost (per-session state, lifecycle complexity, bookmark coupling)?"

## Goals

- Sibling Python package `shinyuiclassonly`, installed from the same wheel
  as `shinyreact` and `shinyui`.
- Mirrors `shinyui`'s class hierarchy and concrete component set exactly,
  minus session-bound machinery.
- Two examples that recreate the UI trees of examples 14 and 15
  line-for-line, swapping class accessors for direct `input.<id>()` reads
  and `shiny.ui.update_*` calls.
- Tests parallel `pkg-py/tests/shinyui/`, with every session-mocking test
  dropped.
- CLAUDE.md gains a short section that names both prototypes and explains
  when to use which.

## Non-goals

- Replacing `shinyui` or making it deprecated. Both packages coexist.
- Changing `shinyreact`, `js/`, or any wire protocol.
- Adding new components or new component features. This package is a
  trimmed subset of an existing class hierarchy.
- Reaching toward `py-shiny` adoption directly from this package. The
  upstream story still goes through `shinyui` (per the umbrella spec).

## Package layout

```
pkg-py/src/shinyuiclassonly/
  __init__.py                # re-exports (see "Public API" below)
  _base.py                   # UiComponent (ABC): tagify(), html_dependencies ClassVar.
                             # NO _session, NO _require_session, NO _read_input.
  _roles.py                  # UiInput, UiOutput, UiLayout — empty marker subclasses.
                             # UiInput has NO abstract value() method.
  _children.py               # AllowsChildren: children list, append(), __enter__/__exit__.
  _ctx_stack.py              # contextvars stack + displayhook shim. Verbatim port from shinyui.
  _ctx_tag.py                # CtxTag(Tag) with contextvar-aware __enter__/__exit__. Verbatim port.
  _card.py                   # card(UiLayout, AllowsChildren): Express + Core overloads, tagify().
  _accordion.py              # accordion(UiLayout, AllowsChildren): overloads, tagify().
  _accordion_panel.py        # accordion_panel(UiLayout, AllowsChildren): overloads, tagify().
  _input_slider.py           # input_slider(UiInput): tagify().
  _input_select.py           # input_select(UiInput): tagify().
  _input_action_button.py    # input_action_button(UiInput): tagify().
  _output_code.py            # output_code(UiOutput): tagify().
  _output_plot.py            # output_plot(UiOutput): tagify() (keeps click/brush/etc. flags).
  _render_plot.py            # render_plot(shiny.render.plot): flags + auto_output_ui().
```

Tests live at `pkg-py/tests/shinyuiclassonly/` (parallel to
`pkg-py/tests/shinyui/`).

Examples live at:

- `examples/app-py/16-shinyuiclassonly-core/app.py`
- `examples/app-py/17-shinyuiclassonly-express/app.py`

## Build wiring

Three changes to root `pyproject.toml`:

- `[tool.hatch.build.targets.wheel].packages` gains
  `"pkg-py/src/shinyuiclassonly"`.
- `[tool.pyright].include` gains
  `"pkg-py/src/shinyuiclassonly"`.
- `[tool.ruff.lint.per-file-ignores]` gains
  `"pkg-py/src/shinyuiclassonly/**/*.py" = ["N801"]` (snake_case class
  names, matching the shinyui convention).

No new dependencies. No `dependency-groups` changes. The package builds
into the same `shinyreact` wheel as the other two.

## Class hierarchy

```
UiComponent (ABC, tagify())
├── UiInput            (marker, no abstract value())
│     ├── input_slider
│     ├── input_select
│     └── input_action_button
├── UiOutput           (marker)
│     ├── output_code
│     └── output_plot
└── UiLayout           (marker)
      ├── card             (+ AllowsChildren)
      ├── accordion        (+ AllowsChildren)
      └── accordion_panel  (+ AllowsChildren)
```

`AllowsChildren` is orthogonal to the role split — mirroring `shinyui`
and the umbrella design.

### What's kept vs. dropped relative to shinyui

| Concept                                     | shinyui | shinyuiclassonly |
|---------------------------------------------|---------|------------------|
| `UiComponent` (ABC, `tagify()`)             | ✅      | ✅               |
| `UiComponent._session` (captured on init)   | ✅      | ❌               |
| `UiComponent._require_session()`            | ✅      | ❌               |
| `UiComponent._read_input()`                 | ✅      | ❌               |
| `UiInput` / `UiOutput` / `UiLayout` markers | ✅      | ✅               |
| Abstract `UiInput.value()`                  | ✅      | ❌               |
| `AllowsChildren` mixin (children + ctx mgr) | ✅      | ✅               |
| Parent-tag context stack + displayhook shim | ✅      | ✅               |
| `CtxTag(Tag)` with contextvar `__enter__`   | ✅      | ✅               |
| `HasInputValue` mixin                       | ✅      | ❌               |
| Input-handler `__init_subclass__` registry  | ✅      | ❌               |
| `bookmark_serializer` + per-session id map  | ✅      | ❌               |
| `lookup_component`                          | ✅      | ❌               |
| `Updatable` ABC + `update()` methods        | ✅      | ❌               |
| `reactive_calc_method`                      | ✅      | ❌               |
| `.value()` / `.open_panels()` / `.full_screen_value()` accessors | ✅ | ❌ |
| `render_plot.auto_output_ui()`              | ✅      | ✅               |
| `render_plot.click_value/brush_value/...`   | ✅      | ❌               |
| Concrete `card`, `accordion`, `accordion_panel` | ✅  | ✅               |
| Concrete `input_slider`, `input_select`, `input_action_button` | ✅ | ✅ |
| Concrete `output_code`, `output_plot`       | ✅      | ✅               |

## Component behavior

Every concrete class has the same shape:

```python
class card(UiLayout, AllowsChildren):
    @overload
    def __init__(self, *, id: str | None = None, full_screen: bool = False,
                 height: str | None = None, ...) -> None: ...

    @overload
    def __init__(self, *args: TagChild, id: str | None = None,
                 full_screen: bool = False, ...) -> None: ...

    def __init__(self, *args, id=None, full_screen=False, ...):
        self.id = id
        self._full_screen = full_screen
        # ... store remaining kwargs as plain attrs
        super().__init__(*args)  # AllowsChildren claims *args as children

    def tagify(self) -> Tag:
        import shiny.ui as _sui
        return _sui.card(*self.children, id=self.id,
                         full_screen=self._full_screen, ...).tagify()
```

Differences from the `shinyui` equivalents:

- No `super().__init__(*args, id=id)` through `HasInputValue` — just
  `AllowsChildren.__init__(*args)`. `id` is a plain instance attribute.
- No `_register_input_handler`, no `register_instance` after `super().__init__`.
- No `value()`, no `update()`, no `full_screen_value()`, no `click_value()`,
  no `open_panels()`, no `_read_input`.
- `id` is `Optional[str]` on layouts (without accessors there's no reason
  to require it). Inputs/outputs still require `id` — needed by the
  underlying `shiny.ui.input_*` / `shiny.ui.output_*` factories.

### `accordion.tagify()` preserves the isinstance quirk

`shiny.ui.accordion` rejects pre-rendered `Tag`s and does
`isinstance(panel, AccordionPanel)` on its positional args. The same
inline rebuild that shinyui's `accordion.tagify()` performs is preserved
here. That code is markup plumbing, not session plumbing.

### `render_plot` keeps `auto_output_ui` only

`render_plot` extends `shiny.render.plot`, carries the interaction flags
(`click`, `dblclick`, `hover`, `brush`, `inline`, `fill`), and overrides
`auto_output_ui()` to emit a `shinyuiclassonly.output_plot` instance with
matching flags:

```python
def auto_output_ui(self, **_kw):
    from ._output_plot import output_plot
    return output_plot(
        self.output_id, inline=self.inline,
        click=self.click_enabled, dblclick=self.dblclick_enabled,
        hover=self.hover_enabled, brush=self.brush_enabled, fill=self.fill,
    )
```

The instance is returned directly (not `.tagify()`'d). htmltools' walker
tagifies it later. Difference from shinyui (which returns a `Tag`): this
reinforces the "components are `Tagifiable`, not `Tag`" lesson.

The session-reading `.click_value()` / `.dbl_value()` / `.hover_value()`
/ `.brush_value()` accessors are dropped. Server code reads
`input.<id>_click()` etc. directly.

## Public API

```python
"""shinyuiclassonly — class-per-component UI hierarchy, stripped of session machinery.

A smaller delta from existing shiny.ui behavior than shinyui: the class
hierarchy, AllowsChildren + parent-tag context stack, and Core/Express
overloads, with no session capture, no `.value()`/`.update()` accessors,
no input-handler or bookmark registration. Server code reads inputs via
`input.<id>()` and pushes updates via `shiny.ui.update_*` the usual way.
"""

from ._accordion import accordion
from ._accordion_panel import accordion_panel
from ._base import UiComponent
from ._card import card
from ._children import AllowsChildren
from ._ctx_tag import CtxTag
from ._input_action_button import input_action_button
from ._input_select import input_select
from ._input_slider import input_slider
from ._output_code import output_code
from ._output_plot import output_plot
from ._render_plot import render_plot
from ._roles import UiInput, UiLayout, UiOutput

__all__ = [
    "AllowsChildren", "CtxTag",
    "UiComponent", "UiInput", "UiLayout", "UiOutput",
    "accordion", "accordion_panel", "card",
    "input_action_button", "input_select", "input_slider",
    "output_code", "output_plot",
    "render_plot",
]
```

Symbols dropped vs. shinyui: `HasInputValue`, `Updatable`,
`lookup_component`.

## Examples

`examples/app-py/16-shinyuiclassonly-core/app.py` mirrors
`14-unified-ui-prototype/app.py`. `examples/app-py/17-shinyuiclassonly-express/app.py`
mirrors `15-shinyui-with-blocks/app.py`. Same UI tree as 14/15.

Differences from 14/15:

- `import shinyuiclassonly as su` instead of `import shinyui as su`.
- **No walrus bindings on inputs or layouts.** The server reads via
  `input.<id>()`, so there is no reason to bind a module-level name on
  any class instance. Each example carries a top-of-file comment calling
  this out as the architectural diff against examples 14/15.
- Server-side reads:

  | shinyui (14/15)                      | shinyuiclassonly (16/17)                     |
  |---------------------------------------|----------------------------------------------|
  | `n_slider.value()`                    | `input.n()`                                  |
  | `dist_select.value()`                 | `input.dist()`                               |
  | `seed_slider.value()`                 | `input.seed()`                               |
  | `acc.open_panels()`                   | `tuple(input.acc() or ())`                   |
  | `main_card.full_screen_value()`       | `bool(input.main_card_full_screen())`        |
  | `plot.click_value()`                  | `input.plot_click()`                         |
  | `plot.brush_value()`                  | `input.plot_brush()`                         |

- Server-side updates:

  | shinyui                                | shinyuiclassonly                              |
  |----------------------------------------|----------------------------------------------|
  | `acc.update(open=("Settings", "Diagnostics"))` | `ui.update_accordion("acc", show=["Settings", "Diagnostics"])` |
  | `acc.update(open=False)`               | `ui.update_accordion("acc", show=False)`     |

- Event triggers: `@reactive.event(open_all_btn.value, ...)` becomes
  `@reactive.event(input.open_all, ...)`.
- Plot renderer: `@su.render_plot(click=True, brush=True)` stays — same
  decorator, same Express auto-placement. The renderer no longer carries
  `.click_value()` / `.brush_value()` accessors.

## Tests

Parallel suite at `pkg-py/tests/shinyuiclassonly/`:

```
conftest.py                 # any shared fixtures (likely empty — no session mocks needed)
test_base.py                # UiComponent: ABC contract, html_dependencies ClassVar, tagify() required
test_roles.py               # UiInput / UiOutput / UiLayout are markers; no abstract value() required
test_children.py            # AllowsChildren: positional, append(), __enter__/__exit__
test_ctx_stack.py           # parent-tag context stack — async-task isolation, displayhook restoration
test_card.py                # card.tagify() shape; with-block composition; no full_screen_value()
test_accordion.py           # accordion.tagify() rebuilds AccordionPanel inline (isinstance quirk)
test_accordion_panel.py     # accordion_panel.value default-from-title; tagify()
test_input_slider.py        # input_slider.tagify() forwards kwargs verbatim
test_input_select.py
test_input_action_button.py
test_output_code.py
test_output_plot.py         # tagify() carries click/brush flags through to shiny.ui.output_plot
test_render_plot.py         # auto_output_ui returns shinyuiclassonly.output_plot instance (not Tag)
test_hierarchy.py           # isinstance(card(), UiLayout); isinstance(input_slider(...), UiInput)
test_public_exports.py      # __all__ matches actual exports; no HasInputValue/Updatable/lookup_component
test_smoke.py               # build a small tree end-to-end, .tagify() succeeds
```

Tests dropped vs. shinyui: `test_input_handler_registration`,
`test_input_value`, `test_bookmark_roundtrip`, `test_reactive`,
`test_read_accessors`, `test_update_resolution`, `test_updatable`,
`test_allows_children` (rolled into `test_children`). Anything that
needed a mocked session is gone.

## CLAUDE.md updates

Two changes to the root `CLAUDE.md`:

**(a) Update the "Repo structure" block** to list all three Python
packages:

```
pkg-py/                       # Python packages (three shipped from one wheel)
  src/shinyreact/             # Core JSON-spec / React-bridge package
    www/                      # Bundled JS
  src/shinyui/                # Class-per-component UI hierarchy prototype (session-aware)
  src/shinyuiclassonly/       # Class-per-component UI hierarchy, structure only (no session)
  tests/                      # pytest tests for all three packages
```

**(b) Add a new section "Sibling packages: shinyui and shinyuiclassonly"**
between the existing "Repo structure" and "Commands" sections:

> Two prototype packages explore a class-per-component UI hierarchy as a
> possible direction for `py-shiny`'s `ui.*` surface. They share the same
> component vocabulary (`card`, `accordion`, `input_slider`, …) but
> differ in what server-side machinery comes attached.
>
> - **`shinyui`** — the full prototype. Every component is a
>   `Tagifiable` class that *also* captures the active session at
>   construction, registers itself with a per-session id→instance map,
>   exposes typed reactive accessors (`slider.value()`,
>   `card.full_screen_value()`, `acc.open_panels()`), supports
>   server-driven `update(...)`, owns its input handler and bookmark
>   serializer, and ships a `render_plot` with derived-input accessors
>   (`click_value`, `brush_value`, …). This is what the umbrella design
>   (`docs/superpowers/specs/2026-05-06-unified-ui-component-class-design.md`)
>   proposes for upstream `py-shiny`. Examples 14 and 15 demonstrate it
>   in Core (positional) and Express (`with`-block) form respectively.
>
> - **`shinyuiclassonly`** — the *small delta* the team can compare
>   against today's `ui.*`. Same component classes and same hierarchy
>   (`UiComponent`, `UiInput`, `UiOutput`, `UiLayout`, `AllowsChildren`,
>   parent-tag context stack), but with **none** of the session-bound
>   machinery: no `_session` capture, no `.value()` / `.update()` /
>   `.click_value()` accessors, no input-handler or bookmark
>   registration, no per-session instance registry, no
>   `reactive_calc_method`. Components are pure `Tagifiable` objects.
>   Server code reads inputs via `input.<id>()` and pushes updates via
>   `shiny.ui.update_*` — exactly like today. Examples 16 and 17 mirror
>   14 and 15 line-for-line so the diff is small enough to read in one
>   sitting.
>
> Use **`shinyuiclassonly`** when motivating "what does the class
> hierarchy give us, structurally, before we add server-side
> ergonomics?" — it's the cheapest possible step from `ui.card(...)` →
> `card(...)`. Use **`shinyui`** when motivating the full vision (typed
> accessors, `update()` on the instance, auto-placement of renderers).

## Open questions

None at design-approval time.
