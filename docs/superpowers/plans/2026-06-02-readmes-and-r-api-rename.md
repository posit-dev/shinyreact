# Language-Agnostic READMEs + R API Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the R exports `ui_output()`→`ui_output_react()` and `render_reactive()`→`render_react()`, make the root `README.md` language-agnostic, add a new `pkg-py/README.md` (PyPI landing page), rewrite `pkg-r/README.md` (bslib-inspired R landing page), and add a repo-root Code of Conduct.

**Architecture:** The R rename is a mechanical, test-guarded change across source, regenerated roxygen docs (`NAMESPACE` + `man/`), `_pkgdown.yml`, tests, R examples, and two living docs. The README work splits the current Python-flavored root README into a language-neutral monorepo front door plus two per-language published landing pages. Python's API is untouched.

**Tech Stack:** R (roxygen2 8.0.0, devtools, usethis 3.2.1, air formatter, testthat 3e), Markdown.

**Spec:** `docs/superpowers/specs/2026-06-02-readmes-and-r-api-rename-design.md`

**Global conventions (CLAUDE.md):** Never write "SPA", "traditional pattern", `client-ui`, `ui-object`. Use `app.py`/`app.R` and `ui.tsx` as the canonical pattern names. Honest pre-release: no fabricated CRAN/PyPI presence.

---

## Reference: confirmed facts

- R `ui.tsx` bootstrap is `page_react_html("www/index.html")`; Python's is `set_react_page()`.
- R pkgdown site: `https://posit-dev.github.io/shinyreact/r` (real).
- Python installs from the **repo root** (single `pyproject.toml`, hatchling) → pre-release install is `pip install "git+https://github.com/posit-dev/shinyreact.git"`.
- R pre-release install: `pak::pak("posit-dev/shinyreact")` does NOT work directly because the package lives in `pkg-r/`; the correct subdir form is `pak::pak("posit-dev/shinyreact/pkg-r")`.
- CI: `.github/workflows/check-r.yaml` exists → R-CMD-check badge is honest. No CRAN/PyPI badges.
- `make r-document` runs `devtools::document()`; `make r-format` runs `air format`; `make r-check` runs format-check + tests + R CMD check + fixtures.

---

## Task 1: Rename the R functions in source (test-guided)

**Files:**
- Modify: `pkg-r/R/output.R`
- Modify: `pkg-r/R/render.R`
- Modify (test): `pkg-r/tests/testthat/test-ui-output.R`
- Modify (test): `pkg-r/tests/testthat/test-render.R`

- [ ] **Step 1: Update the tests to call the new names (failing test first)**

In `pkg-r/tests/testthat/test-ui-output.R`, replace the three `ui_output(` call sites and the two `test_that(` descriptions:

```r
test_that("ui_output_react() builds a shinyreact-output div with the dep", {
  tag <- ui_output_react("hello")
```
(line 1-2)
```r
test_that("ui_output_react() includes extra_deps", {
  extra <- ...                              # leave the existing extra-dep setup line unchanged
  tag <- ui_output_react("hello", extra_deps = list(extra))
```
(lines 10, 12 — only change `ui_output(` → `ui_output_react(`)

In `pkg-r/tests/testthat/test-render.R` (lines 61-62):

```r
test_that("render_react returns a shiny render function", {
  r <- render_react(node("Card"))
```

- [ ] **Step 2: Run the R tests to verify they fail**

Run: `make r-check-tests`
Expected: FAIL — errors like `could not find function "ui_output_react"` / `"render_react"`.

- [ ] **Step 3: Rename in `pkg-r/R/output.R`**

Replace the function name and the roxygen cross-reference:

```r
#' Output placeholder for a shinyreact renderer
#'
#' Creates the `<div>` that the shinyreact Shiny output binding renders into.
#' Pair with [render_react()] on the server (assign to `output[[id]]`).
#'
#' @param id Output ID. Must match the server-side `output[[id]]` assignment.
#' @param extra_deps A list of [htmltools::htmlDependency] objects to include.
#'   Downstream packages use this to inject their own JS/CSS.
#' @return A `shiny.tag` `<div>`.
#' @export
ui_output_react <- function(id, extra_deps = list()) {
  htmltools::div(
    id = id,
    class = "shinyreact-output",
    shinyreact_dep(),
    extra_deps
  )
}
```

- [ ] **Step 4: Rename in `pkg-r/R/render.R`**

Four edits in this file:

1. Comment on line 32:
```r
# Value-transform shared by render_react() and its tests.
```

2. The cli hint inside `.render_transform()` (line 46):
```r
        "i" = "Declare them up-front via {.code ui_output_react(..., extra_deps = list(...))} or at the page level."
```

3. The roxygen block + function (lines 54-80), changing the `[ui_output()]` cross-ref, the function name, the `label`, and the `ui_output` arg passed to `createRenderFunction`:
```r
#' Render a React component tree (or raw data) to a shinyreact output
#'
#' Server-side counterpart to `useShinyOutputValue()`. Assign to `output[[id]]`
#' where the UI has a matching [ui_output_react()]. Accepts a [node()] tree (which may
#' interleave htmltools tags, `HTML()`, and strings) or any JSON-serializable
#' value (passed through unchanged).
#'
#' @param expr An expression returning a `node()` tree / htmltools content, or a
#'   JSON-serializable value.
#' @param env The environment in which to evaluate `expr`.
#' @param quoted Is `expr` already quoted?
#' @return A Shiny render function.
#' @export
render_react <- function(expr, env = parent.frame(), quoted = FALSE) {
  func <- shiny::installExprFunction(
    expr,
    "func",
    eval.env = env,
    quoted = quoted,
    label = "render_react"
  )
  shiny::createRenderFunction(
    func,
    function(value, session, name, ...) .render_transform(value),
    ui_output_react
  )
}
```

- [ ] **Step 5: Run the R tests to verify they pass**

Run: `make r-check-tests`
Expected: PASS (the two renamed tests, plus the rest of the suite).

- [ ] **Step 6: Commit**

```bash
git add pkg-r/R/output.R pkg-r/R/render.R pkg-r/tests/testthat/test-ui-output.R pkg-r/tests/testthat/test-render.R
git commit -m "refactor(r)!: rename ui_output->ui_output_react, render_reactive->render_react"
```

---

## Task 2: Regenerate roxygen docs and update pkgdown reference

**Files:**
- Regenerate: `pkg-r/NAMESPACE`, `pkg-r/man/*.Rd`
- Modify: `pkg-r/_pkgdown.yml`

- [ ] **Step 1: Regenerate NAMESPACE + man/ from roxygen**

Run: `make r-document`
Expected: `pkg-r/NAMESPACE` now exports `render_react` and `ui_output_react` (no longer `render_reactive`/`ui_output`); `pkg-r/man/render_react.Rd` and `pkg-r/man/ui_output_react.Rd` are created; the stale `pkg-r/man/render_reactive.Rd` and `pkg-r/man/ui_output.Rd` are deleted by roxygen2.

- [ ] **Step 2: Verify the regeneration**

Run: `git status pkg-r/NAMESPACE pkg-r/man`
Expected: deletions of `man/render_reactive.Rd`, `man/ui_output.Rd`; additions of `man/render_react.Rd`, `man/ui_output_react.Rd`; modified `NAMESPACE`.

Run: `grep -nE "ui_output_react|render_react" pkg-r/NAMESPACE`
Expected: `export(render_react)` and `export(ui_output_react)` present.

- [ ] **Step 3: Update `pkg-r/_pkgdown.yml` reference contents**

Change the two affected `contents:` entries:

```yaml
  - title: Outputs
    contents: [ui_output_react, render_react]
```
(the `Outputs` section currently reads `[ui_output, render_reactive]`)

- [ ] **Step 4: Commit**

```bash
git add pkg-r/NAMESPACE pkg-r/man pkg-r/_pkgdown.yml
git commit -m "docs(r): regenerate man/NAMESPACE and pkgdown for renamed exports"
```

---

## Task 3: Update R examples and living docs for the rename

**Files:**
- Modify: `examples/app-r/01-hello-world/app.R`
- Modify: `examples/app-r/02-inputs/app.R`
- Modify: `examples/app-r/02-inputs/README.md`
- Modify: `examples/app-r/04-messages/app.R`
- Modify: `examples/ui-tsx-r/01-hello/app.R`
- Modify: `examples/ui-tsx-r/01-hello/README.md`
- Modify: `docs/features.md`
- Modify: `docs/timeline.md`

- [ ] **Step 1: Rewrite the R example call sites**

In each R example, replace `ui_output(` → `ui_output_react(` and `render_reactive(` → `render_react(`. These are the exact occurrences:

- `examples/app-r/01-hello-world/app.R`: line 68 `ui_output("hello")` → `ui_output_react("hello")`; lines 71, 95 `render_reactive({` → `render_react({`.
- `examples/app-r/02-inputs/app.R`: line 124 `ui_output("main", extra_deps = list(inputs_dep))` → `ui_output_react(...)`; lines 127, 143, 147, 151, 155, 159, 163, 167, 171, 176, 210 `render_reactive({` → `render_react({`.
- `examples/app-r/04-messages/app.R`: line 30 `ui_output("main", extra_deps = list(messages_dep))` → `ui_output_react(...)`; line 42 `render_reactive({` → `render_react({`.
- `examples/ui-tsx-r/01-hello/app.R`: lines 12, 16 `render_reactive({` → `render_react({`.

Use a guarded sed per file (R example dirs only — never touch `app.py`):

```bash
for f in examples/app-r/01-hello-world/app.R examples/app-r/02-inputs/app.R examples/app-r/04-messages/app.R examples/ui-tsx-r/01-hello/app.R; do
  perl -i -pe 's/\bui_output\(/ui_output_react(/g; s/\brender_reactive\(/render_react(/g' "$f"
done
```

- [ ] **Step 2: Update the two R example READMEs**

`examples/app-r/02-inputs/README.md` line 5: `... via \`render_reactive\`.` → `... via \`render_react\`.`

`examples/ui-tsx-r/01-hello/README.md` line 6: `\`render_reactive\` outputs for ...` → `\`render_react\` outputs for ...`

- [ ] **Step 3: Update `docs/features.md` (R-pattern section only)**

These lines reference the R API and must change (the Python `shinyreact.ui_output()` mentions at lines 15 and 45 stay):

- Line 105 heading: `### \`app.R\` pattern (\`page_react\` + \`render_react\`)`
- Line 107: `... the server returns trees from \`render_react()\`. ...`
- Line 113 table row: `| \`ui_output_react(id, extra_deps = list())\` | Working | ...`
- Line 114 table row: `| \`render_react(expr)\` | Working | ...`
- Line 129 table row: `| \`render_react(expr)\` | Working | ...`
- Line 147: `- **\`render_react()\` walks via an internal S3 walker.** ...`
- Line 150: `... inject their \`htmlDependency\` via \`ui_output_react(id, extra_deps = list(...))\`. \`render_react()\` is the single rendering entry point. ...`

- [ ] **Step 4: Update `docs/timeline.md` line 83**

`- \`shinyreact::ui_output()\` — equivalent to Python's \`shinyreact.ui_output()\`` → `- \`shinyreact::ui_output_react()\` — equivalent to Python's \`shinyreact.ui_output()\``

(Leave line 110, which is Python.)

- [ ] **Step 5: Verify no R-context old names remain**

Run:
```bash
grep -rn "render_reactive" . --include=*.R --include=*.Rd --include=*.md | grep -v docs/superpowers
grep -rn "\bui_output\b" examples/app-r examples/ui-tsx-r pkg-r
```
Expected: first command returns nothing; second returns nothing (only `ui_output_react` remains in R paths). Python files retaining `ui_output` are fine and outside these paths.

- [ ] **Step 6: Commit**

```bash
git add examples/app-r examples/ui-tsx-r docs/features.md docs/timeline.md
git commit -m "docs: update R examples and living docs for renamed R exports"
```

---

## Task 4: Verify the full R package after the rename

**Files:** none (verification only)

- [ ] **Step 1: Format R sources**

Run: `make r-format`
Expected: exits 0 (air reformats if needed).

- [ ] **Step 2: Run the full R check**

Run: `make r-check`
Expected: format-check, tests, and R CMD check all pass with 0 errors / 0 warnings. R CMD check specifically validates that all `\link{}` cross-references in `man/*.Rd` resolve — this catches any missed `[ui_output()]`/`[render_reactive()]` reference.

- [ ] **Step 3: Commit any formatting changes**

```bash
git add -A pkg-r
git commit -m "style(r): air format after rename" || echo "nothing to commit"
```

---

## Task 5: Add the repo-root Code of Conduct

**Files:**
- Create: `.github/CODE_OF_CONDUCT.md`
- Create: `.github/.gitignore` (usethis side artifact)

- [ ] **Step 1: Generate the tidy Code of Conduct at the repo root**

Run from the repo root:
```bash
Rscript -e 'usethis::with_project(".", usethis::use_tidy_coc())'
```
Expected: creates `.github/CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, contact `codeofconduct@posit.co`) and `.github/.gitignore` containing `*.html`. No `.Rbuildignore` change (repo root is not a package).

- [ ] **Step 2: Verify**

Run: `grep -n "codeofconduct@posit.co" .github/CODE_OF_CONDUCT.md`
Expected: one match (the enforcement-contact line).

Run: `ls .github/CODE_OF_CONDUCT.md`
Expected: file exists.

- [ ] **Step 3: Commit**

```bash
git add .github/CODE_OF_CONDUCT.md .github/.gitignore
git commit -m "docs: add Contributor Covenant code of conduct"
```

---

## Task 6: Rewrite the root `README.md` (language-agnostic)

**Files:**
- Modify: `README.md` (full rewrite)

- [ ] **Step 1: Replace the entire root README with the language-agnostic version**

Write `README.md`:

````markdown
# shinyreact

JSON-driven React rendering infrastructure for [Shiny](https://shiny.posit.co/). `shinyreact` provides the plumbing that lets downstream packages (like `shinyshadcn`) deliver React component trees from **Python or R** — it ships zero UI components itself.

One JSON wire format and one JavaScript bundle back both languages, so a React component registered once renders identically from `app.py` and `app.R`.

This repo ships per-language packages:

| Language | Source | Landing page |
|---|---|---|
| Python | [`pkg-py/`](pkg-py/) | [`pkg-py/README.md`](pkg-py/README.md) |
| R | [`pkg-r/`](pkg-r/) | [`pkg-r/README.md`](pkg-r/README.md) · [pkgdown](https://posit-dev.github.io/shinyreact/r) |

Not sure whether to use the `app.py`/`app.R` pattern or the `ui.tsx` pattern? See [`docs/app-py-vs-ui-tsx.md`](docs/app-py-vs-ui-tsx.md).

## How it works

`shinyreact` ships two first-class patterns, both available in Python and R:

**`app.py` / `app.R` pattern** — UI defined as Python or R objects in the Shiny app file:
1. Server code builds a component tree — a `Spec` of `Element`s in Python, a `node()` tree in R (which may interleave htmltools tags)
2. `shinyreact` serializes the tree as JSON and sends it to the browser via a Shiny output binding
3. The JS bundle renders the JSON into a live React component tree
4. Downstream packages register their own React components so the renderer can resolve `type` strings like `"Card"` or `"Button"`

**`ui.tsx` pattern** — UI defined in a client codebase whose entry conventionally lives in `ui.tsx` (or `App.jsx`, or `app.js` for no-build):
1. The Shiny server contains only reactive computation; it bootstraps a static page — `set_react_page()` in Python, `page_react_html()` in R
2. A static `www/index.html` plus your React client serve the UI
3. Client and server communicate via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler` hooks

See each package's README for runnable code, and [`examples/`](examples/) for working apps in both languages and both patterns.

## Extending shinyreact (package authors)

Downstream packages supply their own React components. The pattern has two halves:

### 1. JS bundle — register components

Build your own IIFE that calls `registerComponents` at load time:

```js
const { registerComponents } = window.shinyreact;

const catalog = { Button, Card, Dialog /* ... */ };
const registry = (type) => catalog[type] ?? null;

registerComponents(catalog, registry);
```

### 2. Server — render your components + inject your dependency

**Python** — subclass `reactive_output` and inject your `HTMLDependency` on the UI side:

```python
class render(shinyreact.reactive_output):
    async def transform(self, value: MyComponent) -> Any:
        return value.to_spec().to_dict()

shinyreact.ui_output("my_output", extra_deps=[my_html_dependency()])
```

**R** — build `node("YourComponent", ...)` trees and inject your `htmlDependency` via `ui_output_react()`:

```r
ui_output_react("my_output", extra_deps = list(my_html_dependency()))
```

### JS hooks available via `window.shinyreact`

Downstream component authors can use these re-exported hooks from `@posit/shiny-react`:

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, default, opts)` | Read/write a Shiny input — full `[value, setValue]` |
| `useShinyInputValue(id)` | Read-only consumer for an input that another component produces |
| `useSetShinyInput(id, default, opts)` | Write-only producer — registers an input and returns just the setter |
| `useShinyOutputValue(id, default?)` | Consume arbitrary data sent by the server renderer |
| `useShinyOutputStatus(id)` | Output lifecycle status — `"pending" \| "ready" \| "recalculating" \| "error"` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |
| `useShinyBusy()` | Whether the Shiny server is currently processing a request |

Shared `React` and `ReactDOM` instances are also available at `window.shinyreact.React` / `window.shinyreact.ReactDOM` — externalize to these in your build to avoid duplicate React.

## Architecture

- **JS bundle** (`js/dist/shinyreact.js`): Self-contained IIFE bundling React 19 and vendored `@posit/shiny-react`. Registers a Shiny `OutputBinding` for `.shinyreact-output` elements. Shared by both language packages.
- **Python package** (`pkg-py/`): `Spec` / `Element` / `Node` data model, `reactive_output` decorator, `ui_output()` + `page_react()` helpers, `set_react_page()` for the `ui.tsx` pattern, and `send_message()` for server-to-client communication.
- **R package** (`pkg-r/`): `node()` tree data model, `render_react()` renderer, `ui_output_react()` + `page_react()` helpers, `page_react_html()` for the `ui.tsx` pattern, and `send_message()`. Same wire format and JS bundle as Python.

## Development

### Setup

```bash
make setup
```

This installs Python dependencies (`uv sync`), JS dependencies (`npm install`), and pre-commit hooks.

### Common commands

```bash
make update-dist       # Build JS + copy to pkg-py/www/ and pkg-r/inst/lib/
make py-check          # Format check + type check + tests
make py-check-tox      # Full matrix: Python 3.10-3.14
make r-check           # R format + tests + R CMD check
make js-build-watch    # JS watch mode
```

Run `make help` to see all targets.
````

- [ ] **Step 2: Verify no banned terms and links resolve**

Run: `grep -niE "SPA|single.page|traditional pattern|client-ui|ui-object" README.md`
Expected: no matches.

Run: `ls pkg-py/README.md pkg-r/README.md docs/app-py-vs-ui-tsx.md examples` (Tasks 7/8 create the package READMEs; this link check is re-run in Task 9).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: make root README language-agnostic (Python or R)"
```

---

## Task 7: Create `pkg-py/README.md` (PyPI landing page)

**Files:**
- Create: `pkg-py/README.md`

- [ ] **Step 1: Write the Python package README**

Write `pkg-py/README.md`:

````markdown
# shinyreact (Python)

JSON-driven React rendering infrastructure for [Shiny for Python](https://shiny.posit.co/py/). `shinyreact` provides the plumbing that lets downstream packages (like `shinyshadcn`) deliver React component trees from Python — it ships zero UI components itself.

This is the Python package. See the [repo root](https://github.com/posit-dev/shinyreact) for the language-agnostic overview and the R package.

## Installation

`shinyreact` is pre-release and not yet on PyPI. Install from GitHub:

```bash
pip install "git+https://github.com/posit-dev/shinyreact.git"
```

## How it works

`shinyreact` ships two first-class patterns:

**`app.py` pattern** — UI defined as Python objects in the Shiny app file:
1. Server code builds a **Spec** — a flat map of elements with a root ID
2. `shinyreact` serializes the Spec as JSON and sends it to the browser via a Shiny output binding
3. The JS bundle renders the JSON into a live React component tree
4. Downstream packages register their own React components so the renderer resolves `type` strings like `"Card"` or `"Button"`

**`ui.tsx` pattern** — UI defined in a client codebase whose entry conventionally lives in `ui.tsx` (or `App.jsx`, or `app.js` for no-build):
1. The Python server contains only reactive computation; it calls `set_react_page()`
2. A static `www/index.html` + client bundle serve as the React app
3. Client and server communicate via `useShinyInput` / `useShinyOutputValue` / `useShinyMessageHandler` hooks

## Usage

### `app.py` pattern

```python
from shiny import App, ui
import shinyreact

app_ui = shinyreact.page_react(
    shinyreact.ui_output("greeting"),
)

def server(input, output, session):
    @shinyreact.reactive_output
    def greeting():
        return shinyreact.Spec(
            root="card",
            elements={
                "card": shinyreact.Element(
                    type="Card",
                    props={"title": "Hello from shinyreact"},
                ),
            },
        )

app = App(app_ui, server)
```

`@shinyreact.reactive_output` also accepts raw JSON-serializable values (dicts, lists, etc.) for use with `useShinyOutputValue()` hooks on the React side.

### `ui.tsx` pattern

```python
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()

@reactive_output
def greeting():
    return {"message": f"Hello, {input.name()}"}
```

Pair with a `www/index.html` that loads your React client (no-build `app.js` or a built bundle from `src/ui.tsx`). See [`docs/app-py-vs-ui-tsx.md`](../docs/app-py-vs-ui-tsx.md) for the file layout and dev workflow.

### Sending messages to React components

Use `send_message` to push data from the server to client-side React hooks:

```python
@reactive.effect
async def notify():
    await shinyreact.send_message(
        session, "notification", {"text": "Done!", "level": "info"}
    )
```

On the JS side, consume with `useShinyMessageHandler("notification", handler)`.

## Extending shinyreact (package authors)

`shinyreact` is designed to be extended by downstream packages that supply their own React components. Three parts:

### 1. JS bundle — register components

```js
const { registerComponents } = window.shinyreact;

const catalog = { Button, Card, Dialog /* ... */ };
const registry = (type) => catalog[type] ?? null;

registerComponents(catalog, registry);
```

### 2. Python UI — inject your HTMLDependency

```python
shinyreact.ui_output("my_output", extra_deps=[my_html_dependency()])
```

### 3. Python render subclass

```python
class render(shinyreact.reactive_output):
    async def transform(self, value: MyComponent) -> Any:
        return value.to_spec().to_dict()
```

Inject your package's `HTMLDependency` on the UI side via `shinyreact.ui_output(id, extra_deps=[...])` (see step 2) — `reactive_output` does not read an `extra_deps` class attribute.

### JS hooks available via `window.shinyreact`

| Hook | Purpose |
|------|---------|
| `useShinyInput(id, default, opts)` | Read/write a Shiny input — full `[value, setValue]` |
| `useShinyInputValue(id)` | Read-only consumer for an input that another component produces |
| `useSetShinyInput(id, default, opts)` | Write-only producer — registers an input and returns just the setter |
| `useShinyOutputValue(id, default?)` | Consume arbitrary data sent by `@shinyreact.reactive_output` |
| `useShinyOutputStatus(id)` | Output lifecycle status — `"pending" \| "ready" \| "recalculating" \| "error"` |
| `useShinyMessageHandler(type, fn)` | Handle server-to-client custom messages |
| `useShinyInitialized()` | Check whether Shiny is connected |
| `useShinyBusy()` | Whether the Shiny server is currently processing a request |

Shared `React` and `ReactDOM` instances are available at `window.shinyreact.React` / `window.shinyreact.ReactDOM` — externalize to these in your build to avoid duplicate React.

## Also in this wheel

The `shinyreact` wheel also ships two experimental prototypes — `shinyui` and `shinyuiclassonly` — that explore a class-per-component UI hierarchy. They are not part of the supported API; see the [repo](https://github.com/posit-dev/shinyreact) for details.
````

- [ ] **Step 2: Verify no banned terms**

Run: `grep -niE "SPA|single.page|traditional pattern|client-ui|ui-object" pkg-py/README.md`
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git add pkg-py/README.md
git commit -m "docs(py): add Python package README (PyPI landing page)"
```

---

## Task 8: Rewrite `pkg-r/README.md` (bslib-inspired R landing page)

**Files:**
- Modify: `pkg-r/README.md` (full rewrite)

- [ ] **Step 1: Replace `pkg-r/README.md`**

Write `pkg-r/README.md`:

````markdown
# shinyreact (R) <a href="https://posit-dev.github.io/shinyreact/r"><img src="https://posit-dev.github.io/shinyreact/r/logo.png" align="right" height="0" alt="" /></a>

<!-- badges: start -->
[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![R-CMD-check](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml)
<!-- badges: end -->

JSON-driven React rendering infrastructure for [Shiny](https://shiny.posit.co/). shinyreact is pure plumbing: it lets downstream packages deliver React component trees from R, and ships zero UI components of its own. The same JSON wire format and JavaScript bundle back both the R and [Python](https://github.com/posit-dev/shinyreact/tree/main/pkg-py) packages.

## Overview

shinyreact gives R Shiny two ways to drive a React front end:

- **`app.R` pattern** — describe the UI as R objects with `node()` and render them with `render_react()`. The server owns the UI.
- **`ui.tsx` pattern** — write the UI in a client React codebase and bootstrap it from R with `page_react_html()`. The server owns only reactive computation.

Either way, downstream packages register the React components, and shinyreact handles the wire format, the output binding, and server-to-client messaging.

## Installation

shinyreact is pre-release and not yet on CRAN. Install the development version from GitHub (the package lives in the `pkg-r/` subdirectory of the monorepo):

```r
# install.packages("pak")
pak::pak("posit-dev/shinyreact/pkg-r")
```

## Usage

A minimal `app.R` (the `app.R` pattern). The thin component helpers wrap `node()` to mirror the React components registered in `hello_world.js`:

```r
library(shiny)
library(shinyreact)

card <- function(title, ...) node("Card", ..., props = list(title = title))

ui <- page_react(
  # ... your htmlDependency for the registered React components ...
  ui_output_react("hello")
)

server <- function(input, output, session) {
  output$hello <- render_react({
    card(
      "Hello Shiny React!",
      htmltools::tags$small("A shinyreact x htmltools demo")
    )
  })
}

shinyApp(ui, server)
```

`render_react()` walks a `node()` tree (which may interleave htmltools tags, `HTML()`, and strings) into the JSON wire tree. Any other JSON-serializable value passes through unchanged for `useShinyOutputValue()` hooks on the React side. Push data to the client with `send_message()`.

See [`examples/app-r/01-hello-world/`](https://github.com/posit-dev/shinyreact/tree/main/examples/app-r/01-hello-world) for the complete runnable app, including the registered components.

## Get started

- **Function reference:** <https://posit-dev.github.io/shinyreact/r>
- **Examples:** [`examples/app-r/`](https://github.com/posit-dev/shinyreact/tree/main/examples/app-r) (the `app.R` pattern) and [`examples/ui-tsx-r/`](https://github.com/posit-dev/shinyreact/tree/main/examples/ui-tsx-r) (the `ui.tsx` pattern)
- **Feature inventory:** [`docs/features.md`](https://github.com/posit-dev/shinyreact/blob/main/docs/features.md)
- **Which pattern?** [`docs/app-py-vs-ui-tsx.md`](https://github.com/posit-dev/shinyreact/blob/main/docs/app-py-vs-ui-tsx.md)
````

NOTE on the logo line: shinyreact has no logo asset. Set `height="0"` keeps the bslib-style right-aligned anchor without rendering a broken image, OR drop the `<a href...>` line entirely. **Drop the logo `<a>` line** if you prefer no placeholder — the plan's default is to remove it. Replace the title line with the plain:

```markdown
# shinyreact (R)
```

- [ ] **Step 2: Decision — remove the logo placeholder**

Edit the first line of `pkg-r/README.md` to just `# shinyreact (R)` (no `<a href>`/`<img>`), since no logo asset exists. This avoids a broken image / 404.

- [ ] **Step 3: Verify badges, terms, and links**

Run: `grep -niE "SPA|single.page|traditional pattern|client-ui|ui-object" pkg-r/README.md`
Expected: no matches.

Run: `grep -n "render_reactive\|ui_output\b" pkg-r/README.md`
Expected: no matches (only `render_react` / `ui_output_react` appear).

- [ ] **Step 4: Commit**

```bash
git add pkg-r/README.md
git commit -m "docs(r): rewrite R package README (bslib-inspired landing page)"
```

---

## Task 9: Final cross-cutting verification

**Files:** none (verification only)

- [ ] **Step 1: Repo-wide rename sanity check**

Run:
```bash
grep -rn "render_reactive" . --include=*.R --include=*.Rd --include=*.md --include=*.yml | grep -v docs/superpowers
grep -rn "\bui_output\b" pkg-r examples/app-r examples/ui-tsx-r
```
Expected: both return nothing. (Python `ui_output` outside these paths is intentional and retained.)

- [ ] **Step 2: All three README links resolve**

Run:
```bash
ls README.md pkg-py/README.md pkg-r/README.md
grep -n "pkg-py/README.md\|pkg-r/README.md\|docs/app-py-vs-ui-tsx.md" README.md
ls pkg-py/README.md pkg-r/README.md docs/app-py-vs-ui-tsx.md
```
Expected: all listed files exist; the root README's relative links point at real files.

- [ ] **Step 3: R package still checks clean**

Run: `make r-check`
Expected: 0 errors, 0 warnings (re-run here because the rename touched man/Rd cross-references).

- [ ] **Step 4: Python package unaffected**

Run: `make py-check`
Expected: passes (Python API untouched; this confirms no incidental breakage and that adding `pkg-py/README.md` did not disturb the build).

- [ ] **Step 5: Final commit if anything outstanding**

```bash
git status
git add -A && git commit -m "chore: finalize README + rename pass" || echo "nothing to commit"
```

---

## Self-review notes

- **Spec coverage:** Part 1 (rename) → Tasks 1-4; Part 2 (root README) → Task 6; Part 3 (pkg-py README) → Task 7; Part 4 (pkg-r README) → Task 8; Part 5 (CoC) → Task 5. Final verification → Task 9.
- **Type/name consistency:** new names `ui_output_react` / `render_react` are used identically across source (Task 1), regenerated docs (Task 2), examples + living docs (Task 3), and the R README (Task 8). The internal `createRenderFunction(..., ui_output_react)` arg is renamed in Task 1 Step 4.
- **No fabrication:** install commands and the pkgdown URL are verified real; no CRAN/PyPI badges; the R logo anchor is explicitly removed because no asset exists.
- **Python untouched:** Python `ui_output`/`reactive_output` retained everywhere; rename greps are path-scoped to R.
