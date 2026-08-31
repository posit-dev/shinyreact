# Verifying shinyreact apps (design notes for #201)

**Status:** updated 2026-08-31, after PR #252 merged (closing #201 with the
FEATURES.md description layer, per-example tests, and the jsdom mount
harness — see `.claude/references/verifying-ui-code.md`). This doc keeps the
parts #252 did not cover. The wire layer is now **shipped API**:
`shinyreact.playwright.WireTap` (Python) and `shinyreact::wire_tap()` (R),
unit-tested in `pkg-py/tests/test_wire_tap.py` /
`pkg-r/tests/testthat/test-wire-tap.R`, exercised against a real app in
`pkg-py/tests/playwright/test_wire_frames.py` and the shinytest2 e2e test
in `pkg-r/tests/testthat/test-wire-tap.R`, which runs against
`pkg-r/inst/examples-shiny/01-hello/` — a copy of `examples/01-hello` (app.R
+ www/) shipped in the installed package so the test works everywhere and
the app is available for `shiny::runExample()`-style use.

## The problem

#201 asks "how to verify JS code." The deeper problem is **self-agreement**:
an agent that writes code and then writes the tests for it encodes the same
misunderstanding in both. This bites two different audiences:

1. **shinyreact developers** — our own JS suite. Audited 2026-08-27: every
   test file was committed alongside the feature it tests; mutation testing
   (StrykerJS) on the four best-covered files scored 81.6% with survivors
   like `updateDebounceDelay(){}` (body deleted, all 166 tests pass);
   several tests assert only against hand-written mocks of `window.Shiny`
   whose shape differs from the real `@posit/shiny` API. Line coverage
   (79%) is the misleading number.
2. **App authors** — "I asked the agent for a histogram of *waiting times*;
   how do I know it didn't bin `eruptions`?" No test the same agent writes
   can answer this: it's a prompt→code translation error, and the test
   inherits it.

## Trust model

Split every claim about an app into two kinds:

- **Plumbing** (machine-checkable): input reaches the server, output
  re-renders, counts sum to the row count, module namespacing works. Agents
  can and should test this.
- **Semantics** (author-checkable only): right column, right units, right
  filter. The author is the only holder of the spec, so verification cannot
  be delegated — only made *cheap*. The framework's job is to route the
  spec's observable consequences back to the author in a form faster to
  check than reading code.

The loop: **author verifies evidence once → evidence becomes a snapshot
test → machines keep it true forever after.** Agent-written tests are for
*staying* correct, not *becoming* correct.

## Layer 1: nested feature tree + fresh-model audit

**Status: the tree half shipped in #252** as `examples/*/FEATURES.md` with
`(test)`/`(verify)` leaf markers; per-example tests assert the `(test)`
leaves. Still open: the **fresh-model bidirectional audit** of tree↔code.

A checked-in plain-text feature tree, heavily nested, one falsifiable claim
per leaf:

```
- histogram of Old Faithful eruption WAITING times
  - data: faithful.csv, column `waiting` (minutes, ~43–96)
    - NOT the `eruptions` column
  - binning matches R's hist(): equal-width, (lo, hi], first bin inclusive
- bins slider
  - default 30, updates live
  - drives BOTH outputs
    - dist_data: {breaks: number[], counts: number[]}
    - dist_caption: "272 eruptions in N bins"
      - singular "bin" when N=1
- while recalculating: previous chart stays mounted, dims (no skeleton)
```

A **fresh-context model** (not the one that wrote the code) audits it
**bidirectionally**: spec→code (each leaf `CONFIRMED file:line` /
`CONTRADICTED` / `NOT FOUND`) and code→spec ("the code does X that appears
nowhere in the tree" — scope creep). The auditor never saw the writing
agent's reasoning, so it can't agree with itself.

Rules that make it work:

- Leaves must be falsifiable in code ("singular 'bin' when N=1" is a grep;
  "nice UX" is not).
- The audit runs on every change (definition-of-done or CI), or the tree
  decays into a stale README.
- Declarative library props (`<Bar dataKey="counts">`) are far more
  auditable than hand-rolled SVG math — see "skill guidance" below.

## Layer 2: evidence pack (runtime truth)

Static comparison can't see "renders blank in Chrome" (#166). Per feature,
the agent's definition of done includes evidence the author checks in
seconds:

- **Wire JSON** — the payload that crossed the websocket. `breaks: [43,
  48.3, …]` proves *waiting* in one glance; `[1.6, 1.85, …]` would scream
  *eruptions*.
- **Screenshot** of the running app, axes and labels visible. The human
  eye is the oracle for "does this look like what I asked for."
- **Behavior demo** — "slider at 5 → these counts; at 20 → these."

The author compares evidence to intent — the one glance only they can do.

## Layer 3: independent oracles

Wherever the app reproduces something that already has an answer, pin the
server output against *that*, not against the code's own output:

- R's `hist()` vs Python's `histogram()` — #252 asserted exactly this and
  found a real bug: the Python binner was `[lo, hi)` where R is `(lo, hi]`,
  masked on the Old Faithful data because no observation sits on an interior
  break.
- The spreadsheet/SQL/last-month's-report the app replaces.
- The R/Python twin app: same feature tree, same wire frames — two
  implementations agreeing by accident is unlikely. This repo's twin
  structure is itself a verification asset.

An oracle the agent didn't write is the only test that catches the agent's
misunderstanding.

## Layer 4: wire-capture testing APIs (shipped)

shinyreact's client/server contract is plain JSON on the websocket, so the
evidence in Layer 2 is directly assertable:

| | unit (no browser) | full wire (real client + server) |
|---|---|---|
| **R** | `testServer()` — `output$x` works today; `send_message` has no unit-tier capture (MockShinySession's `sendCustomMessage` is a noop; a recorder helper was prototyped and dropped — `wire_tap()` covers the message channel end-to-end without the `unlockBinding()` hack) | shinytest2 `AppDriver$new(options = list(shiny.trace = TRUE))` → `get_logs()` websocket rows (`location == "chromote"`, `level == "websocket"`, `send `/`recv ` prefixed). See `spikes/201-wire-verification/shinytest2-ws-frames.R` |
| **Python** | fake session (`AsyncMock`) — the pattern in `pkg-py/tests/test_send_message.py`; for outputs, factor computation into plain functions (the `faithful.py` pattern) since py-shiny has no `testServer` | Playwright `page.on("websocket")` frame capture. See `pkg-py/tests/playwright/test_wire_frames.py` |

The full-wire tier asserts **both directions**, which makes previously
unverifiable client behavior testable: the `:shinyreact.default` wire-id
suffix, `debounceMs` coalescing, `priority: "event"`, initial-value
delivery. The shinytest2 route also chips at #194 (no R e2e suite).

**`WireTap`: one API, identical in both languages** (`WireTap(page)` in
Python, `wire_tap(app)` in R). Cross-channel frame order is
reactive-scheduling coincidence, not contract: outputs batch arbitrarily
into `values` frames, flush order shifts, busy/progress frames interleave.
Exposing an ordered global frame array would invite authors to pin exactly
that incidental ordering. So the public surface is per-channel only —
within one channel (one output id, one message type, one input id) wire
order *is* guaranteed:

```
# retrying expectations — matcher is a value (equality) or fn (truthy),
# playwright-style (cf. page.expect_response(url_or_predicate)):
expect_output_value(id, matcher, timeout)
expect_message(id, matcher, timeout)      # send_message payloads: {id, data}
expect_input_value(id, matcher, timeout)

# complete recorded history, cursor-independent (playwright's all_ idiom):
all_output_values(id) / all_messages(id) / all_input_values(id)
```

Missed-middle-value safeguard: capture is lossless (every frame is recorded
by the event handler / shinytest2 log), so the `expect_*` methods never
check "latest" — they scan the recorded history from a per-channel cursor
and consume through the match. Successive expectations therefore assert an
ordered subsequence; a value that arrived between checks is still in
history where the next expectation will meet it. Polling only decides when
to re-scan, never what was seen. A matcher that errors on a value's shape
(e.g. the early `dist_data: null` frame) counts as a non-match; the timeout
error reports the values scanned and the last matcher error. Attach before
`goto` — history is complete from attach onward. `input_values` matches the
bare id or any `id:type` wire id, so callers use the id they wrote in
`useShinyInput()`.

Both implementations assert the same things on 01-hello:
`expect_input_value("bins", 30)` (hook default, via the
`:shinyreact.default` wire id) and `expect_output_value("dist_data", fn)`
with `breaks[0] == 43` (waiting, not eruptions — eruptions would start at
~1.6) and `sum(counts) == 272` (every row binned). Known small divergence:
jsonlite maps a JSON `null` output value to `NULL`, indistinguishable from
an absent key, so R drops early null frames that Python sees as `None`.

**Shipped as:** `shinyreact.playwright.WireTap` — the module import (not
the package) requires playwright, keeping it a test-only dependency — and
`shinyreact::wire_tap(app)`, which checks at runtime that shinytest2 is
installed (Suggests, not Imports) and that `app$get_logs()` returns a data
frame with `location`/`level`/`message` columns before doing anything else.
Both READMEs carry a usage section; the R export is pinned in the
API-surface test and documented in pkgdown under "Testing".

Declined: exporting a `record_messages()` testServer helper — it needed
`unlockBinding()` surgery on MockShinySession, and `wire_tap()` covers the
message channel end-to-end. The clean unit-tier version is an upstream
rstudio/shiny change (MockShinySession recording custom messages natively);
file that issue if testServer-tier message assertions turn out to matter.

## Guidance for a "write-shinyreact" skill (#199/#200)

**Core principle: minimize agent-authored surface.** A trusted library is
an oracle the agent didn't write; what remains is glue mapping wire JSON →
library props, which is small and auditable against the feature tree.

- **A ladder, not a mandate:** native HTML/CSS → `window.shinyreact`
  primitives (`ShinyOutput` gives plotly/DT for free) → allowlisted library
  → hand-rolled last. Verification effort scales with the rung: hand-rolled
  rendering triggers the full evidence pack; library glue needs only the
  payload check.
- **Short allowlist with pinned, known-good snippets** (e.g. Recharts,
  shadcn/ui — already in examples 03/04, TanStack Table), not "use
  libraries" — open-ended choice invites hallucinated APIs.
- **The duplicate-React trap goes in the skill:** libraries mean a Vite
  build, and downstream builds must externalize to `window.React` /
  `window.ReactDOM` or ship a second React — a runtime-only crash, exactly
  the class static checks miss (#166).
- **Make the build fork explicit:** no-build `www/app.js` for toy apps;
  Vite + allowlist for anything with real UI.
- **Definition of done = the evidence pack + feature-tree audit**, not
  "vitest passes."

## For shinyreact's own JS suite (secondary, from the same audit)

1. Write the hook contracts down in prose (`pkg-js/` has no README); tests
   cite the line they enforce. Prerequisite for everything else; feeds #86.
   (Partly superseded: `protocol/surface.json` now pins the wire shapes.)
2. Mutation testing in the authoring loop (`make js-test-mutation`; Stryker
   ran 4 files in 62s). The mechanical answer to "would this test pass if
   the behavior were wrong?"
3. Type the fakes: one `test-utils/fake-shiny.ts` typed against
   `@posit/shiny`'s real types, zero `as any`, tests inside `tsc --noEmit`.
4. Push un-mockable guarantees (debounce, priority, output-status sequence)
   to the wire tier above — unit-mocking them is what produced the current
   holes.

## Work items

1. ~~Ship the wire-capture helpers with docs~~ — done: `WireTap` /
   `wire_tap()` exported, unit + e2e tested, READMEs updated.
2. Prototype the fresh-model bidirectional audit of `FEATURES.md`↔code on
   01-hello (the tree itself shipped in #252), evaluate what it catches.
3. Fold the evidence pack (Layer 2) and audit into the write-shinyreact
   skill as definition-of-done.
4. JS-suite hardening per the audit (separate issue; overlaps #86, #194).
5. ~~Export `record_messages()`~~ — declined (see Layer 4); file the
   upstream MockShinySession issue if testServer-tier message assertions
   turn out to matter.
