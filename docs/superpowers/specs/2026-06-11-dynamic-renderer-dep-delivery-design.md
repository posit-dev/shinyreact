# Dynamic renderer dependency delivery — design

**Issue:** [#160](https://github.com/posit-dev/shinyreact/issues/160) — `set_react_page`:
dependencies for dynamically-registered renderers (post-page-load) are never delivered.
Builds on [#87](https://github.com/posit-dev/shinyreact/issues/87) (Layer A — static
session-output harvest).

## Problem

In the `ui.tsx` pattern, `set_react_page()` injects each renderer's `HTMLDependency`
(the JS that *defines* its Shiny output binding) into `<head>` by harvesting renderers
registered at page-generation time (Layer A, #87). A renderer **registered after page
generation** — e.g. a `render_plotly` created inside a `@reactive.effect` and registered
via `get_current_session().output(...)` on a button click, with a React-supplied
`<ShinyOutput>` placeholder — is invisible to that harvest, so its binding-JS dependency
never reaches the client and the widget cannot render.

## Root cause (confirmed empirically)

The defect is **only** the missing dependency — not value delivery.

With a dynamically-registered `render_plotly` + React placeholder:

- The server registers, computes, and **sends the value** — `{"values":{"scatter":{model_id,…}}}`
  and the shinywidgets comm are observed on the WebSocket.
- But `script[src*='ipywidget-output-binding']` is **absent** (`dep_scripts=0`), so Shiny
  has no binding registered for `shiny-ipywidget-output`; the element is **never bound**
  (`bound=0`); nothing renders.
- **Proof it is purely the dependency:** adding a `ui.hold()`-ed warm-up `render_plotly`
  at top level (so Layer A injects the binding JS at startup) makes the *dynamically*
  registered output bind and render (`dep=2, bound=1, plotly=1`).
- A built-in binding (`render.text`, whose JS ships in core `shiny.js`) works dynamically
  with no issue, confirming the gap is the dependency, not value delivery.

**Lynchpin for the fix** — Shiny's client replays a stored value when an element binds:

```js
// shiny.min.js
async bindOutput(e,t){ ...; this.$bindings[e]=t,
  this.$values[e]!==void 0 ? await t.onValueChange(this.$values[e]) : ... }
```

So a value that arrives *before* its binding exists is stored in `$values` and rendered
the moment the binding is registered and `bindAll` runs. The fix can therefore deliver the
dependency *after* the value and still render correctly.

## Scope

- **A (fix):** automatically deliver dependencies for renderers registered after page load.
- **C (proof):** add an app/test proving client-owned mounting of a *pre-registered*
  renderer works (React mounts the `<ShinyOutput>` on demand; dep already in `<head>`).
- **B (already works, untouched):** server-delivered dynamic UI via `@render.ui` /
  `insert_ui` injects deps through Shiny's native path — covered by the existing
  `test_dynamic_ui_plotly_dep`.

## Design

### Server — flush-diff dependency watcher (`pkg-py/src/shinyreact/_page.py`)

`set_react_page()` runs in both Express passes. Only on the **server pass** (a real
session, `get_current_session()` is not `None` and `not session.is_stub_session()`),
register a flush watcher:

```python
session = get_current_session()
if session is not None and not session.is_stub_session():
    _register_dynamic_dep_pusher(session)
```

```python
def _register_dynamic_dep_pusher(session: Session) -> None:
    seen: set[str] = set()
    first = True

    async def _push_new_deps() -> None:
        nonlocal first
        current = set(session.output._outputs)
        if first:
            # Baseline: everything registered by the first flush is "static" and
            # already harvested into <head> by Layer A. Record, push nothing.
            seen.update(current)
            first = False
            return
        new_names = current - seen
        seen.update(new_names)
        deps: list[Jsonifiable] = []
        for name in new_names:
            ui = session.output._outputs[name].renderer.auto_output_ui()
            if isinstance(ui, (Tag, TagList)):
                # Real session: registers the /lib route AND returns serialized deps.
                deps.extend(session._process_ui(ui)["deps"])
        if deps:
            await session.send_custom_message(
                "shinyReactMessage", {"type": "shinyreact.deps", "data": {"deps": deps}}
            )

    session.on_flushed(_push_new_deps, once=False)
```

Notes:
- `on_flushed(once=False)` fires after every reactive flush; a renderer registered during
  a flush (button-click effect) is in `_outputs` by the time the post-flush callback runs.
- **Baseline on first flush, diff thereafter** avoids re-pushing the static set. Baseline-skip
  is safe: Layer A guarantees static deps are already in `<head>`; only genuinely post-load
  registrations are ever diffed and pushed.
- Re-pushing an already-loaded dep would be harmless anyway (the client de-dups by
  name+version), so the watcher does not track per-dep identity — only output names.
- The message uses `send_custom_message` directly (envelope `shinyReactMessage`, inner
  `type: "shinyreact.deps"`) — **not** the public `send_message`, which namespaces the type
  via `resolve_id`; this internal channel must stay un-namespaced.

### Client — dependency-injection handler (`js/src/index.ts`, `js/src/shiny.d.ts`)

Register an internal handler on the shared shiny-react message registry (the same registry
`useShinyMessageHandler` dispatches through):

```ts
messageRegistry.addHandler("shinyreact.deps", async (data: { deps: unknown[] }) => {
  // Load the binding JS first, THEN bind — order matters: bindAll must see the
  // registered output binding. bindAll is idempotent (skips already-bound elements).
  await window.Shiny.renderDependenciesAsync(data.deps);
  window.Shiny.bindAll(document.body);
});
```

- `renderDependenciesAsync` (awaited) guarantees dependency `<script>`s execute — and their
  output bindings register — before `bindAll` runs.
- On `bindAll`, the newly-registered binding for the React-mounted placeholder picks up the
  value already stored in `$values` (see lynchpin) and renders.
- Extend the ambient `Shiny` type decl with `renderDependenciesAsync?` and `bindAll?`.
- Rebuild + copy via `make update-dist` (updates `js/dist/`, `pkg-py/src/shinyreact/www/`,
  `pkg-r/inst/lib/shiny/`); run `make js-lint`.

If `messageRegistry` is not already exported as a shared singleton from
`js/src/shiny-react/message-registry.ts`, export it and have `useShinyMessageHandler`
consume that same instance, so the internal handler and component handlers share one dispatcher.

### C proof app + tests (`pkg-py/tests/playwright/`)

- **`apps/client_mount_plotly/`** — a `ui.hold()`-ed pre-registered `render_plotly`; the
  React app mounts its `<ShinyOutput>` only after a button click. The dep is in `<head>`
  from startup (Layer A), so client-owned mounting binds + renders **without** Layer B.
  Test: after the click, assert `#scatter .plotly` is attached.
- **`apps/button_add_plotly/`** — button → `@reactive.effect` registers a brand-new
  `render_plotly` via `get_current_session().output(scatter, ...)`; React supplies the
  placeholder. Test: after the click, assert both `script[src*='ipywidget-output-binding']`
  is attached **and** `#scatter .plotly` is attached. This fails without Layer B and passes
  with it — the genuine regression guard.

Both run under `make py-test-e2e` (the Playwright suite excluded from `make py-check-tests`).
Follow `.claude/references/playwright-e2e-tests.md` conventions (3-file fixtures, Express
import marker, explainer paragraph, Rules-of-Hooks, action-button `debounceMs: 0` +
`priority: "event"`).

### Docs & issue

- Issue **#160** filed (this feature's tracking issue).
- Update `docs/todos.md`: dependencies for renderers registered after page load are now
  delivered automatically; note the `ui.hold()` warm-up as the manual escape hatch and the
  opt-out story.
- Update `set_react_page()` docstring: post-load dynamically-registered renderers now get
  their dependencies pushed and injected client-side.
- Update the #87 spec note (`2026-06-10-set-react-page-module-dep-discovery-design.md`):
  Layer B is now **built** under #160 (supersedes the earlier "Layer B not built" note,
  which was correct for the `@render.ui` dynamic-UI case).

## Testing policy

- A fix: `apps/button_add_plotly` e2e test is the regression guard — fails without the
  server watcher + client handler, passes with them.
- C proof: `apps/client_mount_plotly` e2e test.
- Re-run the full `make py-test-e2e` suite plus `make py-check` (lint/types/unit) and
  `make js-lint` after the bundle rebuild.

## Risks / open points

- **Async dependency load vs. `bindAll` ordering** — mitigated by awaiting
  `renderDependenciesAsync` before `bindAll`. Validate in the `button_add_plotly` e2e test;
  if `renderDependenciesAsync` is not exposed on the public `window.Shiny`, fall back to the
  sync `renderDependencies` and confirm the binding JS is registered before `bindAll`.
- **Per-flush cost** — the watcher does a set-difference of output-name keys each flush; O(n)
  in number of outputs, negligible. No per-dep bookkeeping.

## Out of scope

- R counterpart (`page_react_html`) — already tracked separately (R has no renderer
  auto-discovery at all; see the #87 R-asymmetry issue).
- Removing/replacing dependencies when outputs are destroyed — deps are additive and
  de-duplicated client-side; unloading is unnecessary.
