# Playwright e2e tests for `ShinyOutput` (issue #59)

**Date:** 2026-05-08
**Status:** Design approved, ready for implementation plan
**Closes:** #59 (after PR merges)

## Context

Issue #59 asks for browser tests covering `ShinyOutput` when it wraps custom Shiny outputs (`@render.data_frame`, `@render_plotly`) and when a custom `className` is applied. PR #75 already removed the wrapper `<div>` from `ShinyOutput` and verified the dataframe + plotly cases by hand, plus added jsdom unit tests for the no-wrapper guarantee. The remaining gap is **automated browser coverage** in a real browser.

The repo currently has zero browser-test infrastructure — this work introduces the first Playwright tests. `decisions/2026-03-17-playwright-testing-architecture.md` recommends a long-term "TS as source of truth + codegen to Python/R" architecture, but that work is deferred and has open questions (codegen mechanism, R bindings). This spec deliberately does **not** start that architecture; it lands the smallest defensible test infrastructure and uses py-shiny's existing pytest-playwright fixtures so we can move forward today.

## Goals

- Automated Playwright tests for the three scenarios listed in #59:
  1. `@render.data_frame` nested in `ShinyOutput`
  2. `@render_plotly` (shinywidgets) nested in `ShinyOutput`
  3. Custom `className` (and arbitrary HTML attributes) land on the rendered element with no wrapper between
- CI integration that gates PRs on these tests passing.
- Establish the test-authoring pattern for future browser coverage in this repo.

## Non-goals

- R-side e2e tests (R package is still a placeholder).
- Codegen / TypeScript controller layer (decision doc territory; revisit later).
- Browser matrix beyond chromium.
- Python-version matrix for e2e.
- webkit/firefox, sharding, or py-shiny's Docker-based `setup-playwright-remote`.
- Converting `examples/ui-tsx/06-data-frame` or `07-plotly` into test fixtures (kept separate so example tweaks don't break tests).

## Architecture

**Test stack:** pytest + `pytest-playwright` + Python Playwright API + py-shiny's `local_app` fixture (from `shiny.pytest`). `local_app` boots a `ShinyAppProc` per test (own port, own Python subprocess), parametrized with the path to one of our spartan apps.

**Layout:**

```
pkg-py/tests/playwright/
  apps/
    data_frame/
      app.py
      www/
        index.html
        app.js
    plotly/
      app.py
      www/
        index.html
        app.js
    classname/
      app.py
      www/
        index.html
        app.js
  conftest.py
  test_shiny_output.py
```

**Why pytest-playwright over `@playwright/test`:** py-shiny exposes `local_app` and friends via `shiny.pytest`, which handles app boot, port allocation, and teardown for free. Using the JS test runner would force us to reimplement that lifecycle in `playwright.config.ts`'s `webServer` block. The trade-off: this walks back the decision doc's "TS as source of truth" direction. Acceptable — when codegen lands, these tests become an *example consumer* of generated controllers rather than the source.

## Spartan fixture apps

Each fixture is the smallest Shiny app that exercises one assertion target. No sliders, greetings, or styling beyond what tests inspect.

### `apps/data_frame/app.py`

```python
import pandas as pd
from shiny.express import render
from shinyreact import set_react_page

set_react_page()

@render.data_frame
def my_table():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})
```

### `apps/data_frame/www/app.js`

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h("div", { "data-test": "container" },
    h(ShinyOutput, { id: "my_table", tagName: "shiny-data-frame" }));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

### `apps/plotly/app.py`

```python
import plotly.express as px
from shinyreact import set_react_page
from shinywidgets import render_plotly

set_react_page()

@render_plotly
def scatter():
    return px.scatter(x=[1, 2, 3], y=[1, 4, 9])
```

### `apps/plotly/www/app.js`

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h("div", { "data-test": "container" },
    // Plotly renders 0×0 without explicit sizing on the host element.
    h(ShinyOutput, {
      id: "scatter",
      className: "shiny-ipywidget-output shiny-report-size",
      style: { width: "100%", height: "300px" },
    }));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

### `apps/classname/app.py`

```python
from shinyreact import reactive_output, set_react_page

set_react_page()

@reactive_output
def out():
    return "hi"
```

### `apps/classname/www/app.js`

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h("div", { "data-test": "container" },
    h(ShinyOutput, { id: "out", className: "custom-a custom-b", "data-test-marker": "x" }));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

### Shared fixture concerns

- Each `www/index.html` is the standard ~15-line shinyreact bootstrap copied from `examples/ui-tsx/01-hello/www/index.html` (loads `/shinyreact/shinyreact.js` and renders into `<div id="root">`).
- Every fixture wraps `ShinyOutput` in `<div data-test="container">` to give tests a stable "is this a direct child?" anchor.
- Every fixture gates render on `useShinyInitialized()`. `ShinyOutput`'s bind effect runs once with `[id, tagName]` deps; without the gate, the effect can fire before `window.Shiny.bindAll` exists and the element never binds. This matches the documented pattern in every existing example.
- Fixtures are deliberately not added to docs/examples or to `make py-check`. They are test-only.

## The three tests

All in `pkg-py/tests/playwright/test_shiny_output.py`. Each parametrizes `local_app` with the relevant fixture path, navigates the page, and asserts.

### Test 1: `test_data_frame_renders_inside_shiny_output`

Uses `apps/data_frame/`.

- `expect(page.locator("shiny-data-frame#my_table")).to_be_visible()` — the data-frame element renders.
- `expect(page.locator("shiny-data-frame#my_table")).to_contain_text("1")` — at least one cell of the dataframe is rendered (smoke check that the binding fired).
- `expect(page.locator("[data-test=container] > shiny-data-frame#my_table")).to_be_attached()` — direct-child assertion (no wrapper).

### Test 2: `test_plotly_renders_inside_shiny_output`

Uses `apps/plotly/`.

- `expect(page.locator("#scatter")).to_be_visible()` — host element renders.
- `expect(page.locator("#scatter .js-plotly-plot")).to_be_visible()` — plotly attached its SVG/canvas inside.
- `expect(page.locator("[data-test=container] > #scatter")).to_be_attached()` — direct-child assertion.

### Test 3: `test_custom_classname_lands_on_rendered_element`

Uses `apps/classname/`.

- `expect(page.locator("#out")).to_be_visible()`
- Order-tolerant class assertions (only the classes the caller passed; `<ShinyOutput>` does not add any classes of its own):
  - `expect(loc).to_have_class(re.compile(r"\bcustom-a\b"))`
  - `expect(loc).to_have_class(re.compile(r"\bcustom-b\b"))`
- `expect(loc).to_have_attribute("data-test-marker", "x")` — arbitrary HTML attributes pass through.
- `expect(page.locator("[data-test=container] > #out")).to_be_attached()` — direct-child assertion.

The `>` combinator in the direct-child selector is what enforces "no wrapper between". If a wrapper regression sneaks back in, the selector stops matching and the test fails with a clear locator error.

## Dependencies, build, and CI

### `pyproject.toml`

New dependency group `tests-e2e`:

- `pytest-playwright`
- `shiny[playwright]` (pulls in `playwright` and the `local_app` fixture)
- `shinywidgets`
- `plotly`
- `pandas`

`make py-check-tests` keeps its current scope. E2e is opt-in.

### Makefile

```make
.PHONY: py-install-e2e
py-install-e2e:  ## [py] Install Playwright browsers for e2e tests
	uv sync --group tests-e2e
	uv run playwright install --with-deps chromium

.PHONY: py-test-e2e
py-test-e2e:  ## [py] Run Playwright e2e tests (chromium)
	uv run pytest pkg-py/tests/playwright --browser chromium
```

### CI

New job `playwright-e2e` in `.github/workflows/check-py.yaml`, mirroring py-shiny's structure but trimmed:

- `ubuntu-latest`, single Python (3.12), chromium only.
- Cache `~/.cache/ms-playwright` keyed on the resolved Playwright version (looked up from `uv.lock`).
- Steps: checkout → uv setup → `uv sync --group tests-e2e` → restore browser cache → `playwright install --with-deps chromium` (no-op on cache hit) → `make py-test-e2e`.
- `actions/upload-artifact@v4` of `test-results/` on failure (Playwright traces + screenshots), 5-day retention.
- Runs on PRs to main and pushes to main. Not on draft PRs (mirroring py-shiny's draft pruning).

Playwright invocation passes `--tracing=retain-on-failure --screenshot=only-on-failure` so artifact uploads have something useful in them.

## Edge cases and operational notes

- **Test isolation:** `local_app` gives each test its own `ShinyAppProc` (own port, own subprocess). Tests are safe to run in parallel later if we add `pytest-xdist`; this PR keeps it serial.
- **Init pause:** Tests rely on Playwright's auto-retry through `to_be_visible()` to wait through Shiny initialization. No explicit `wait_for_function` is needed.
- **className order:** React may reorder classes in some configurations. Tests assert with `re.compile(r"\bclass\b")` per class rather than an exact string match.
- **Plotly host sizing:** Without explicit `width`/`height` on the host element, Plotly renders at 0×0 and tests can't find the SVG. The fixture comment documents this so future maintainers don't strip the style block.

## Summary of files changed

New:

- `pkg-py/tests/playwright/conftest.py`
- `pkg-py/tests/playwright/test_shiny_output.py`
- `pkg-py/tests/playwright/apps/{data_frame,plotly,classname}/app.py`
- `pkg-py/tests/playwright/apps/{data_frame,plotly,classname}/www/{index.html,app.js}`

Modified:

- `pyproject.toml` — add `tests-e2e` dep group.
- `Makefile` — add `py-install-e2e` and `py-test-e2e` targets.
- `.github/workflows/check-py.yaml` — add `playwright-e2e` job.
- `docs/todos.md` — remove the "automated playwright coverage for #59" entry once tests land.
