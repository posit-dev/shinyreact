# `set_react_page()` Module Dependency Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `set_react_page()` auto-discover `HTMLDependency` objects from renderers defined inside `@module.server`, so module-only components load their JS/CSS without any user boilerplate.

**Architecture:** At HTML-generation time the Express stub session already holds *every* synchronously-mounted renderer (top-level **and** module) in `session.output._outputs`. The page function harvests their dependencies from there, in addition to the existing `*args` walk. A dynamic-UI test then decides whether a second, websocket-push layer is needed for renderers mounted *after* page load.

**Tech Stack:** Python (shinyreact `pkg-py`), Shiny for Python (Express), pytest, Playwright (`pytest-playwright`, `shiny[playwright]`, `shinywidgets`, `plotly`), TypeScript/React (Vite IIFE bundle) — JS only if Layer B is built.

**Spec:** `docs/superpowers/specs/2026-06-10-set-react-page-module-dep-discovery-design.md`

---

## File Structure

- **Modify** `pkg-py/src/shinyreact/_page.py` — add session-output harvest to `_react_page_fn`; add a `_collect_renderer_deps` helper; import `get_current_session`. (Layer B, if built, adds a per-session flush hook in `set_react_page`.)
- **Create** `pkg-py/tests/test_page_dep_harvest.py` — fast unit test for Layer A (no browser).
- **Modify** `pkg-py/tests/playwright/test_module_dependency.py` — remove the `xfail` on the existing module test.
- **Create** `pkg-py/tests/playwright/apps/dynamic_plotly/{app.py,www/index.html,www/app.js}` — dynamic-UI fixture.
- **Modify** `pkg-py/tests/playwright/test_module_dependency.py` — add the dynamic-UI test.
- **Modify** `pkg-py/src/shinyreact/_page.py` (docstring) and `docs/todos.md` — documentation.
- **Layer B only (conditional):** `js/src/index.ts` (+ `js/src/shiny.d.ts`), then `make update-dist`.

---

## Task 1: Layer A — harvest dependencies from session outputs

**Files:**
- Modify: `pkg-py/src/shinyreact/_page.py`
- Test: `pkg-py/tests/test_page_dep_harvest.py`

- [ ] **Step 1: Write the failing unit test**

Create `pkg-py/tests/test_page_dep_harvest.py`:

```python
"""Layer A: _react_page_fn harvests deps from renderers registered on the
session, including those inside @module.server (issue #87)."""

from __future__ import annotations

from htmltools import HTMLDependency, TagList, div
from shiny.express._stub_session import ExpressStubSession
from shiny.render.renderer import Renderer
from shiny.session import session_context

from shinyreact._page import _build_react_page_fn


def _make_widget_renderer(dep: HTMLDependency) -> type[Renderer]:
    class render_widget(Renderer):  # noqa: N801
        def auto_output_ui(self):
            return div(dep, id=self.output_id, class_="my-widget-output")

        async def transform(self, value):  # pragma: no cover - not exercised
            return value

    return render_widget


def test_react_page_harvests_session_output_deps(tmp_path) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    dep = HTMLDependency("widget-x", "1.0", source={"subdir": str(tmp_path)})
    render_widget = _make_widget_renderer(dep)

    page_fn = _build_react_page_fn(index)

    stub = ExpressStubSession()
    with session_context(stub):
        # Register a renderer the way @module.server would — it lands in
        # stub.output._outputs but is NOT passed to page_fn as an arg.
        @stub.output
        @render_widget
        def thing():  # pragma: no cover - never rendered
            return "x"

        result = page_fn()  # no *args, mirroring a module-only renderer

    dep_names = [d.name for d in TagList(result).get_dependencies()]
    assert "widget-x" in dep_names
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_page_dep_harvest.py -v`
Expected: FAIL — `assert "widget-x" in dep_names` is False (current `_react_page_fn` only walks `*args`, which is empty here).

- [ ] **Step 3: Implement the harvest**

In `pkg-py/src/shinyreact/_page.py`, add `get_current_session` to the imports:

```python
from shiny.render.renderer import Renderer
from shiny.session import get_current_session
```

Add a helper above `_build_react_page_fn`:

```python
def _collect_renderer_deps(renderer: Renderer, deps: list[HTMLDependency]) -> None:
    """Append a renderer's output-UI dependencies to ``deps``.

    Calls ``.tagify()`` first so dependencies that only materialize during
    tagification are resolved (a bare ``get_dependencies()`` on the untagified
    UI can miss them). The page function runs under the Express stub session,
    whose ``_process_ui`` is a no-op, so tagify — not ``session._process_ui`` —
    is the correct resolver here; the resolved deps are emitted into the page
    TagList, and Shiny registers their file routes when it renders the page.
    """
    ui = renderer.auto_output_ui()
    if isinstance(ui, (Tag, TagList)):
        deps.extend(ui.tagify().get_dependencies())
```

Replace the body of `_react_page_fn` with:

```python
    def _react_page_fn(*args: Any) -> Tag:
        deps: list[HTMLDependency] = []

        # Top-level renderers Shiny Express hands to the page function.
        for arg in args:
            if isinstance(arg, Renderer):
                _collect_renderer_deps(arg, deps)

        # Renderers registered on the active session — including those defined
        # inside @module.server, which `*args` never sees (issue #87). At the
        # tagify pass the stub session already holds every synchronously
        # mounted renderer in `output._outputs`.
        session = get_current_session()
        if session is not None:
            for info in session.output._outputs.values():
                _collect_renderer_deps(info.renderer, deps)

        # Shiny de-duplicates dependencies by name+version when hoisting to
        # <head>, so any overlap between the two passes is harmless.
        # page_opts types page_fn as -> Tag, but TagList works at runtime
        return cast(Tag, TagList(_dep_page(), *deps, HTML(index_html)))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest pkg-py/tests/test_page_dep_harvest.py -v`
Expected: PASS.

- [ ] **Step 5: Run the broader Python suite + type check**

Run: `make py-check-tests && make py-check-types`
Expected: PASS (no regressions).

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyreact/_page.py pkg-py/tests/test_page_dep_harvest.py
git commit -m "fix: discover module renderer HTMLDependencies in set_react_page (#87)"
```

---

## Task 2: Flip the existing module xfail to a passing test

**Files:**
- Modify: `pkg-py/tests/playwright/test_module_dependency.py`

- [ ] **Step 1: Remove the xfail marker**

In `pkg-py/tests/playwright/test_module_dependency.py`, delete the
`@pytest.mark.xfail(...)` decorator on `test_module_renderer_dep_injected` (and
the now-unused `import pytest` if nothing else uses it). Leave the
`module_plotly` fixture app **unchanged** — it must keep calling plain
`set_react_page()` so the test proves zero-boilerplate auto-discovery. The
function body stays as-is:

```python
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

module_plotly_app = create_app_fixture("apps/module_plotly/app.py")


def test_module_renderer_dep_injected(
    page: Page, module_plotly_app: ShinyAppProc
) -> None:
    page.goto(module_plotly_app.url)

    # shinywidgets ships an `ipywidget-output-binding` HTMLDependency that
    # render_plotly attaches. With the session-output harvest, set_react_page()
    # now finds it even though the renderer lives inside @module.server.
    expect(
        page.locator("script[src*='ipywidget-output-binding']")
    ).to_be_attached()
```

- [ ] **Step 2: Ensure the e2e env is installed**

Run: `make py-install-e2e`
Expected: `uv sync --group tests-e2e` + `playwright install chromium` complete (installs `shinywidgets`, `plotly`, browser).

- [ ] **Step 3: Run the test to verify it now passes**

Run: `make py-test-e2e PYTEST_ARGS="pkg-py/tests/playwright/test_module_dependency.py::test_module_renderer_dep_injected"`

If the Makefile target does not accept `PYTEST_ARGS`, run directly:
`uv run pytest pkg-py/tests/playwright/test_module_dependency.py::test_module_renderer_dep_injected -o addopts= -v`
Expected: PASS (was xfail before Task 1).

- [ ] **Step 4: Commit**

```bash
git add pkg-py/tests/playwright/test_module_dependency.py
git commit -m "test: module renderer dep is now auto-injected (#87)"
```

---

## Task 3: Dynamic-UI fixture + test (decides whether Layer B is needed)

A checkbox (React state → Shiny input) gates a Plotly chart rendered through
Shiny's **dynamic-UI** path (`@render.ui` → `output_widget`). The chart's
`ipywidget-output-binding` dependency is delivered either by Layer A (the
top-level `render_plotly` is on the session) or by Shiny's native dynamic-UI
dependency injection. Written as `xfail(strict=True)` first; **run it and record
the real outcome** (the user approved deciding xfail-vs-pass empirically).

**Files:**
- Create: `pkg-py/tests/playwright/apps/dynamic_plotly/app.py`
- Create: `pkg-py/tests/playwright/apps/dynamic_plotly/www/index.html`
- Create: `pkg-py/tests/playwright/apps/dynamic_plotly/www/app.js`
- Modify: `pkg-py/tests/playwright/test_module_dependency.py`

- [ ] **Step 1: Create the fixture `app.py`**

`pkg-py/tests/playwright/apps/dynamic_plotly/app.py`:

```python
import plotly.express as px
from shiny.express import input, render, ui  # noqa: F401  # marks Express
from shinyreact import set_react_page
from shinywidgets import output_widget, render_plotly

set_react_page()


# Dynamic UI: the widget placeholder only exists in the DOM once the React
# checkbox sets `input.show()` to True. The dependency that the placeholder
# needs cannot be known from the dynamic UI until it renders.
@render.ui
def holder():
    if not input.show():
        return None
    return output_widget("scatter")


@render_plotly
def scatter():
    return px.scatter(x=[1, 2, 3], y=[1, 4, 9])
```

- [ ] **Step 2: Create the fixture `www/index.html`**

`pkg-py/tests/playwright/apps/dynamic_plotly/www/index.html`:

```html
<p>
  Check the box to reveal a Plotly chart rendered via Shiny dynamic UI
  (<code>@render.ui</code> → <code>output_widget</code>). The
  <code>ipywidget-output-binding</code> dependency must be present for the
  chart to mount.
</p>
<div id="root"></div>
<script src="app.js" defer></script>
```

- [ ] **Step 3: Create the fixture `www/app.js`**

`pkg-py/tests/playwright/apps/dynamic_plotly/www/app.js`:

```js
const { React, ReactDOM, useShinyInitialized, useShinyInput, ShinyOutput } =
  window.shinyreact;
const h = React.createElement;

function App() {
  // Both hooks run on every render (Rules of Hooks); the early return below
  // is safe because no hooks follow it.
  const initialized = useShinyInitialized();
  const [show, setShow] = useShinyInput("show", false, { priority: "event" });
  if (!initialized) return null;

  return h(
    "div",
    { "data-test": "container" },
    h("input", {
      type: "checkbox",
      id: "show",
      checked: show,
      onChange: (e) => setShow(e.target.checked),
    }),
    // Hosts Shiny's dynamic @render.ui output; bindAll lets Shiny inject the
    // dependency for whatever the dynamic UI renders.
    h(ShinyOutput, { id: "holder", className: "shiny-html-output" }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

- [ ] **Step 4: Add the test (as strict xfail first)**

Append to `pkg-py/tests/playwright/test_module_dependency.py`:

```python
dynamic_plotly_app = create_app_fixture("apps/dynamic_plotly/app.py")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Provisional: verifying whether a checkbox-gated Plotly chart "
        "rendered via dynamic UI mounts under set_react_page(). Outcome is "
        "determined empirically — see issue #87."
    ),
)
def test_dynamic_ui_plotly_dep(page: Page, dynamic_plotly_app: ShinyAppProc) -> None:
    page.goto(dynamic_plotly_app.url)

    # Before checking the box, no chart is shown.
    page.locator("#show").check()

    # The ipywidgets binding dependency must be loaded...
    expect(
        page.locator("script[src*='ipywidget-output-binding']")
    ).to_be_attached()
    # ...and the Plotly chart must actually render inside the dynamic holder.
    expect(page.locator("#holder .plotly").first).to_be_attached()
```

(Re-add `import pytest` at the top of the file if Task 2 removed it.)

- [ ] **Step 5: Run the test and record the outcome**

Run: `uv run pytest pkg-py/tests/playwright/test_module_dependency.py::test_dynamic_ui_plotly_dep -o addopts= -v`

Interpret the result:
- **XPASS reported as a failure** (strict xfail but the test actually passed): the dynamic case works without extra machinery. Go to Step 6.
- **XFAIL** (the assertions genuinely fail): the dynamic case is not handled natively. Go to Step 7.

- [ ] **Step 6: If it passes — remove the xfail and finalize**

Delete the `@pytest.mark.xfail(...)` decorator from `test_dynamic_ui_plotly_dep`
and update the reason text into a plain docstring noting that Layer A /
Shiny's native dynamic-UI injection covers this case. Re-run:
`uv run pytest pkg-py/tests/playwright/test_module_dependency.py::test_dynamic_ui_plotly_dep -o addopts= -v` → Expected: PASS.

Then record in the spec's "Dynamic-UI test" section: *"Outcome: passes natively;
Layer B not built."* **Skip Task 4 entirely.**

- [ ] **Step 7: If it fails — keep the xfail for now**

Leave the strict `xfail` in place (it currently documents the gap) and proceed
to **Task 4** to build Layer B. Task 4 ends by flipping this test to passing.

- [ ] **Step 8: Commit**

```bash
git add pkg-py/tests/playwright/apps/dynamic_plotly pkg-py/tests/playwright/test_module_dependency.py
git commit -m "test: dynamic-UI plotly dependency under set_react_page (#87)"
```

---

## Task 4: Layer B — flush-diff dependency push (CONDITIONAL — only if Task 3 failed natively)

> **Skip this entire task if Task 3 Step 5 reported the test passing.** This layer adds a per-session server hook plus a client message handler; build it only when the dynamic case is proven not to work natively.

**Files:**
- Modify: `pkg-py/src/shinyreact/_page.py` (add per-session hook in `set_react_page`)
- Modify: `js/src/index.ts` and `js/src/shiny.d.ts`
- Then: `make update-dist`

- [ ] **Step 1: Add the JS dependency-injection handler**

In `js/src/shiny.d.ts`, extend the ambient `Shiny` const with the optional
client API used here (add inside the `const Shiny: {...}` block):

```ts
    renderDependencies?: (deps: unknown[]) => void;
```

In `js/src/index.ts`, after `window.shinyreact = Object.assign(...)`, register a
built-in handler on the shared message registry. Import the registry singleton
(it is the same instance `useShinyMessageHandler` uses — confirm the export name
in `js/src/shiny-react/message-registry.ts`; it exposes a module-level registry):

```ts
import { messageRegistry } from "./shiny-react/message-registry";

// Inject HTMLDependencies pushed by the server for renderers that mount after
// page load (e.g. dynamically-mounted modules). Uses Shiny's own dependency
// injector so <script>/<link> tags land exactly as renderUI would emit them.
messageRegistry.addHandler("shinyreact.deps", (data: { deps: unknown[] }) => {
  window.Shiny?.renderDependencies?.(data.deps);
});
```

If `message-registry.ts` does not already export a shared instance, add:
`export const messageRegistry = new ShinyMessageRegistry();` and make
`useShinyMessageHandler` consume that same export, so the dispatcher is shared.

- [ ] **Step 2: Add the per-session flush hook in `set_react_page`**

In `pkg-py/src/shinyreact/_page.py`, at the end of `set_react_page`, after the
`page_opts(...)` call, register the pusher when running under a real session
(the per-session server pass), and add the helper:

```python
    page_opts(page_fn=_build_react_page_fn(index_path))

    # During the per-session server pass, watch for renderers that mount after
    # page generation (e.g. dynamically-mounted modules) and push their
    # dependencies to the client. The UI/tagify pass runs under a stub session,
    # which we skip — those deps are already harvested into <head>.
    session = get_current_session()
    if session is not None and not session.is_stub_session():
        _register_dynamic_dep_pusher(session)


def _register_dynamic_dep_pusher(session: Session) -> None:
    seen: set[str] = set()

    async def _push_new_deps() -> None:
        new_deps: list[Jsonifiable] = []
        for name, info in session.output._outputs.items():
            if name in seen:
                continue
            seen.add(name)
            ui = info.renderer.auto_output_ui()
            if isinstance(ui, (Tag, TagList)):
                # Real session: _process_ui registers file routes AND returns
                # client-injectable serialized deps.
                rendered = session._process_ui(ui)
                new_deps.extend(rendered["deps"])
        if new_deps:
            await session.send_custom_message(
                "shinyReactMessage",
                {"type": "shinyreact.deps", "data": {"deps": new_deps}},
            )

    session.on_flushed(_push_new_deps, once=False)
```

Add the needed imports/typing to `_page.py`:

```python
from shiny.session import Session, get_current_session
from shiny.types import Jsonifiable
```

- [ ] **Step 3: Rebuild the JS bundle and copy to packages**

Run: `make update-dist`
Expected: `js/dist/shinyreact.js` rebuilt and copied to `pkg-py/src/shinyreact/www/` (and `pkg-r/inst/lib/shiny/`). Also run `make js-lint` → Expected: PASS.

- [ ] **Step 4: Flip the dynamic test to passing**

Remove the `@pytest.mark.xfail(...)` from `test_dynamic_ui_plotly_dep`. Run:
`uv run pytest pkg-py/tests/playwright/test_module_dependency.py::test_dynamic_ui_plotly_dep -o addopts= -v`
Expected: PASS.

- [ ] **Step 5: Record the outcome and commit**

Record in the spec's "Dynamic-UI test" section: *"Outcome: failed natively;
Layer B built."*

```bash
git add pkg-py/src/shinyreact/_page.py pkg-py/src/shinyreact/www js/dist js/src \
        pkg-r/inst/lib/shiny pkg-py/tests/playwright/test_module_dependency.py \
        docs/superpowers/specs/2026-06-10-set-react-page-module-dep-discovery-design.md
git commit -m "feat: push dynamically-mounted renderer deps to client (#87)"
```

---

## Task 5: Documentation + R asymmetry issue

**Files:**
- Modify: `pkg-py/src/shinyreact/_page.py` (docstring)
- Modify: `docs/todos.md`

- [ ] **Step 1: Update the `set_react_page` docstring**

Add a paragraph to `set_react_page`'s docstring (after the existing note about
dependency discovery):

```
    Renderers defined inside ``@module.server`` are discovered too: every
    renderer mounted while the app body runs is found via the session's
    registered outputs, so module components load their JS/CSS with no extra
    configuration. Renderers mounted *dynamically after page load* (e.g. a
    module server called inside a ``@reactive.effect``) rely on Shiny's
    dynamic-UI dependency injection to deliver their dependencies.
```

- [ ] **Step 2: Add a `docs/todos.md` note**

Append a short entry to `docs/todos.md`:

```markdown
## Dynamically-mounted module dependencies in the `ui.tsx` pattern

`set_react_page()` auto-discovers `HTMLDependency` objects from every renderer
mounted while the app body runs, including those inside `@module.server`
(issue #87). Renderers mounted *dynamically after page load* (a module server
called from a `@reactive.effect`) are not in the initial page; they depend on
Shiny's dynamic-UI dependency injection. If a future case needs server-pushed
dependency injection for those, see the Layer B design in
`docs/superpowers/specs/2026-06-10-set-react-page-module-dep-discovery-design.md`.
```

- [ ] **Step 3: Run format + the fast suite**

Run: `make py-format && make py-check-tests`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add pkg-py/src/shinyreact/_page.py docs/todos.md
git commit -m "docs: note module dependency discovery in set_react_page (#87)"
```

- [ ] **Step 5: File the R asymmetry GitHub issue**

R's `page_react_html()` is a plain UI function used as `shinyApp(ui = ...)` and
performs no renderer auto-discovery, so module dependencies are not found there
either — a separate concern from this Python fix.

Run:

```bash
gh issue create \
  --title "page_react_html() does not auto-discover renderer HTMLDependencies (R counterpart of #87)" \
  --body "$(cat <<'EOF'
Python's \`set_react_page()\` discovers \`HTMLDependency\` objects from renderers
(including those inside \`@module.server\`) by harvesting the session's
registered outputs at page-generation time — see #87 and
\`docs/superpowers/specs/2026-06-10-set-react-page-module-dep-discovery-design.md\`.

R's \`page_react_html()\` (pkg-r/R/page.R) is a plain UI function used directly as
\`shinyApp(ui = page_react_html())\`. It does **no** renderer dependency discovery
at all — it only reads the HTML file and prepends the shinyreact page dependency.
So downstream package dependencies attached by renderers (top-level **or**
module) are never injected into \`<head>\` on the R side.

Decide whether R should mirror Python's session-output harvest (and how, given R
Shiny's UI/server split differs from Express's two-pass model), or document the
limitation and rely on an explicit dependency mechanism.

Related: #87.
EOF
)"
```

Expected: prints the new issue URL. If `gh` is not authenticated, surface the
issue title/body to the user to file manually.

---

## Self-Review Notes

- **Spec coverage:** Layer A → Task 1; existing xfail flip → Task 2; dynamic-UI test → Task 3; Layer B (conditional) → Task 4; docs + R issue → Task 5. All spec sections mapped.
- **Evidence gate:** Task 3 Step 5 explicitly branches; Task 4 is skipped on a native pass. No work is done speculatively.
- **Type/name consistency:** `_collect_renderer_deps` (Task 1) is the shared helper for both walks; `_register_dynamic_dep_pusher` + `"shinyreact.deps"` message type are consistent between the Python sender (Task 4 Step 2) and JS handler (Task 4 Step 1).
- **Stub vs real session:** Layer A uses `.tagify()` (stub session's `_process_ui` is a no-op); Layer B uses `session._process_ui` (real session) — this distinction is called out where each is used.
