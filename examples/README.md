# shinyreact examples

Runnable example apps for the `ui.tsx` pattern: the server contains only
reactive computation, and the UI is defined in a client-side React codebase
whose entry is conventionally `ui.tsx` (simpler variants like `www/ui.js`
for no-build or `src/ui.jsx` for Vite + JSX fill the same role).

Examples are Python unless noted; [01-hello](01-hello/),
[07-plotly](07-plotly/) and [11-npm-local](11-npm-local/) also ship an `app.R`
showing the same app on the R package. The first two are the canonical source
for a copy in `pkg-r/inst/examples-shiny/` that ships with the installed R
package — **after editing their `app.R` or `www/`, run `make update-examples`**
(a testthat drift guard fails otherwise). 11-npm-local is not copied: its
`www/ui.js` is built, not committed, so the shipped copy would be an app that
cannot run.

**Shipping several servers over one `www/` client is a device of these
examples, not a pattern to copy.** A real app has one server. It exists here
for two reasons: it demonstrates that the client does not know which language
answers, and it lets a single behavior be asserted with the *same* golden
values in Python and in R — which is how a divergence between the two
implementations becomes visible rather than silently correct in isolation.

Every example carries a `FEATURES.md` describing what it does, leaf by leaf —
see [Example behavior trees](#example-behavior-trees) below.

| Example | Description |
|---------|-------------|
| [01-hello](01-hello/) | Shiny's `01_hello` Old Faithful app rebuilt `ui.tsx`-first (no JSX, no bundler). The server returns histogram `{breaks, counts}` as JSON; the client draws the bars as SVG. Includes `app.py`, `app-core.py`, and `app.R` servers over the same `www/` client |
| [02-columns](02-columns/) | Drag-between-columns demo, no build step. Server owns data only (one `move_item` event input), client owns UI (~20 lines of server logic) |
| [03-columns-shadcn](03-columns-shadcn/) | Same drag-between-columns demo as 02, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyreact`. The only example that owns its own `www/index.html` — `ReactApp(server)` serves it as-is, inserting the tags at `<meta name="shiny-dependency-placeholder">` |
| [04-shadcn](04-shadcn/) | shadcn/ui + Tailwind v4. Side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@reactive_output`, client renders); Plotly hover/click/select events round-trip through `useShinyInput` |
| [05-temperature](05-temperature/) | Temperature conversion app demonstrating simple reactive data flow |
| [06-data-frame](06-data-frame/) | Embeds `@render.data_frame` via `ShinyOutput` and `set_react_page()` |
| [07-plotly](07-plotly/) | Embeds `@render_plotly` via `ShinyOutput` and `set_react_page()`. Also ships an `app.R` using `plotly::renderPlotly()` over the same `www/` client — its binding JS is discovered from the render function and pushed automatically |
| [08-input-handler](08-input-handler/) | `useShinyInput` with `type="shiny.datetime"` — client sends unix seconds; server `input.when()` is a `datetime.datetime` via Shiny's built-in handler |
| [09-hmr](09-hmr/) | React Fast Refresh in dev (Vite dev server alongside Shiny). The npm tier: imports `@posit-dev/shinyreact` and bundles its own React, with `set_react_page(shinyreact_js="client")` so the server doesn't also serve shinyreact.js |
| [10-bookmarking](10-bookmarking/) | Bookmark restoration: URL query string (or server-stored state) hydrates `useShinyInput` initial values via the `#shinyreact-config` tag emitted by `page_react()` |
| [11-npm-local](11-npm-local/) | The npm tier with nothing else on the page: the client imports `@posit-dev/shinyreact` (repo-relative `file:../../pkg-js`, as 09-hmr does) and the server is `page_bare(page_react_dep(...))` — no shinyreact JS, no `#shinyreact-config` tag, no protocol handshake. `app.py` + `app.R` |

## Running an example

The R examples run straight from GitHub, no clone:

```r
# install.packages("pak")
pak::pak("posit-dev/shinyreact")

shiny::runGitHub("posit-dev/shinyreact", subdir = "examples/01-hello")
shiny::runGitHub("posit-dev/shinyreact", subdir = "examples/07-plotly")
```

Note the capital H — `shiny::runGithub` does not exist. It downloads the
repo's default branch and runs the app in `subdir`; pass `ref = "some-branch"`
for anything else. `01-hello` and `07-plotly` are the only examples that ship
an `app.R`, so they are the two this launches; the rest are Python.

Python has no `runGitHub` equivalent, so clone and run:

```bash
git clone https://github.com/posit-dev/shinyreact
cd shinyreact
shiny run examples/01-hello/app.py
```

The three examples with a build step — [03-columns-shadcn](03-columns-shadcn/),
[04-shadcn](04-shadcn/), [09-hmr](09-hmr/) — do **not** commit their bundle
(`www/ui.js` is gitignored). [04-shadcn](04-shadcn/) and [09-hmr](09-hmr/)
build it themselves on first run when it is missing, so `shiny run` just works;
[03-columns-shadcn](03-columns-shadcn/) still needs `npm install && npm run
build` in the example directory first. Their READMEs cover it.

## Example behavior trees

Each example directory has a `FEATURES.md`: a nested bullet list of everything
that app does, one atomically checkable claim per leaf. Each one **stands
alone** — it carries its own marker legend and never asks the reader to go
somewhere else for the format — so an agent handed a single example directory
has everything it needs.

The README of an example is prose for a human deciding whether to read it. Its
`FEATURES.md` is the checkable description: exact ids, defaults, ranges, wire
shapes, and copy, with no explanation. Where they overlap, `FEATURES.md` wins,
because it is the one an audit can falsify.

The format is the repo-root [`FEATURES.md`](../FEATURES.md)'s, scoped to one
app instead of the packages, plus a `(test)` marker for a claim pinned by a
unit test in that example's own `tests/` directory (`test_*.py`,
`testthat/test-*.R`, `ui.test.ts`) — see
[Running an example's tests](#running-an-examples-tests) below.

Two rules keep them worth reading:

1. **A PR that changes an example updates that example's `FEATURES.md` in the
   same PR.** A behavior change with no tree diff is an incomplete PR.
2. **When the code and the tree disagree, the code wins and the tree gets
   fixed.**

They also serve as worked examples of the output the
`shinyreact-convert-app` skill produces when porting an existing Shiny app:
describe the app in plain English first, then build against the description.

## Running an example's tests

The tests for an example live beside it, in `<example>/tests/`, and run from
the example — you do not need the shinyreact packages installed to run them:

```bash
cd examples/01-hello

pytest                                   # the app's Python tests
Rscript -e 'shiny::runTests()'           # the app's R tests (also shinytest2::test_app())
npx vitest run --root .. 01-hello        # the app's UI tests
```

Most of the Python tests drive the app itself, with
[`shiny.testserver.test_server()`](https://shiny.posit.co/py/api/testing/):
inputs in, output values out, in memory. That is a good fit for these apps
because a `ui.tsx` server contains only reactive computation, so the JSON a
test asserts is exactly what `useShinyOutputValue()` receives:

```python
with test_server(APP) as ts:
    ts.set_inputs(bins=9)
    assert ts.get_output("dist_caption") == "272 eruptions in 9 bins"
```

Pass an absolute `Path` (`Path(__file__).resolve().parents[1] / "app.py"`), and
mind two shinyreact-specific details: an **untyped** input id needs no
`:shinyreact.default` suffix (the hook adds it on the wire, but Python's
handler is a no-op), while a **typed** one does, because the suffix is what
runs the handler; and an input read through `@reactive.event(...,
ignore_init=True)` needs two `set_inputs` calls, mirroring the client's
register-at-mount then send-the-event.

The UI tests need a JS toolchain, which the no-build examples deliberately do
not carry. `examples/package.json` provides one for the whole examples tree, so
`npm install` there once covers every example:

```bash
cd examples && npm install
npm test                    # every example's UI tests
npx vitest run 01-hello     # one example's
```

Each package's own test run also includes these files — pytest's `testpaths`
covers `examples/`, `pkg-js/vitest.config.ts` includes `../examples/**/tests/`,
and `pkg-r/tests/testthat/test-examples.R` sources the examples' testthat
files — so a package change that breaks an example fails the package's suite.
