# `set_react_page()` module dependency discovery — design

**Issue:** [#87](https://github.com/posit-dev/shinyreact/issues/87) — `set_react_page`: HTMLDependency harvesting misses renderers inside Shiny modules.

## Problem

`set_react_page()` (the `ui.tsx` pattern entry) injects downstream `HTMLDependency`
objects into `<head>` by walking the renderers Shiny Express passes to the page
function. Today that walk only sees the renderers handed in as `*args`:

```python
# pkg-py/src/shinyreact/_page.py — _react_page_fn
def _react_page_fn(*args: Any) -> Tag:
    deps: list[HTMLDependency] = []
    for arg in args:
        if isinstance(arg, Renderer):
            ui = arg.auto_output_ui()
            if isinstance(ui, (Tag, TagList)):
                deps.extend(ui.get_dependencies())
    return cast(Tag, TagList(_dep_page(), *deps, HTML(index_html)))
```

A `@render_*` defined inside a `@module.server` function is **not** in `*args`, so
its dependency never reaches `<head>` and the component fails to mount in the
browser (e.g. `shinywidgets` ships an `ipywidget-output-binding` dependency that a
module-level `render_plotly` needs).

The issue floated an explicit `extra_deps=[...]` escape hatch as the immediate
workaround. We are **not** taking that route — dependencies should be discoverable
automatically because module renderers live on the session.

## Key finding (validated empirically)

The Express app body runs **twice**:

1. **UI / tagify pass** — `create_express_app` runs `run_express(...).tagify()` under
   an `ExpressStubSession`. The *entire* app body executes here, including
   `@module.server` calls like `plot_module("a")`.
2. **Server pass** — `express_server` runs `run_express(...)` again **per session**
   under a real `Session`.

During pass 1, every renderer — top-level **and** module — registers into the
active session's `output._outputs` dict before the page function runs. Each entry
exposes its dependency via `auto_output_ui()`. Verified with a probe:

```
keys: ['toplevel', 'a-thing']
  toplevel: ['top-binding']     # top-level renderer
  a-thing:  ['mod-binding']     # renderer inside @module.server, ns "a"
```

So synchronously-mounted module dependencies are **already discoverable at
HTML-generation time** — no websocket push, no client injection, no first-render
race is required to fix the reported bug.

## Design

### Layer A — static `_outputs` harvest (always)

In `_react_page_fn`, after the existing `*args` walk, also harvest from the active
session's registered outputs:

```python
from shiny.session import get_current_session

def _react_page_fn(*args: Any) -> Tag:
    deps: list[HTMLDependency] = []

    # Existing: top-level renderers passed by Express.
    for arg in args:
        if isinstance(arg, Renderer):
            _collect_deps(arg, deps)

    # New: renderers registered on the session, including those inside
    # @module.server (which `*args` never sees).
    session = get_current_session()
    if session is not None:
        for info in session.output._outputs.values():
            _collect_deps(info.renderer, deps)

    return cast(Tag, TagList(_dep_page(), *deps, HTML(index_html)))
```

**Robust dependency extraction.** `get_dependencies()` on the raw `auto_output_ui()`
result can miss dependencies that only materialize during tagification. The harvest
helper must resolve them — call `session._process_ui(ui)` (preferred: it also
registers the server-side `/lib/...` file route and resolves nested/late deps) or
`.tagify()` before reading dependencies, rather than calling `get_dependencies()`
on the untagified object:

```python
def _collect_deps(renderer: Renderer, deps: list[HTMLDependency]) -> None:
    ui = renderer.auto_output_ui()
    if not isinstance(ui, (Tag, TagList)):
        return
    # Tagify / process so "not-immediately-available" deps are resolved
    # (and the file route is registered) before we read them.
    deps.extend(ui.tagify().get_dependencies())
```

(The exact call — `.tagify()` vs `session._process_ui()` — is settled during
implementation; whichever resolves late deps and registers routes without
double-registering is used. `_process_ui` is preferred when a real/stub session is
available.)

**Keep the `*args` walk** (decision: belt-and-suspenders). `_outputs` appears to be
a superset, but retaining both costs nothing — Shiny de-duplicates dependencies by
name+version when hoisting to `<head>`, so overlap is harmless. No `extra_deps`
parameter is added.

**Coverage / limitation.** Layer A covers every renderer mounted *synchronously*
during the app-body run (top-level and module). It does **not** cover modules
mounted *dynamically after page load* (e.g. inside a `@reactive.effect` that calls
a module server in response to an input) — those register after the page HTML is
frozen. That case is handled either by Shiny's native dynamic-UI dependency
injection (see the dynamic test) or by Layer B if proven necessary.

### Dynamic-UI test (decides whether Layer B is built)

Add a fixture app + Playwright test where a checkbox (React state → Shiny input)
gates a plotly chart rendered through Shiny's **dynamic-UI path**, so the
`ipywidget-output-binding` dependency cannot be known until the dynamic UI renders.

Shiny's own `@render.ui` path already calls `session._process_ui()` and ships the
serialized dependencies to the client (`renderContent` → `renderDependencies`). The
hypothesis is that this dynamic case is therefore **already covered natively** and
the test passes without any shinyreact change.

- Write the test initially as `@pytest.mark.xfail(strict=True)`.
- Run it. **Empirically determine** xfail vs pass (the user approved deciding this
  during implementation) and record the outcome in the test and in this spec's
  implementation notes.
- If it **passes** natively → Layer B is YAGNI; do not build it.
- If it **fails** natively → build Layer B (below) and flip the test to passing.

**Outcome: passes natively; Layer B not built.**

*Fixture hardening (post-review):* the first version of the fixture registered
`scatter` at the top level under `ui.hold()`. `ui.hold()` suppresses display but
not session registration, so Layer A pre-injected `ipywidget-output-binding` into
the initial `<head>` and the dep assertion passed vacuously. The fixture now
registers `scatter` inside a `@reactive.effect` — in the real session, after page
HTML is frozen — and the test first asserts the dependency is *absent* from the
initial page before checking the box. The pass therefore genuinely demonstrates
native dynamic-UI delivery, and additionally shows that a renderer registered
*after page load* renders correctly when its placeholder arrives via `@render.ui`
(the #160 gap is specifically the React-supplied-placeholder case).

### Layer B — flush-diff dependency push (conditional, only if the dynamic test fails natively)

There is no public "output added" event (`_outputs` is a plain dict; no observer).
But new outputs are detectable by **diffing on flush**:

1. During the per-session server pass, `set_react_page()` runs under a real session.
   Register `session.on_flush(fn, once=False)` — fires on every reactive flush.
2. The callback remembers seen `_outputs.keys()`; on each flush it diffs to find
   newly-registered outputs (dynamically-mounted modules register during a flush).
3. For each new output, `session._process_ui(auto_output_ui())` registers the file
   route + serializes the dependency, then push a custom message to the client.
4. A new internal handler in the JS bundle calls
   `window.Shiny.renderDependencies(deps)` to inject the `<script>`/`<link>` tags.

This is where the new client-side handler and the inject/bind load-order
considerations live — the reason it is gated behind a failing test rather than
built speculatively.

## Existing test

`pkg-py/tests/playwright/test_module_dependency.py::test_module_renderer_dep_injected`
is currently `@pytest.mark.xfail(strict=True)` against the `module_plotly` fixture
(plain `set_react_page()`). Layer A fixes it:

- Remove the `xfail` marker.
- Leave the `module_plotly` fixture app unchanged — it now proves auto-discovery
  reaches the module renderer with no user-side boilerplate.

## Out of scope

- **R asymmetry.** R's `page_react_html()` is a plain UI function used as
  `shinyApp(ui = ...)`; it performs no renderer auto-discovery at all, so module
  dependencies are not found there either. File a separate GitHub issue noting this
  asymmetry; do not address it here.
- **No `extra_deps` parameter** on `set_react_page()`.

## Documentation

- Docstring note on `set_react_page()`: synchronously-mounted module renderers are
  auto-discovered; dynamically-mounted ones rely on Shiny's dynamic-UI dependency
  injection (and Layer B, if built).
- Update `docs/todos.md` (remove/adjust the #87 entry).

## Testing policy

- Layer A: the existing `test_module_renderer_dep_injected` (xfail → passing) is the
  regression test. It fails without Layer A and passes with it.
- Dynamic-UI test: new fixture + test as described.
- Run via `make py-test-e2e` (Playwright suite is excluded from the default
  `make py-check-tests`).
