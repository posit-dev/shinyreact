# Adding a Playwright e2e test

Reference for adding browser e2e tests to shinyreact. Linked from `CLAUDE.md`'s **Testing policy** section.

Tests live at `pkg-py/tests/playwright/`. They use `pytest-playwright` + py-shiny's `create_app_fixture` — each test gets its own spartan Shiny app booted as a subprocess. Run with `make py-test-e2e`. The `[tool.pytest.ini_options]` block in `pyproject.toml` ignores this subtree by default so `make py-check-tests` stays fast; `py-test-e2e` clears that with `-o addopts=`.

## 1. Spartan fixture app under `pkg-py/tests/playwright/apps/<name>/`

Each fixture is the smallest Shiny app that exercises one assertion target. Three files:

### `app.py`

Decorate one server function with whatever you're testing (`@reactive_output`, `@render.data_frame`, `@render_plotly`, …) and call `set_react_page()`.

**Every `app.py` MUST import something from `shiny.express`** (e.g. `from shiny.express import render`, with `# noqa: F401` if unused). Without that import, Shiny doesn't recognise the file as Express and `set_react_page()` raises `RuntimeError: No top-level recall context manager has been set`. `@render_plotly` (shinywidgets) and `@reactive_output` (shinyreact) do **not** trigger Express recognition on their own.

### `www/index.html`

Minimal bootstrap: optional `<style>` block, `<div id="root"></div>`, `<script src="app.js" defer></script>`. `shinyreact.js` is auto-injected by `set_react_page()` — do **not** add a `<script>` tag for it.

**`set_react_page()` caches `www/index.html` at process startup** (see [issue #82](https://github.com/posit-dev/shinyreact/issues/82)). After editing `index.html`, stop and restart the Shiny server — a browser hard-refresh alone won't help.

### `www/app.js`

No-build, no-JSX React. Gate render on `useShinyInitialized()`, wrap the `ShinyOutput` in `<div data-test="container">` so the direct-child assertions bite.

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    h(ShinyOutput, { id: "my_output" /* … */ }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

**Render a short "expected behaviour" paragraph at the top of the app.** One or two sentences in a `<p>` (or rendered `<code>` for URL fragments / expected values) describing what the page should look like after the test runs successfully. When a Playwright assertion fails and you need to debug by booting the fixture (`uv run shiny run --port 8101 …`), the rendered explainer tells you in seconds what should be on screen — far faster than rereading the test source to reverse-engineer the contract. Keep it terse; this is for the person at the keyboard, not for end users.

Rules-of-Hooks reminder: every hook the component calls (`useShinyInput`, `useShinyOutputValue`, `useSetShinyInput`, …) MUST run on every render. Calling `useShinyInitialized()` and then `return null` is only safe when no other hooks are called afterward — i.e. all you do is render a `<ShinyOutput>` (whose hooks live in its own component). If `App` itself calls additional hooks, drop the `useShinyInitialized()` early-return and let those hooks short-circuit internally on the not-yet-initialised state.

## 2. Add a fixture line + test to `test_shiny_output.py`

```python
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

my_app = create_app_fixture("apps/<name>/app.py")  # path relative to this test file

def test_my_thing(page: Page, my_app: ShinyAppProc) -> None:
    page.goto(my_app.url)
    ...
```

## 3. Assertion patterns proven out by the existing suite

### No-wrapper guarantee (the #61 / #75 regression guard)

```python
expect(page.locator("[data-test=container] > #my_id")).to_be_attached()
```

The `>` combinator fails if any wrapper sneaks back in between the container and the output.

### Direct-child CSS check (same regression, demonstrable visually)

Paint a hot-pink outline on direct children only in the fixture's `index.html`:

```html
<style>
  [data-test="container"] > * {
    outline: 3px solid hotpink;
    outline-offset: 4px;
  }
</style>
```

…and assert in the test:

```python
expect(loc).to_have_css("outline-style", "solid")
expect(loc).to_have_css("outline-color", "rgb(255, 105, 180)")
```

A wrapper would steal the selector match and leave the output at its default outline.

Custom elements (`<shiny-data-frame>`) default to `display: inline`; add `display: inline-block` (or `block`) on the host in the same `<style>` block, or the outline visually collapses onto the rendered content (test still passes, but the manual-viewing demo doesn't work).

### Empty outputs

Use `to_be_attached()` instead of `to_be_visible()`. A `<div>` with no content has a 0×0 box and Playwright reports it "hidden".

### Class assertions

Order-tolerant via `to_have_class(re.compile(r"\bclass-name\b"))`. Shiny adds `shiny-bound-output` after the binding pass, so exact-string matches are brittle.

### `<ShinyOutput>` adds no classes of its own

Caller-supplied classes are the full set on the rendered element (plus whatever Shiny's binding adds later).

## 4. Running locally

```bash
make py-install-e2e   # one-time: uv sync + playwright install chromium
make py-test-e2e      # the suite
```

When iterating manually, `uv run shiny run --port 8101 pkg-py/tests/playwright/apps/<name>/app.py` boots a fixture for browser viewing. Remember the index.html cache (see issue #82) — restart the server after each `www/` edit.

## 5. CI uses Docker for the browser

Composite action at `.github/shinyreact/setup-playwright-remote/action.yaml` (cribbed from py-shiny PRs [#2208](https://github.com/posit-dev/py-shiny/pull/2208) and [#2228](https://github.com/posit-dev/py-shiny/pull/2228) — avoids the ~5% chance of a 30-minute `playwright install` hang from the CDN).

The `connect_options` fixture in `pkg-py/tests/playwright/conftest.py` reads `PW_TEST_CONNECT_WS_ENDPOINT` and tells pytest-playwright to call `browser_type.connect()` instead of `.launch()`. Locally the env var is unset and the launch path is used unchanged — no special setup beyond `make py-install-e2e`.
