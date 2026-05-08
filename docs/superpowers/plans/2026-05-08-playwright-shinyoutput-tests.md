# Playwright e2e tests for `ShinyOutput` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automated Playwright e2e tests covering `ShinyOutput` for `@render.data_frame`, `@render_plotly`, and custom-className use, gated by CI. Closes #59.

**Architecture:** pytest-playwright + py-shiny's `local_app` fixture. Three spartan Shiny apps under `pkg-py/tests/playwright/apps/`. Three tests in `pkg-py/tests/playwright/test_shiny_output.py` use `create_app_fixture` to boot each spartan app and assert against the rendered DOM. New `tests-e2e` dependency group, new `make py-test-e2e` target, and a new `playwright-e2e` job in `.github/workflows/check-py.yaml`. Default pytest discovery is configured to skip the `playwright/` subtree so `make py-check-tests` keeps working as before.

**Tech Stack:** Python 3.12, pytest, pytest-playwright, `shiny[playwright]` (`local_app`, `create_app_fixture`), shinywidgets, plotly, pandas. JS fixture clients are no-build (use `window.shinyreact` + `React.createElement`).

**Spec:** `docs/superpowers/specs/2026-05-08-playwright-shinyoutput-tests-design.md`

---

## File Structure

**New files:**

```
pkg-py/tests/playwright/
  conftest.py                                 # marker: file is a pytest dir; can stay empty
  test_shiny_output.py                        # the three tests + create_app_fixture wiring
  apps/
    classname/
      app.py
      www/index.html
      www/app.js
    data_frame/
      app.py
      www/index.html
      www/app.js
    plotly/
      app.py
      www/index.html
      www/app.js
docs/superpowers/plans/2026-05-08-playwright-shinyoutput-tests.md   # this file
```

**Modified files:**

- `pyproject.toml` — add `tests-e2e` dep group + `[tool.pytest.ini_options]` to ignore the `playwright/` subtree by default.
- `Makefile` — add `py-install-e2e` and `py-test-e2e` targets.
- `.github/workflows/check-py.yaml` — add `playwright-e2e` job.

**Why this structure:**

- One spartan app per assertion target keeps test failures legible — when test 2 fails you know it's plotly. `local_app` parametrization lets us share the test file.
- Each fixture's `app.py` + `www/{index.html,app.js}` matches the exact layout used by `examples/ui-tsx/01-hello/`, so `set_react_page()` (which resolves `www/index.html` relative to the calling app file) works without any path arguments.
- E2e tests live next to unit tests but in a separate subtree (`pkg-py/tests/playwright/`) excluded from default discovery, so existing CI workflow stays fast.

---

## Task 1: Add `tests-e2e` dep group and pytest config

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `tests-e2e` dep group and pytest ini config**

Edit `pyproject.toml`. Add a new entry inside `[dependency-groups]` (after the `dev` group ends, before any other top-level section) and add a new `[tool.pytest.ini_options]` section after `[tool.pyright]`.

After editing, the relevant blocks should read exactly:

```toml
[dependency-groups]
examples = [
    "matplotlib>=3.8.0",
    "numpy>=1.26.0",
    "pandas>=2.1.0",
    "python-dotenv>=1.0.0",
    "chatlas>=0.1.0",
    "shinywidgets>=0.8.0",
    "plotly>=6.7.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pyright>=1.1.0",
    "ruff>=0.6.0",
    "pytest-cov>=5.0.0",
    "tox>=4.0.0",
    "tox-uv>=1.0.0",
    "pre-commit>=4.0.0",
]
tests-e2e = [
    "pytest-playwright>=0.5.0",
    "shiny[playwright]>=1.2.0",
    "shinywidgets>=0.8.0",
    "plotly>=6.7.0",
    "pandas>=2.1.0",
]

[tool.pyright]
include = ["pkg-py/src/shinyreact"]
pythonVersion = "3.10"
typeCheckingMode = "basic"

[tool.pytest.ini_options]
testpaths = ["pkg-py/tests"]
addopts = "--ignore=pkg-py/tests/playwright"
```

- [ ] **Step 2: Verify the existing unit tests still discover correctly**

Run: `uv run pytest --collect-only`
Expected: collects all current tests under `pkg-py/tests/` *except* anything in `pkg-py/tests/playwright/` (which doesn't exist yet — this should pass as a no-op confirmation that the ignore directive parses).

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore(py): add tests-e2e dep group and scope pytest discovery"
```

---

## Task 2: Add Makefile targets

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add the two new targets**

Open `Makefile`. Find the `py-format` target (around line 153). Insert two new targets immediately after it. The inserted block:

```make
.PHONY: py-install-e2e
py-install-e2e:  ## [py] Install Playwright browsers for e2e tests
	@echo "🆙 Installing Playwright browsers"
	uv sync --group tests-e2e
	uv run playwright install --with-deps chromium

.PHONY: py-test-e2e
py-test-e2e:  ## [py] Run Playwright e2e tests (chromium)
	@echo "🧪 Running Playwright e2e tests"
	uv run pytest pkg-py/tests/playwright --browser chromium -o addopts=
```

The `-o addopts=` clears the global `--ignore=pkg-py/tests/playwright` from pytest ini so this command can actually collect the e2e tests.

- [ ] **Step 2: Verify Makefile parses and lists the new targets**

Run: `make help | grep e2e`
Expected output (order may vary):

```
  py-install-e2e        [py] Install Playwright browsers for e2e tests
  py-test-e2e           [py] Run Playwright e2e tests (chromium)
```

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore(py): add py-install-e2e and py-test-e2e targets"
```

---

## Task 3: Install Playwright browsers locally

**Files:** none (env-only)

- [ ] **Step 1: Sync the e2e dep group and install chromium**

Run: `make py-install-e2e`
Expected: `uv sync --group tests-e2e` succeeds, then `playwright install --with-deps chromium` downloads chromium into `~/.cache/ms-playwright`. On macOS the `--with-deps` part is a no-op; on Linux it installs OS packages via apt.

- [ ] **Step 2: Sanity-check the install**

Run: `uv run playwright --version`
Expected: prints something like `Version 1.NN.N`. Run: `ls ~/.cache/ms-playwright | grep chromium`
Expected: a `chromium-NNNN` directory exists.

(No commit — env state only.)

---

## Task 4: Create the `classname` fixture app

**Files:**
- Create: `pkg-py/tests/playwright/apps/classname/app.py`
- Create: `pkg-py/tests/playwright/apps/classname/www/index.html`
- Create: `pkg-py/tests/playwright/apps/classname/www/app.js`

- [ ] **Step 1: Create the Shiny app file**

Create `pkg-py/tests/playwright/apps/classname/app.py` with exactly:

```python
from shiny.express import render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def out():
    return "hi"
```

The unused `from shiny.express import render` is required: Shiny's CLI uses an
import scan to recognise the file as Shiny Express; without that line,
`set_react_page()` raises `RuntimeError: No top-level recall context manager
has been set.` The same pattern is needed for the other two fixture apps.

- [ ] **Step 2: Create the HTML bootstrap**

Create `pkg-py/tests/playwright/apps/classname/www/index.html` with exactly:

```html
<div id="root"></div>
<script src="app.js" defer></script>
```

- [ ] **Step 3: Create the JS client**

Create `pkg-py/tests/playwright/apps/classname/www/app.js` with exactly:

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    h(ShinyOutput, {
      id: "out",
      className: "custom-a custom-b",
      "data-test-marker": "x",
    }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

- [ ] **Step 4: Smoke-launch the app to confirm it loads**

Run: `uv run shiny run --port 0 pkg-py/tests/playwright/apps/classname/app.py` and Ctrl+C after the URL prints.
Expected: prints something like `INFO: Uvicorn running on http://127.0.0.1:NNNNN` with no Python tracebacks.

(No commit yet — fixture commits with the test in Task 5.)

---

## Task 5: Write the `test_custom_classname_lands_on_rendered_element` test

**Files:**
- Create: `pkg-py/tests/playwright/conftest.py`
- Create: `pkg-py/tests/playwright/test_shiny_output.py`

- [ ] **Step 1: Create empty conftest**

Create `pkg-py/tests/playwright/conftest.py` with exactly:

```python
# Intentionally empty. The shiny pytest plugin auto-registers `local_app` and
# `create_app_fixture`; this file just marks the directory as a pytest root.
```

- [ ] **Step 2: Write the failing test**

Create `pkg-py/tests/playwright/test_shiny_output.py` with exactly:

```python
import re

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

classname_app = create_app_fixture("apps/classname/app.py")


def test_custom_classname_lands_on_rendered_element(
    page: Page, classname_app: ShinyAppProc
) -> None:
    page.goto(classname_app.url)

    out = page.locator("#out")
    # `to_be_attached()` (not `to_be_visible()`): the rendered element has no
    # content, so its box is 0×0 and Playwright would consider it "hidden".
    # We only care about presence + classes + attributes here.
    expect(out).to_be_attached()

    # `<ShinyOutput>` does not add classes of its own; only the caller-supplied
    # ones should be present.
    expect(out).to_have_class(re.compile(r"\bcustom-a\b"))
    expect(out).to_have_class(re.compile(r"\bcustom-b\b"))

    # Arbitrary HTML attributes pass through to the rendered element.
    expect(out).to_have_attribute("data-test-marker", "x")

    # Direct-child assertion: `>` combinator fails if any wrapper sneaks in.
    expect(page.locator("[data-test=container] > #out")).to_be_attached()
```

- [ ] **Step 3: Run the test and verify it passes**

Run: `make py-test-e2e`
Expected: `1 passed` for `test_custom_classname_lands_on_rendered_element`. If it fails, read the error: most likely failure modes are (a) `local_app`/`create_app_fixture` not found — re-run `make py-install-e2e`; (b) DOM not yet ready — Playwright auto-retries `to_be_visible()` for 5s, so timing should not be the issue; (c) class regex doesn't match — inspect the actual `class` attribute via `page.locator("#out").get_attribute("class")` in a debug print and adjust.

- [ ] **Step 4: Commit fixture + first test together**

```bash
git add pkg-py/tests/playwright/conftest.py \
        pkg-py/tests/playwright/test_shiny_output.py \
        pkg-py/tests/playwright/apps/classname
git commit -m "test(py): playwright test for custom className on ShinyOutput"
```

---

## Task 6: Create the `data_frame` fixture app

**Files:**
- Create: `pkg-py/tests/playwright/apps/data_frame/app.py`
- Create: `pkg-py/tests/playwright/apps/data_frame/www/index.html`
- Create: `pkg-py/tests/playwright/apps/data_frame/www/app.js`

- [ ] **Step 1: Create the Shiny app file**

Create `pkg-py/tests/playwright/apps/data_frame/app.py` with exactly:

```python
import pandas as pd
from shiny.express import render
from shinyreact import set_react_page

set_react_page()


@render.data_frame
def my_table():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})
```

- [ ] **Step 2: Create the HTML bootstrap**

Create `pkg-py/tests/playwright/apps/data_frame/www/index.html` with exactly:

```html
<div id="root"></div>
<script src="app.js" defer></script>
```

- [ ] **Step 3: Create the JS client**

Create `pkg-py/tests/playwright/apps/data_frame/www/app.js` with exactly:

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    h(ShinyOutput, { id: "my_table", tagName: "shiny-data-frame" }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

- [ ] **Step 4: Smoke-launch the app to confirm it loads**

Run: `uv run shiny run --port 0 pkg-py/tests/playwright/apps/data_frame/app.py` and Ctrl+C after the URL prints.
Expected: clean startup, no tracebacks.

(No commit yet — fixture commits with the test in Task 7.)

---

## Task 7: Write the `test_data_frame_renders_inside_shiny_output` test

**Files:**
- Modify: `pkg-py/tests/playwright/test_shiny_output.py`

- [ ] **Step 1: Add the data-frame fixture and test**

Edit `pkg-py/tests/playwright/test_shiny_output.py`. After the existing `classname_app = create_app_fixture(...)` line, add a second fixture line and append the new test at the end of the file. The full file should read exactly:

```python
import re

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

classname_app = create_app_fixture("apps/classname/app.py")
data_frame_app = create_app_fixture("apps/data_frame/app.py")


def test_custom_classname_lands_on_rendered_element(
    page: Page, classname_app: ShinyAppProc
) -> None:
    page.goto(classname_app.url)

    out = page.locator("#out")
    # `to_be_attached()` (not `to_be_visible()`): the rendered element has no
    # content, so its box is 0×0 and Playwright would consider it "hidden".
    # We only care about presence + classes + attributes here.
    expect(out).to_be_attached()

    # `<ShinyOutput>` does not add classes of its own; only the caller-supplied
    # ones should be present.
    expect(out).to_have_class(re.compile(r"\bcustom-a\b"))
    expect(out).to_have_class(re.compile(r"\bcustom-b\b"))

    # Arbitrary HTML attributes pass through to the rendered element.
    expect(out).to_have_attribute("data-test-marker", "x")

    # Direct-child assertion: `>` combinator fails if any wrapper sneaks in.
    expect(page.locator("[data-test=container] > #out")).to_be_attached()


def test_data_frame_renders_inside_shiny_output(
    page: Page, data_frame_app: ShinyAppProc
) -> None:
    page.goto(data_frame_app.url)

    table = page.locator("shiny-data-frame#my_table")
    expect(table).to_be_visible()

    # Smoke check: the binding fired and at least one cell from the dataframe
    # rendered. The frame is `{"a": [1, 2], "b": [3, 4]}` — "1" appears as the
    # first value of column "a".
    expect(table).to_contain_text("1")

    # Direct-child assertion: no wrapper between `<div data-test="container">`
    # and the rendered `<shiny-data-frame>` element.
    expect(
        page.locator("[data-test=container] > shiny-data-frame#my_table")
    ).to_be_attached()
```

- [ ] **Step 2: Run only the new test**

Run: `uv run pytest pkg-py/tests/playwright/test_shiny_output.py::test_data_frame_renders_inside_shiny_output --browser chromium -o addopts= -v`
Expected: PASS. If `to_contain_text("1")` fails it likely means `<shiny-data-frame>` rendered an empty grid (binding didn't fire) — confirm by `page.locator("shiny-data-frame#my_table").inner_html()` in a debug breakpoint.

- [ ] **Step 3: Run the full e2e suite to confirm both tests still pass**

Run: `make py-test-e2e`
Expected: `2 passed`.

- [ ] **Step 4: Commit fixture + test together**

```bash
git add pkg-py/tests/playwright/test_shiny_output.py \
        pkg-py/tests/playwright/apps/data_frame
git commit -m "test(py): playwright test for @render.data_frame in ShinyOutput"
```

---

## Task 8: Create the `plotly` fixture app

**Files:**
- Create: `pkg-py/tests/playwright/apps/plotly/app.py`
- Create: `pkg-py/tests/playwright/apps/plotly/www/index.html`
- Create: `pkg-py/tests/playwright/apps/plotly/www/app.js`

- [ ] **Step 1: Create the Shiny app file**

Create `pkg-py/tests/playwright/apps/plotly/app.py` with exactly:

```python
import plotly.express as px
from shiny.express import render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import set_react_page
from shinywidgets import render_plotly

set_react_page()


@render_plotly
def scatter():
    return px.scatter(x=[1, 2, 3], y=[1, 4, 9])
```

`@render_plotly` comes from `shinywidgets`, not `shiny.express`, so an explicit
`from shiny.express import render` is needed to mark the file as Shiny Express
(same reason as the classname fixture in Task 4).

- [ ] **Step 2: Create the HTML bootstrap**

Create `pkg-py/tests/playwright/apps/plotly/www/index.html` with exactly:

```html
<div id="root"></div>
<script src="app.js" defer></script>
```

- [ ] **Step 3: Create the JS client**

Create `pkg-py/tests/playwright/apps/plotly/www/app.js` with exactly:

```js
const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    // Plotly renders 0×0 without explicit sizing on the host element.
    h(ShinyOutput, {
      id: "scatter",
      className: "shiny-ipywidget-output shiny-report-size",
      style: { width: "100%", height: "300px" },
    }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

- [ ] **Step 4: Smoke-launch the app to confirm it loads**

Run: `uv run shiny run --port 0 pkg-py/tests/playwright/apps/plotly/app.py` and Ctrl+C after the URL prints.
Expected: clean startup, no tracebacks.

(No commit yet — fixture commits with the test in Task 9.)

---

## Task 9: Write the `test_plotly_renders_inside_shiny_output` test

**Files:**
- Modify: `pkg-py/tests/playwright/test_shiny_output.py`

- [ ] **Step 1: Add the plotly fixture and test**

Edit `pkg-py/tests/playwright/test_shiny_output.py`. Add the third `create_app_fixture` line and append the third test at the end. The full file should read exactly:

```python
import re

from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

classname_app = create_app_fixture("apps/classname/app.py")
data_frame_app = create_app_fixture("apps/data_frame/app.py")
plotly_app = create_app_fixture("apps/plotly/app.py")


def test_custom_classname_lands_on_rendered_element(
    page: Page, classname_app: ShinyAppProc
) -> None:
    page.goto(classname_app.url)

    out = page.locator("#out")
    # `to_be_attached()` (not `to_be_visible()`): the rendered element has no
    # content, so its box is 0×0 and Playwright would consider it "hidden".
    # We only care about presence + classes + attributes here.
    expect(out).to_be_attached()

    # `<ShinyOutput>` does not add classes of its own; only the caller-supplied
    # ones should be present.
    expect(out).to_have_class(re.compile(r"\bcustom-a\b"))
    expect(out).to_have_class(re.compile(r"\bcustom-b\b"))

    # Arbitrary HTML attributes pass through to the rendered element.
    expect(out).to_have_attribute("data-test-marker", "x")

    # Direct-child assertion: `>` combinator fails if any wrapper sneaks in.
    expect(page.locator("[data-test=container] > #out")).to_be_attached()


def test_data_frame_renders_inside_shiny_output(
    page: Page, data_frame_app: ShinyAppProc
) -> None:
    page.goto(data_frame_app.url)

    table = page.locator("shiny-data-frame#my_table")
    expect(table).to_be_visible()

    # Smoke check: the binding fired and at least one cell from the dataframe
    # rendered. The frame is `{"a": [1, 2], "b": [3, 4]}` — "1" appears as the
    # first value of column "a".
    expect(table).to_contain_text("1")

    # Direct-child assertion: no wrapper between `<div data-test="container">`
    # and the rendered `<shiny-data-frame>` element.
    expect(
        page.locator("[data-test=container] > shiny-data-frame#my_table")
    ).to_be_attached()


def test_plotly_renders_inside_shiny_output(
    page: Page, plotly_app: ShinyAppProc
) -> None:
    page.goto(plotly_app.url)

    host = page.locator("#scatter")
    expect(host).to_be_visible()

    # Plotly attaches its rendered chart with the `js-plotly-plot` class on a
    # descendant of the host. If sizing is missing the chart is 0×0 and this
    # locator becomes invisible.
    expect(host.locator(".js-plotly-plot")).to_be_visible()

    # Direct-child assertion: no wrapper between the container and `#scatter`.
    expect(page.locator("[data-test=container] > #scatter")).to_be_attached()
```

- [ ] **Step 2: Run only the new test**

Run: `uv run pytest pkg-py/tests/playwright/test_shiny_output.py::test_plotly_renders_inside_shiny_output --browser chromium -o addopts= -v`
Expected: PASS. If `.js-plotly-plot` isn't found, the chart is likely rendering at 0×0 — confirm by `host.bounding_box()` in a debug breakpoint and check the `style` attribute on `#scatter`.

- [ ] **Step 3: Run the full e2e suite**

Run: `make py-test-e2e`
Expected: `3 passed`.

- [ ] **Step 4: Commit fixture + test together**

```bash
git add pkg-py/tests/playwright/test_shiny_output.py \
        pkg-py/tests/playwright/apps/plotly
git commit -m "test(py): playwright test for @render_plotly in ShinyOutput"
```

---

## Task 10: Add the `playwright-e2e` CI job

**Files:**
- Modify: `.github/workflows/check-py.yaml`

- [ ] **Step 1: Add the new job**

Edit `.github/workflows/check-py.yaml`. Append the following job after the existing `py-check` job. The full file (after editing) should read exactly:

```yaml
name: check-py

on:
  push:
    branches: [main]
    paths:
      - "pkg-py/**/*"
      - "pyproject.toml"
      - ".github/workflows/check-py.yaml"
  pull_request:
    paths:
      - "pkg-py/**/*"
      - "pyproject.toml"
      - ".github/workflows/check-py.yaml"

permissions:
  contents: read

env:
  UV_VERSION: "0.9.x"

jobs:
  py-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 🚀 Install uv
        uses: astral-sh/setup-uv@v6.1.0
        with:
          version: ${{ env.UV_VERSION }}

      - name: 📦 Install the project
        run: uv sync --all-extras --all-groups

      - name: 📐 Check formatting
        run: make py-check-format

      - name: 🧪 Check tests and types (Python 3.10–3.14)
        run: make py-check-tox

  playwright-e2e:
    if: github.event.pull_request.draft != true
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 🚀 Install uv
        uses: astral-sh/setup-uv@v6.1.0
        with:
          version: ${{ env.UV_VERSION }}

      - name: 📦 Sync e2e deps
        run: uv sync --group tests-e2e

      - name: 🗂  Cache Playwright browsers
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-${{ runner.os }}-${{ hashFiles('pyproject.toml') }}
          restore-keys: |
            playwright-${{ runner.os }}-

      - name: 🌐 Install Playwright browsers
        run: uv run playwright install --with-deps chromium

      - name: 🧪 Run Playwright e2e tests
        run: |
          uv run pytest pkg-py/tests/playwright \
            --browser chromium \
            --tracing=retain-on-failure \
            --screenshot=only-on-failure \
            -o addopts= \
            -v

      - name: 📤 Upload Playwright traces on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-e2e-results
          path: test-results/
          retention-days: 5
```

- [ ] **Step 2: Lint the workflow file**

Run: `uv run python -c "import yaml, sys; yaml.safe_load(open('.github/workflows/check-py.yaml'))"`
Expected: no output, exit 0 (the YAML parses cleanly). If a `yaml` module isn't available, run `cat .github/workflows/check-py.yaml | head -80` and visually verify the indentation matches the block above.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/check-py.yaml
git commit -m "ci: add playwright-e2e job"
```

---

## Task 11: Final verification

**Files:** none

- [ ] **Step 1: Run all e2e tests one more time end-to-end**

Run: `make py-test-e2e`
Expected: `3 passed` in under 30 seconds (first run after fresh install may take a bit longer for browser warmup).

- [ ] **Step 2: Run the existing unit-test suite to confirm we didn't break it**

Run: `make py-check-tests`
Expected: previous test count passes, no e2e tests collected, no errors.

- [ ] **Step 3: Run the broader Python checks**

Run: `make py-check-format && make py-check-types`
Expected: both pass. The new test file uses imports from `shiny.pytest` and `shiny.run`; pyright is configured to include only `pkg-py/src/shinyreact`, so test-file types aren't checked. If pyright surprises you with errors about the new files, double-check `[tool.pyright].include` was not changed by this work.

- [ ] **Step 4: Update `docs/todos.md` if it references this work**

Run: `grep -n "playwright\|#59\|ShinyOutput.*test" docs/todos.md` to find any matching entries. If a "playwright coverage for #59" entry exists, remove it. If nothing matches, skip this step.

If you removed an entry, commit:

```bash
git add docs/todos.md
git commit -m "docs: drop the playwright-coverage TODO now that #59 is closed"
```

- [ ] **Step 5: Push and open a PR**

```bash
git push -u origin schloerke/check-issue-59
gh pr create --base main \
  --title "test(py): playwright e2e tests for ShinyOutput (closes #59)" \
  --body "$(cat <<'EOF'
## Summary
- Adds Playwright e2e tests covering ShinyOutput for `@render.data_frame`, `@render_plotly`, and custom `className` use.
- Uses py-shiny's `local_app` / `create_app_fixture` to boot three spartan Shiny apps under `pkg-py/tests/playwright/apps/`.
- New `tests-e2e` dep group, new `make py-install-e2e` / `make py-test-e2e` targets, and a new `playwright-e2e` GitHub Actions job.
- Default pytest discovery is configured to skip the `playwright/` subtree so `make py-check-tests` is unchanged.

Closes #59.

## Test plan
- [x] `make py-install-e2e`
- [x] `make py-test-e2e` → 3 passed
- [x] `make py-check-tests` → unchanged passing count, no e2e tests collected
- [x] `make py-check-format && make py-check-types`
- [ ] CI `playwright-e2e` job green
EOF
)"
```

Expected: PR created, CI runs `playwright-e2e` and turns green.
