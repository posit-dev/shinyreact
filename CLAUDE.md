# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`shinyreact` is a monorepo providing React UI infrastructure for Shiny (Python and R). It provides zero UI components — it is the bridge between a Shiny server that contains only reactive computation and a React client the app author owns.

The repo ships one first-class pattern: the **`ui.tsx` pattern** — `set_react_page()` (Python Express) / `page_react()` (Python Core, R) bootstraps a React client whose entry conventionally lives in `ui.tsx` (compiled to `www/ui.js`, discovered automatically); the client and server communicate through the `useShinyInput` / `useShinyOutputValue` hook family. See `DESIGN.md` for background.

## Terminology

**`ui.tsx`** is the canonical name of the pattern. **Never write "SPA", "Single Page App", "Single-Page Application", "traditional pattern", `client-ui`, or `ui-object`** in new content (docs, comments, commit messages, PR/issue text).

- **`ui.tsx` pattern** — UI defined in a client-side codebase whose entry is conventionally `ui.tsx` (or `ui.jsx`, or `ui.js` for no-build); bootstrapped from the app file via `set_react_page()` / `page_react()` (or `page_react_html()` for apps that own a full HTML document). `ui.tsx` is the *idiomatic* canonical name — examples use the same role at different tiers: `www/ui.js` (no-build) or `src/ui.jsx` (Vite + JSX, built to `www/ui.js`). Treat `ui.tsx` as a *role label* for the React entry, not a strict filename requirement.
- The phrase "traditional Shiny" is fine when it refers to vanilla Shiny (no shinyreact involved).
- The repo formerly also shipped an **`app.py` pattern** (server-side JSON-spec rendering via `Node` / `render_react` / `page_react`). It was removed in #168; see the tracking comment on #167 for git-history pointers if you encounter stale references.

## Repo structure

```
pkg-js/                     # TypeScript/React Vite IIFE bundle
  src/                      # index.ts, global.ts, shiny-output.tsx, shiny.d.ts, shinyreact.css
  dist/                     # Built assets (committed to repo)
  src/shiny-react/          # Vendored @posit/shiny-react source (hooks, registries)
pkg-py/                     # Python package
  src/shinyreact/           # React-bridge package
    www/                    # Bundled JS
  tests/                    # pytest tests (+ tests/playwright/ e2e)
pkg-r/                      # R package — mirrors the Python API in R
  R/                         # render.R, page.R, message.R, bookmark.R, dep.R, input-handler.R
  inst/lib/shiny/            # Bundled JS (R counterpart of pkg-py www/)
  tests/testthat/            # testthat tests
examples/                   # ui.tsx pattern examples (01-hello … 10-bookmarking)
FEATURES.md                 # behavior tree for all three packages — see below
docs/                       # posit-conf-2026-goals.md, historical plans/specs
decisions/                  # Architecture decision records
pyproject.toml              # Root-level, hatchling backend
Makefile                    # All build/check/format commands
```

## Commands

```bash
# Initial setup
uv sync --all-extras --all-groups   # Python env
make js-setup                        # JS deps (cd pkg-js && npm install)
pre-commit install                   # Pre-commit hooks

# Build
make js-build                        # Build JS bundle (pkg-js/dist/)
make update-dist                     # Build JS + copy to pkg-py/www/ and pkg-r/inst/lib/shiny/

# Python checks (run all before committing)
make py-check                        # format check + type check + tests
make py-check-tests                  # pytest only
make py-check-types                  # pyright only
make py-format                       # ruff fix + format
make py-check-tox                    # full matrix: Python 3.10–3.14

# JS checks
make js-lint                         # tsc --noEmit
make js-build-watch                  # watch mode

# R checks
make r-check                         # format + tests + R CMD Check
make r-format                        # air format

# Run a single Python test
uv run pytest pkg-py/tests/test_page.py::test_name

# Update test snapshots
make py-update-snaps
```

Run `make help` to see all targets.

## Architecture

### JS bundle

The JS output (`pkg-js/dist/shinyreact.js`) is a self-contained IIFE that bundles React 19 and vendored `@posit/shiny-react`, and installs the public API at `window.shinyreact`.

**Global API exposed at `window.shinyreact`:**
- `useShinyInput`, `useShinyInputValue`, `useSetShinyInput`, `useShinyOutputValue`, `useShinyOutputStatus`, `useShinyMessageHandler`, `useShinyInitialized`, `useShinyBusy` — re-exported shiny-react hooks
- `ImageOutput`, `ShinyModuleProvider`, `ShinyReactComponentElement`, `ShinyOutput`, `MISSING` — components/utilities
- `React`, `ReactDOM` — shared instances (downstream ESM builds should externalize to these to avoid duplicate React)

`ShinyOutput` renders a traditional Shiny output element (e.g. `shiny-data-frame`, a plotly widget) inside a React tree and wires `Shiny.bindAll`/`unbindAll` — it has no dependency on any server-side placeholder.

#### Don't write to `window` — with two named exceptions

**Default: module-level state, not globals.** A module singleton is testable, typed, and cannot be clobbered by another script on the page. Reach for it first.

Writing to `window` (including `window.Shiny.*`) is justified in exactly one situation: **state that must be shared per *page*, not per *bundle copy*.** Two copies of this library can be on one page today — the server injects the IIFE bundle even for an npm-tier app, until the opt-out in #217 lands — and each copy has its own module singletons. Anything that must be single per page has to travel through something both copies can see.

The two sanctioned cases, both mediated by a single accessor:

| Accessor | Why page-scoped |
|---|---|
| `getReactRegistry()` | input/output values and their subscribers; two registries would split one input id's producers and consumers across them |
| `getMessageRegistry()` | Shiny gives **one dispatcher slot per message type**, so a second `addCustomMessageHandler("shinyReactMessage")` either replaces the first or throws — either way one copy's handlers go dead |

Rules if you find yourself adding a third:

- **Go through an accessor**, never a bare assignment at the point of use. One place attaches (`shiny.x ??= singleton`), everyone reads through it. Scattered assignments are how `window.Shiny.messageRegistry` ended up written from two places and read from none.
- **Fall back to the module singleton when `window.Shiny` is absent** rather than throwing or returning `undefined` — the client legitimately runs before Shiny loads.
- **Type the property optional** (`x?: T`). It genuinely is, before the first attach.
- **Test the sharing**, not just the happy path: `vi.resetModules()` plus a re-import simulates a second copy of the library on the same page.
- **Write down why page scope is required.** If the answer is "so I can inspect it in DevTools", that is not a reason — use a module export and a test.

### Python package

- `@shinyreact.reactive_output` — `Renderer[Jsonifiable]` subclass; passes raw JSON data through for `useShinyOutputValue()` hooks, with no placeholder (`auto_output_ui()` returns `None`)
- `shinyreact.send_message(session, id, data)` — sends `shinyReactMessage` custom messages consumed by `useShinyMessageHandler()`
- `shinyreact.set_react_page(path=None)` — Express helper; with no args serves `www/index.html` when present, else discovers `www/ui.js` / `www/ui.css` and emits no body HTML. Auto-discovers `HTMLDependency` objects from traditional Shiny renderers and injects the shinyreact dep
- `shinyreact.page_react(src_dir=None, js_file="ui.js", css_file="ui.css", title=None)` — Core-mode zero-config page: discovers `www/ui.js` / `www/ui.css` next to the calling module, serves them as an mtime-versioned dependency (cache-busted), title defaults to the app folder name; the client appends its own mount container to `<body>`
- `shinyreact.ReactApp(server, *, ui=None, static_assets=MISSING, bookmark_store="disable", **kwargs)` — `shiny.App` for the ui.tsx pattern with the UI discovered next to the calling module: `www/index.html` present → `page_react_html()`, else → `page_react()`. The discovered UI is a per-request function, so bookmark restore works with no wiring (`ReactApp(server, bookmark_store="url")`); `ui=page_react_html(...)` + a bookmark store raises, since one already-built document can't restore. The React asset dir is mounted at `/`, and a passed `static_assets` mapping is **merged with** that mount rather than replacing it — the author wins only on collision (`"/"` key, a bare path, or `None` for nothing). `static_assets` defaults to `MISSING`, not `None`, so `None` can mean "mount nothing". `ui=` overrides discovery (a `ReactHtmlDocument` still gets its dir mounted); discovery reads the *immediate* calling frame, so helpers wrapping `ReactApp(...)` must pass `ui=`
- `shinyreact.page_react_html(path="www/index.html")` — Core-mode helper for apps that own a complete HTML document containing `<meta name="shiny-dependency-placeholder" content="">` (py-shiny's `ui.PageDocument.DEPS_PLACEHOLDER`); Shiny's and shinyreact's tags render in its place. Rarely called directly — `ReactApp` discovers it (plain `shiny.App` works too via `ui.PageDocument`, consumed as a git dep until py-shiny#2475 releases — issue #216). Does not auto-discover renderer dependencies
- `shinyreact.page_bare(...)` / `shinyreact.page_react_dep(...)` — escape-hatch page builder and app-bundle `HTMLDependency` helper
- Bookmark restore + protocol handshake: page entry points emit a `<script type="application/json" id="shinyreact-config">` tag carrying the wire-protocol version and any restored input values (`_bookmark.py` / `bookmark.R`); the bundle asserts the protocol major version and seeds `useShinyInput` initial values from it; the config tag is the only delivery channel (`window.shinyreact._restore` is a write-only DevTools sentinel)

### R package

The R package (`pkg-r/`) mirrors the Python API in R idioms; exports are `reactive_output`, `page_bare`, `page_react`, `page_react_html`, `page_react_dep`, `send_message`. Key shape differences from Python:

- `reactive_output(expr, ...)` is a **function** assigned to `output$id`, not a decorator/`Renderer` class.
- `page_react(src_dir = "www", ...)` matches Python's `page_react()` (R resolves against the working directory; Python against the calling module).
- `page_react_html(path = "www/index.html")` matches Python: a complete HTML document with a `<meta name="shiny-dependency-placeholder" content="">` tag (R rewrites it to `{{ headContent() }}` internally, since `htmlTemplate()` is how R places rendered deps). R uses it directly as `shinyApp(ui = ...)`; Python discovers it via `shinyreact.ReactApp(server)` (asset auto-mount; py-shiny#2475 provides the document support). Python additionally has the Express-only `set_react_page()` and `ReactApp` (R has no `shiny.App` subclass equivalent).
- `send_message(session, id, data)` matches Python.
- `page_react_dep()` takes `src_dir` as a required first argument; Python's is keyword-only and infers `src_dir`/`name` from the caller's `__file__` when omitted (R has no equivalent). Pass `src_dir=` explicitly in Python too if you wrap the call in a helper — the inference reads the *immediate* calling frame.
- The internal `output_ui(render_fn, id)` (not exported yet) builds the UI a render function's matching `*Output()` would produce (R counterpart of Python's `Renderer.auto_output_ui()`). It powers R's automatic renderer-dependency discovery (`pkg-r/R/dep-discovery.R`): because R renders the UI before `server()` runs, dependencies can't be inlined into `<head>` like Python's `set_react_page()` — instead, after every flush the session's registered outputs are diffed and new outputs' deps are pushed as a `shinyreact-deps` custom message; the JS bundle loads them and re-runs `bindAll`. The hook is a `.shinyreact_init` client ping (`pkg-js/src/dep-discovery.ts`) handled by the dedicated `shinyreact.init` input handler, so it works with zero configuration, including for module servers mounted after startup.

The deliberate remaining divergences (decided in #184) are recorded in `decisions/2026-08-13-r-python-parity.md`: relative-path resolution, `set_react_page()`'s renderer-dependency discovery, and scalar-array flattening in the default input handler.

### Built assets

`pkg-js/dist/` and `pkg-py/src/shinyreact/www/` are both committed to the repo. After changing JS source, run `make update-dist` to rebuild and copy. `pkg-r/inst/lib/shiny/` is the R counterpart (same flow).

### Build backend

`pyproject.toml` uses hatchling (not uv_build) because the package source lives at `pkg-py/src/shinyreact/` — a non-standard path that requires explicit hatchling configuration.

## Common patterns

### HTMLDependency cache-busting for examples

Shiny serves static files from `HTMLDependency` at `/lib/{name}-{version}/`. The browser caches by URL, so if the version doesn't change, edited JS files won't be picked up. In examples, use the JS file's mtime (in seconds) as the version to auto-bust the cache during development:

```python
_src_dir = Path(__file__).parent
HTMLDependency(
    name="hello-world",
    version=str(int((_src_dir / "hello_world.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "hello_world.js", "defer": ""},
)
```

This is only for examples and development. Published packages should use a fixed version.

### Action buttons

Use the Shiny action button pattern — start at `0`, increment on click:

**JS:**
```js
var [count, setCount] = useShinyInput("my_button", 0, { debounceMs: 0, priority: "event" });
function handleClick() { setCount(count + 1); }
```

`debounceMs: 0` ensures every click is delivered immediately (the default 100ms debounce can coalesce rapid clicks). `priority: "event"` marks it as an event input.

**Python:**
```python
@shinyreact.reactive_output
@reactive.event(input.my_button, ignore_init=True)
def button_response():
    return f"Clicked {input.my_button()} times"
```

`ignore_init=True` prevents firing on page load when `useShinyInput` registers the initial `0` value.

### useShinyInput defaultValue

`defaultValue` is captured on first mount only (same as `React.useState`). Inline literals like `{}` and `[]` are safe — the value is stabilized internally via `useRef`.

### useShinyMessageHandler

Inline arrow functions are safe to pass as the handler — the function is stored in a ref internally, avoiding unnecessary deregister/re-register cycles.

### Hook decomposition

The hook surface follows the Jotai/Recoil cadence — each hook has one responsibility:

| | Full | Read-only | Write-only |
|---|---|---|---|
| **Input** | `useShinyInput(id, default)` → `[value, setValue]` | `useShinyInputValue(id)` → `value` | `useSetShinyInput(id, default)` → `setValue` |
| **Output** | — (no compound) | `useShinyOutputValue(id, default?)` → `value` | — |
| **Output status** | | `useShinyOutputStatus(id)` → `"pending" \| "ready" \| "recalculating" \| "error"` | |

Pick the narrowest hook that fits the call site. A button that pushes events but never reads its own state should use `useSetShinyInput`, not `useShinyInput` with a discarded `[value]`. A display card that just reads should use `useShinyInputValue` / `useShinyOutputValue`. Narrow hooks make data-flow direction visible at the call site, prevent accidental writes from read-only components, and avoid spurious re-renders from subscribing to channels you don't observe.

### Routing input values through Shiny input handlers (`type=`)

`useShinyInput` and `useSetShinyInput` accept an optional `type` that appends `:type` to the wire id, opting into Shiny's server-side input-handler dispatch:

```js
const [when, setWhen] = useShinyInput("when", Math.floor(Date.now() / 1000), {
  type: "shiny.datetime",
});
```

```python
@reactive.effect
def _():
    print(type(input.when()))  # datetime.datetime
```

The handler name is a server-side contract: once an input id has been registered with a `type` (or with no `type`), a later mount disagreeing with that policy throws. Validation rejects empty strings, whitespace, and `:` characters at hook mount.

### The `shinyreact.default` input handler (zero config, R/Python parity)

shinyreact routes every untyped `useShinyInput` value through a built-in
`shinyreact.default` input handler (the JS hook appends `:shinyreact.default`
to the wire id automatically). Its job is to undo the parts of
jsonlite/shiny simplification that would make R disagree with Python about the
same JSON payload — Python's deserializer never simplifies, so both Python
handlers are no-ops.

The contract, in terms of the JSON the React hook sent:

| JSON sent | R | Python |
|---|---|---|
| `[{name, size}, ...]` | list of records | list of dicts |
| `[0, 100]`, `["a", "b"]` | `c(0, 100)` — atomic vector | `[0, 100]` |
| `[]` | `list()` | `[]` |
| `[[1, 2], [3, 4]]` | nesting preserved | nesting preserved |
| anything else | as-is | as-is |

So `for (f in input$x) f$size` works just like Python's
`for f in input.x(): f["size"]`. Flattening a scalar array to an atomic vector
is the one deliberate divergence — it is what R code wants, and it matches
shiny's own default no-type coercion.

The `[]` and nested-array rows are #184 fixes: shiny's default handler turns
`[]` into `NULL` (conflating "empty" with "absent") and flattens
`[[1, 2], [3, 4]]` to `c(1, 2, 3, 4)`, destroying the shape the component sent.

If you need the parsed value returned completely untouched, opt into the
pass-through handler:

```js
useShinyInput("coords", [], { type: "shinyreact.asis" });
```

Both `shinyreact.default` and `shinyreact.asis` are registered in R and Python,
so the same React component is portable across both servers.

### Avoiding flicker on input changes (use status correctly, don't conflate states)

The four output-status values exist for a reason — collapsing them into one boolean leaks DOM churn into the UI. Wrong:

```jsx
const data = useShinyOutputValue("foo");
const status = useShinyOutputStatus("foo");
const isLoading = status !== "ready";        // conflates pending + recalculating
if (!data || isLoading) return <Skeleton/>;  // unmounts the chart on every input change
```

This unmounts the populated card every time the server recomputes — destroying chart/table DOM, briefly showing a skeleton, then re-mounting fresh. Right:

```jsx
const data = useShinyOutputValue("foo");
const status = useShinyOutputStatus("foo");
if (!data) return <Skeleton/>;               // skeleton only when no data has ever arrived
return <Chart className={status === "recalculating" ? "recalculating" : ""} data={data}/>;
```

Plus a CSS rule like `.recalculating { opacity: 0.6; transition: opacity 200ms; }` so the user sees a stale-data cue without DOM tear-down. The chart node survives across input changes and React reconciles in place.

`"pending"` is the only state where you don't have data yet. `"recalculating"` means the server is computing fresh data but the previous result is still mounted — keep showing it. `"error"` is rarely surfaced today; treat like `"ready"` unless you have a use case. If your card doesn't need any of this nuance, just call `useShinyOutputValue` and skip the status entirely.

### Server pattern: fact table + shared `@reactive.calc` + per-output aggregations

Dashboards with several cards driven by the same filter input should follow:

1. **Generate or load a fact table** — long-format, one row per (date, entity) (or whatever the natural grain is).
2. **A single `@reactive.calc filtered_data`** that applies all the inputs (date, search, categories, …) to the fact table.
3. **One `@reactive_output` per card** that calls `filtered_data()` and aggregates to the shape that card needs.

This is what Shiny's reactive graph is good at: each input change recomputes `filtered_data` once and fans out to all cards. Static pre-aggregated tables that some inputs can't touch produce broken-feeling examples — the demo claims to react to a filter that visibly does nothing for half the page.

## The feature tree (`FEATURES.md`)

`FEATURES.md` at the repo root is a nested bullet list of **every behavior shinyreact actually has today** across all three packages, written so a model (or a human) can audit the code against it leaf by leaf.

One file, not one per package. It is organized **by behavior, not by language** — `page_react()`'s Python and R claims sit side by side, so a divergence is a visible leaf instead of a diff you have to run between two files. Language markers do that work:

- **unmarked leaf** — holds in every language its subtree applies to. State shared behavior once.
- **`[py]` / `[r]` / `[js]`** — holds only there. A `[py]` leaf with no `[r]` sibling is either a parity bug or a divergence that needs the marked-leaf treatment below.

Examples are **not** covered yet — deferred to a later pass.

### The format

One rule: **each leaf is one atomically checkable claim.** The tree path tells the auditor *where* the claim lives (data vs. UI vs. reactivity vs. wire); the leaf tells it *what to check*. Sketch, using an example app since it needs no shinyreact context:

```
- histogram of Old Faithful eruption WAITING times
  - data: faithful.csv, column `waiting` (minutes, ~43–96)
    - NOT the `eruptions` column
  - binning matches R's hist(): equal-width, (lo, hi], first bin inclusive
    - server-side, in faithful.py; client only draws
- bins slider
  - range 1–50, default 9 (verify)
  - debounced? no: updates live
  - drives BOTH outputs
    - dist_data: {breaks: number[], counts: number[]}
    - dist_caption: "272 eruptions in N bins"
      - singular "bin" when N=1
- while recalculating: previous chart stays mounted, dims (no skeleton flash)
```

Conventions:

- **Behavior, not implementation.** "title defaults to the app folder name", not "calls `Path(__file__).parent.name`".
- **Specifics or nothing.** Exact ids, defaults, ranges, wire shapes, error messages, singular/plural. "handles empty input" is unauditable; "`[]` stays `list()`, not `NULL`" is.
- **No `file:line` references.** They rot, and locating the claim is the auditor's job. Naming a *file* coarsely ("server-side, in `faithful.py`") is fine and helpful.
- **No prose paragraphs, no code blocks**, other than short inline literals (wire shapes, ids, messages). Explanations belong in `DESIGN.md`, `decisions/`, or this file.
- **Mark uncertainty, don't omit it.** A `(verify)` suffix on a leaf is a valid state and a direct target for the next audit. Silently dropping a claim you weren't sure of is what makes the tree untrustworthy.
- **Present tense, today's code.** Not roadmap, not aspiration. Planned work goes in the issue tracker.
- **Deliberate divergences are sibling leaves**, both stated, with the reason as a child pointing at the decision record — e.g. `[r]` scalar-array flattening in `default_input_handler()` vs. `[py]` no-op → `decisions/2026-08-13-r-python-parity.md`.
- **`(e2e)` marks a leaf pinned by a Playwright test.** Browser-verified behavior is the strongest claim in the file; say so where it applies.

### The completeness bar

A tree that only describes the happy path is worse than useless — it reads as complete while hiding exactly the behavior that breaks. **Derive the tree from an inventory of the source, not from reading order.** Read the whole package, then sweep for each of these and confirm every hit has a leaf:

| Sweep | Why it earns a leaf |
|---|---|
| every public symbol, every parameter, every default | defaults are the most-relied-on, least-documented behavior |
| every `raise` / `warnings.warn` / `cli_abort` | what triggers it, and what the message tells the reader |
| every branch a caller can steer | existence checks, `None` fallbacks, absolute vs. relative paths, marker present/absent |
| every fallback value | `"0"`, `"0.1.0"`, `Path.cwd()` — silent fallbacks are where drift hides |
| every test name in `pkg-*/tests/` | each asserts a behavior; a test with no leaf means the tree is behind the suite |
| every Playwright test | boundary behavior no unit test can express — mark it `(e2e)` |
| every documented security property | e.g. bookmark values appearing in page source |
| every deliberate divergence | with its decision record |

What does *not* earn a leaf: private helper structure, internal call order, type annotations, or anything a reader would check by reading the code rather than by running it.

Two counts worth stating when you finish a pass: how many leaves, and what you deliberately left out (with why). "Thorough" is a claim that needs evidence like any other.

### Keeping it current

`FEATURES.md` is only useful if it is true, so treat it like the test suite:

- **Any PR that changes behavior updates `FEATURES.md` in the same PR** — added, changed, and removed leaves alike. A behavior change with no tree diff is an incomplete PR.
- **When you add a language marker, look for its sibling.** Same reflex as [Cover both R and Python](#cover-both-r-and-python), applied to behavior instead of assertions: does the other language claim this? If not, say why — one-sided (Express-only `set_react_page()`), deliberate (decision record), or a bug worth filing.
- **When reading unfamiliar code, read the tree first**, then verify rather than trust it. If the code and the tree disagree, the code wins and the tree gets fixed.

### Auditing

`/audit-shinyreact-features` walks the leaves and emits, per leaf: `CONFIRMED <file:line>` / `CONTRADICTED <what the code does>` / `NOT FOUND IN CODE`. The reverse pass is equally valuable: **behavior in the code that appears nowhere in the tree** — scope creep, or a real feature nobody documented. Both directions produce work: fix the code, or fix the tree.

The audit is accountable to the same completeness bar: it runs the sweeps above as inventories and reports how many items in each were matched to a leaf, so "I checked everything" is a number rather than an assurance.

## Testing policy

When fixing a bug, add or update unit tests to cover the fix whenever possible. The test should fail without the fix and pass with it. If the fix is purely a type annotation or comment change with no runtime behavior difference, tests are not required.

- **Python tests:** `pkg-py/tests/` — run with `make py-check-tests`
- **R tests:** `pkg-r/tests/testthat/` — run with `make r-check-tests`
- **JS tests:** `pkg-js/src/__tests__/` (the shinyreact layer — `ShinyOutput`) and `pkg-js/src/shiny-react/__tests__/` (the vendored hooks/registries) — run both with `cd pkg-js && npx vitest run`. Requires `make js-setup` first; a missing `node_modules` fails with `ERR_MODULE_NOT_FOUND`, not a test failure
- **Playwright e2e tests:** `pkg-py/tests/playwright/` — run with `make py-test-e2e`. The `[tool.pytest.ini_options]` block ignores this subtree by default so `make py-check-tests` stays fast; `py-test-e2e` clears that with `-o addopts=`. **Adding a new e2e test:** see [`.claude/references/playwright-e2e-tests.md`](.claude/references/playwright-e2e-tests.md) for the fixture-app layout, the four traps that bit us while writing the suite, and the canonical assertion patterns.

### Cover both R and Python

`pkg-py/` and `pkg-r/` are two implementations of one API. **When you add a test to one, add the equivalent to the other** — otherwise coverage drifts, and with it the behavior. Every parity bug found in #182–#186 was in code one language tested and the other did not:

- `page_react_dep()` emitted the wrong script attributes in R for as long as it did because R had **zero** tests for it while Python pinned the attributes (#182).
- The R bookmark script failed to escape U+2028/U+2029 because Python's reliance on `ensure_ascii` was documented in a comment but never asserted, so nothing described the requirement the R port had to meet (#183).
- Python's `page_bare()` emitted two `<title>` elements because the test only checked the title appeared *somewhere*, not once (#186).

Practically, when writing a test ask: **does the other language have this behavior, and is it asserted there?**

- **Yes, and asserted** — nothing to do.
- **Yes, not asserted** — write both. Name them so they're findable from each other, and cross-reference in a comment (e.g. `# Mirrors Python's test_config_script_tag_line_separators_round_trip`).
- **Behavior differs deliberately** — assert the *actual* behavior in each language and say why it differs, pointing at the decision record. `decisions/2026-08-13-r-python-parity.md` is the current one; scalar-array flattening in `default_input_handler()` is the worked example.
- **Genuinely one-sided** — Express-only features (`set_react_page()`) have no R counterpart at all. Note that in the test or the decision record rather than leaving a silent hole.

This applies to helpers too: a payload round-trip helper or fixture written for one language is usually worth porting, since divergent test *scaffolding* hides divergent behavior. `extract_restore_payload()` in `pkg-r/tests/testthat/helper-config.R` is a port of `_extract_restore_payload()` in `pkg-py/tests/test_bookmark_restore.py`.

R currently has no e2e suite; that gap is tracked in #194, so Playwright tests are Python-only for now.

## Open work, examples catalog

- **Open work / known issues** live in the [GitHub issue tracker](https://github.com/posit-dev/shinyreact/issues), not a checked-in TODO file. File substantive work as an issue.
- **`examples/README.md`** — the catalog of what exists today. Add a row when you add an example. The API surface itself is documented in `pkg-py/README.md` / `pkg-r/README.md` and the R pkgdown reference, not in a separate inventory.

## Key decisions

- `decisions/` contains architecture decision records. `decisions/2026-03-17-playwright-testing-architecture.md` documents the recommended approach (code-gen from TypeScript) for future browser testing — not yet implemented.
- `shiny-react` is vendored at `pkg-js/src/shiny-react/` rather than installed as an npm dependency (commit `4137071`).
- The app.py pattern (server-side JSON-spec rendering: `Node`/`node()`, `render_react`, `output_react`, `page_react`, the JS renderer/registry, and the `shinyui` prototype) was removed in #168. History pointers live in a comment on #167.
