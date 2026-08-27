# Extracting output UI (and dependencies) from R render functions — design

**Issue:** [#203](https://github.com/posit-dev/shinyreact/issues/203) — Extract UI methods
for R outputs.

**Related:** [#146](https://github.com/posit-dev/shinyreact/issues/146) (R's
`page_react_html()` did no renderer dependency discovery — the R counterpart of
[#87](https://github.com/posit-dev/shinyreact/issues/87)),
[#160](https://github.com/posit-dev/shinyreact/issues/160) (post-page-load dependency
delivery, Python side), [#138](https://github.com/posit-dev/shinyreact/issues/138)
(R example using a renderer with obvious HTML dependencies).

**Status: shipped.** Extraction primitive (`output_ui()`, internal for now — not
exported until the API has settled, per review) plus automatic
per-flush dependency discovery. Browser-verified end to end with
`examples/07-plotly/app.R` (`plotly::renderPlotly()` bound and rendered through
`<ShinyOutput>` with zero manual dependency wiring).

## The extraction primitive

Every R render function is classed `shiny.render.function` and carries `outputFunc` /
`outputArgs` attributes (set by `shiny::markRenderFunction()`). shiny's own canonical
consumer is `shiny:::useRenderFunction()` — the function behind both
`as.tags.shiny.render.function` and the knitr auto-print path. `output_ui()`
(`pkg-r/R/output-ui.R`) replicates its core:

```r
do.call(attr(f, "outputFunc"), c(list(id), attr(f, "outputArgs")))
```

rather than calling `useRenderFunction()`, which has two side effects we must not
trigger: it registers the render function into the current reactive domain's `output`
under a fresh random id (double-registration when harvesting a live session) and flips
the `hasExecuted` flag.

Key properties (verified on R 4.5.2 / shiny 1.14.0.9000):

- **No user expression is ever evaluated** — `outputFunc` is a UI constructor; only
  *invoking* the render function runs user code, and extraction never does.
  (`renderImage({})` constructs fine; only its render call needs a real file.)
- `reactive_output()`'s render functions get shiny's placeholder `outputFunc` (a `<pre>`
  notice) — dep-less, so harvesting skips them naturally.
- Composed with `htmltools::findDependencies()`, this is the exact R counterpart of
  Python's `renderer.auto_output_ui()` + `.tagify().get_dependencies()`
  (`_collect_renderer_deps()` in `pkg-py/src/shinyreact/_page.py`).

## Automatic discovery (the delivery design)

Python's Express-mode `set_react_page()` harvests `session.output._outputs` at
page-generation time and inlines every dep into the initial `<head>`. R cannot:
`shinyApp(ui, server)` renders the UI before the session's `server()` runs. So R pushes
instead (`pkg-r/R/dep-discovery.R` + `pkg-js/src/dep-discovery.ts`):

1. **Hook** — the JS bundle sends one `.shinyreact_init` ping (typed
   `shinyreact.init`) after Shiny init; that type's dedicated input handler calls
   `install_dep_discovery(session)` (idempotent per session). The guaranteed ping means
   every session bootstraps exactly once, with or without other inputs, and the
   value-transforming handlers (`shinyreact.default` / `shinyreact.asis`) stay pure.
   (An input handler is the hook because shiny has no public session-created hook;
   Python registers `shinyreact.init` as a no-op — its bootstrap point for #220.)
2. **Harvest** — on **every** `onFlushed` (not just the first, so module servers mounted
   after startup are covered), diff `names(private$.outputs)` against the seen set —
   a `setdiff` on names, microseconds when nothing changed. For each new output, get the
   render function via the public `session$getOutput(name)`, build UI with `output_ui()`,
   `findDependencies()`, drop already-sent deps (name@version), `createWebDependency()`
   each, and send one `shinyreact-deps` custom message. (`private$.outputs` is exactly as
   private as Python's `session.output._outputs`, already relied on in `_page.py`.)
3. **Client** — the bundle's handler awaits `Shiny.renderDependenciesAsync(deps)` then
   re-runs `Shiny.bindAll(document.documentElement)`; `bindAll` skips elements already
   marked `.shiny-bound-*`, so page-wide re-binding is safe.

### Why the late push works in R (where it failed in Python, #160)

- The shiny client replays stored output values when an element binds late, and
  hidden-output suspension means an unbound output's value usually isn't computed until
  *after* the bind anyway (bind → client reports visible → observer resumes → value).
- R htmlwidgets are **value-based**: the widget payload carries its own runtime deps
  (e.g. plotly-main), so only the binding JS (`htmlwidgets.js`, `plotly-binding`) needs
  to pre-exist at bind time — exactly what the push delivers, in dependency order.
  Python's blocker was shinywidgets' `comm_open` **custom message** racing the dep load;
  R has no such side channel. #160 (the shinywidgets ordering problem) remains open and
  is *not* fixed by this design.

## Rejected acquisition routes

| | Why rejected |
|---|---|
| Explicit `page_react_html(deps = ...)` arg | Was the fallback plan; unnecessary once the push proved out — `output_ui()` remains internally as the extraction primitive |
| `MockShinySession` pre-run of `server()` at startup | Executes the user's whole server body twice (DB connects, side effects) |
| Static AST scan of the server body for `render*()` calls | Misses dynamic/wrapped renderers; fragile pattern-match |

## Parity notes

- Python Express (`set_react_page()`) already discovers deps inline; Python Core
  (`page_react_html()`) does not — the same input-handler + flush-diff push design ports
  to py-shiny (`input_handlers.add`, `session.on_flushed(once=False)`) and would also
  cover Express outputs registered after page load for value-based renderers. Tracked as
  a follow-up (see the PR for this spec).
- Tests: `pkg-r/tests/testthat/test-output-ui.R` and `test-dep-discovery.R`; the Python
  counterpart behavior is asserted in `pkg-py/tests/test_page_dep_harvest.py`.
