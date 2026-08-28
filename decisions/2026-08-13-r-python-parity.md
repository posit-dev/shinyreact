# R/Python parity: what converges and what stays different

**Date:** 2026-08-13
**Status:** Decided, implemented
**Issues:** [#182](https://github.com/posit-dev/shinyreact/issues/182), [#183](https://github.com/posit-dev/shinyreact/issues/183), [#184](https://github.com/posit-dev/shinyreact/issues/184)

## Context

An R/Python parity audit turned up a set of divergences between `pkg-py/` and
`pkg-r/`. Two were outright bugs (#182, #183). The rest, tracked in #184, needed
a decision rather than a fix: some were accidents worth converging, others are
consequences of the two languages that should be documented instead of papered
over.

The guiding rule: **the same React component talking to either server should get
the same data and produce the same page.** Divergence is acceptable only where
matching the other language would make the API worse in its own idiom.

## Converged

### `page_react_dep()` script attributes (#182)

R emitted `script = list(src = js_file, defer = "")`, Python
`script={"src": js_file, "type": "module"}`. An ESM bundle — the default output
of a Vite `build.lib` config — throws on its first `import` under a classic
`<script defer>` tag, so the R tag was simply wrong for the common case.

**Decision:** both emit `type="module"`. It is implicitly deferred, so `defer`
is redundant. Anyone shipping a classic script builds the `HTMLDependency` /
`htmlDependency()` directly; that escape hatch is documented on both sides.

### `page_react_dep()` argument shape (#184)

R was positional with `src_dir` + `js_file` required and offered `name` /
`css_file`; Python was keyword-only, inferred `src_dir` and `name` from the
caller's `__file__`, and always attached `main.css`.

**Decision:** take the better half of each.

- Python gains `src_dir=` and `name=`. R's explicit `src_dir` is the better
  design: Python's frame inspection reads the *immediate* calling frame, so a
  library author wrapping `page_react_dep()` in a helper silently resolves
  against the wrapper's directory. Inference stays as the default because it is
  what makes the one-line app case pleasant, but it is now opt-out.
- Both default to `js_file = "main.js"` and `css_file = "main.css"`.
- **Neither the script nor the stylesheet is attached unless the file exists.**
  Python previously emitted a link to `main.css` unconditionally, 404-ing for
  bundles that ship no CSS; R defaulted to no CSS at all. Existence-gating gives
  both the same behavior and is what either default was reaching for. The same
  rule applies to `js_file`: a tag pointing at a file that is not there is never
  useful.

  A missing `js_file` additionally **warns**. It is the entry point, so an
  existence-gated dependency with no script is empty — it loads nothing and,
  unlike the 404 it replaces, leaves nothing in the console to diagnose. The
  warning keeps the "build the dep before the bundle exists" dev flow working
  (the `"0"` version fallback is unchanged) while making the silence audible.

`src_dir` stays required in R — there is no per-caller `__file__` to infer from.

### `send_message()` namespacing (#184)

R fell back to an un-namespaced type when `session$ns` was not a function.
That silently delivers a message no module-scoped handler matches.

**Decision:** abort instead. Every real Shiny session namespaces —
`ShinySession$ns()` is `NS(NULL, id)` at top level and the module prefix inside
`moduleServer()` — so the fallback only ever fired for a malformed session,
where an error is the useful outcome.

### Bookmark-restore error handling (#184)

R wrapped the whole `shiny:::` restore-context read in
`tryCatch(..., error = function(e) list())`. Python catches only the
`RuntimeError` raised when there is no session.

**Decision:** drop the blanket catch. `hasCurrentRestoreContext()` already
returns `FALSE` (it does not error) outside an HTTP request and when no bookmark
query string was parsed, so the guard covers the expected-empty cases on its
own. Genuine breakage in the pinned internals now surfaces rather than silently
disabling bookmark restore across a shiny release.

### `shinyreact.default` input-handler edge cases (#184)

Two observable results differed with nothing pinning them as deliberate: `[]`
arrived as `NULL` in R vs `[]` in Python, and `[[1, 2], [3, 4]]` flattened to
`c(1, 2, 3, 4)` in R but kept its nesting in Python.

**Decision:** both were accidents of inheriting shiny's default coercion. R now
returns `list()` for an empty array and preserves nested arrays. The full
contract is tabulated in `CLAUDE.md` and tested on both sides.

### `page_react_html()` file read (#184)

R's `readLines()` + `paste(collapse = "\n")` dropped a trailing newline and
normalized CRLF; Python's `read_text()` is byte-exact.

**Decision:** R reads the bytes verbatim via `readChar()`. The same
`index.html` now renders identically from either server.

## Stays different

### Relative-path resolution in `page_react_html()`

Python resolves a relative `path` against the calling module's `__file__`
directory, falling back to CWD. R resolves against the process working
directory, full stop.

**Decision:** keep the difference. R has no per-caller `__file__`, and the
alternatives (`sys.function()` walking, `srcref` inspection) are fragile and
surprising. Under `runApp()` / `shinyApp()` the working directory *is* the app
directory, so the default `"www/index.html"` works in both languages; the
divergence only shows up outside that. Documented in the R function's
`@section Path resolution`, and the not-found error now names the working
directory so a wrong CWD is diagnosable rather than mysterious.

### Renderer `HTMLDependency` discovery — SUPERSEDED 2026-08-28

> **Superseded 2026-08-28** (recorded while auditing `FEATURES.md`, issue #245).
> This is no longer a divergence: R gained push-based per-session discovery in
> #221 (merged 2026-08-27), and Python Core gained it in #249 (merged
> 2026-08-28, closing #220). Both languages now discover renderer dependencies
> automatically; Express's `set_react_page()` additionally inlines them into the
> initial page. The decision below is kept as the record of what was believed on
> 2026-08-13.

`set_react_page()` harvests dependencies off renderers and off
`session.output._outputs`. R has no analogue.

**Decision:** no R analogue for now. `set_react_page()` is Shiny **Express**
only, and Express has no R equivalent — the harvesting exists because Express
gives the page function the renderers. Python's own Core-mode
`page_react_html()` is equally dependency-blind, so R currently matches
Python-Core exactly, which is the right comparison. Revisit only if R module
apps turn out to need it, and file it as its own issue with a concrete failing
app rather than as a parity item.

### Scalar-array flattening in the default input handler

`[0, 100]` becomes `c(0, 100)` in R and stays `[0, 100]` in Python.

**Decision:** deliberate. An atomic vector is what R code wants to work with,
and it matches shiny's own no-type coercion, so the R idiom wins over
structural identity here. `type = "shinyreact.asis"` is the documented opt-out
for components that need the value untouched.
