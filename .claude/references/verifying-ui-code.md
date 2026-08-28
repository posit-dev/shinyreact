# Verifying UI code (answer to the #201 spike)

**The problem.** An agent that writes the client and then writes the client's
tests is agreeing with itself. The tests still catch regressions, but they
cannot catch a misunderstanding — both artifacts encode the same wrong idea.

**What actually breaks the loop** is not a better test framework. It is putting
an independent description of the behavior between the code and the test, and
writing the test against the *description*:

```
app behavior  →  FEATURES.md leaf  →  test asserting that leaf
   (code)          (plain English)        (jsdom / pytest / testthat)
```

The description has to be falsifiable by a human at a glance ("the first column
has no `←` button") and it has to be written from the running app or the source
you are porting — not from the code you are about to write. Then a test that
passes while the description is wrong is a *visible* disagreement, because the
description is readable by someone who will never read the test.

That is why the examples carry `examples/*/FEATURES.md` and why
`shinyreact-convert-app` produces the description before any code.

## Where the tests live

**Beside the app, run by the package.** Each example keeps its own tests in
`examples/<app>/tests/` — `test_*.py`, `test-*.R`, `ui.test.ts` — because they
describe that app, and someone reading the app should find them without
knowing the repo's package layout.

Every package's test run includes them anyway, so a package change that breaks
an example fails immediately rather than at the next manual run:

| Package | How |
|---|---|
| Python | `testpaths = ["pkg-py/tests", "examples"]` in `pyproject.toml` |
| JS | `include: [..., "../examples/**/tests/*.test.ts"]` in `pkg-js/vitest.config.ts` (with `resolve.alias` + `server.fs.allow`, since the files sit outside the package root) |
| R | `pkg-r/tests/testthat/test-examples.R` sources every `examples/*/tests/test-*.R`, and skips when `examples/` is absent (installed package) |

## The three layers, and what each can actually prove

| Layer | Proves | Cost |
|---|---|---|
| Pure functions in their own module | binning, formatting, conversions | trivial — do this always |
| Client mounted in jsdom against a fake Shiny | rendering, input wiring, wire ids, status handling | low, and it exercises the file the app ships |
| Playwright | layout, real Shiny, real bindings, real browser | high; reserve for what the layers above cannot see |

### Layer 1 — factor the logic out of the app file

`examples/01-hello/faithful.py` is the pattern: the binner lives in a module
beside `app.py`, so `examples/01-hello/tests/test_faithful.py` can import and
assert it. Every other example puts its logic inside `app.py` next to
`set_react_page()`, which makes it unimportable and therefore untested. That is
the single cheapest thing to fix in a new app.

When the same logic exists in R and Python, assert the **same golden values in
both files** and cross-reference them in a comment. That is what turned up a
real divergence: the Python binner truncated (`[lo, hi)`) while R's `hist()`
is right-closed (`(lo, hi]`), and they agreed on the Old Faithful data only
because no observation lands on an interior break. One shared golden vector
plus one boundary case found it.

### Layer 2 — mount the real client in jsdom

`examples/testing/mount.ts` reads an example's `www/ui.js` off disk and
evaluates it the way a browser evaluates a classic script, against the
real `window.shinyreact` global and the real hooks and registries. Only Shiny
is faked.

```ts
const app = await mountExample("01-hello");
await app.setOutput("dist_data", { breaks, counts });   // pretend the server answered
expect(app.container.querySelectorAll("rect").length).toBe(9);

await app.settleDebounce();                             // wait out the input debounce
expect(app.lastInput("bins:shinyreact.default")).toBe(30);
```

Why this shape and not `render(<App/>)`:

- It tests **the file the app ships**, not a copy of the component. A test that
  imports a component the app does not use is testing nothing.
- It sees the **wire**. `inputCalls` records every `Shiny.setInputValue`, so
  you can assert the wire id including its `:type` suffix — which is how the
  08-input-handler test proves `type: "shiny.datetime"` bypasses
  `shinyreact.default`.
- It sees **status**, not just values. `setRecalculating` is how you pin the
  "chart stays mounted and dims" idiom, including that it is the *same* DOM
  node before and after.

Traps, all of which cost time to rediscover:

- **`fireEvent.change`, not `el.dispatchEvent(new Event("change"))`.** React
  tracks the native value setter; a raw event on a directly-assigned `value`
  is silently ignored. (`onInput` handlers are the exception and work either
  way.)
- **Debounce is real.** `useShinyInput`'s default is 100 ms, so nothing is on
  the wire immediately after mount — `await app.settleDebounce()`. And two
  actions inside one tick coalesce *even at `debounceMs: 0`*, so to prove "no
  coalescing" put a real gap between them; asserting it within a tick tests the
  test, not the app.
- **The output registry appends its own hidden div to `<body>`.** The
  example's mount container is the other child.
- Examples whose `www/ui.js` is a build artifact (03, 04, 09) are gitignored
  and cannot be mounted. Test the shared behavior on the no-build twin (02
  covers 03) and say so in the `FEATURES.md`.
- jsdom has no layout and the fake Shiny runs no bindings, so anything reading
  geometry, and anything a widget draws, is out of reach. For `ShinyOutput`
  the testable contract is the **host element's shape** — tag, id, classes —
  which is the part the example owns.

### Layer 3 — Playwright

See [`playwright-e2e-tests.md`](playwright-e2e-tests.md). Use it for what
layers 1 and 2 structurally cannot reach, not to re-assert them more slowly.

## Checklist for a new UI test

1. Is there a `FEATURES.md` leaf for this behavior? If not, write it first — in
   plain English, from the app, before the test.
2. Can it be a pure function instead? Move it out of the app file.
3. Assert what a user or the server would observe: DOM text, element shape,
   wire messages. Not internal state, not implementation calls.
4. Does the other language have this behavior? Mirror the golden values and
   cross-reference. (See "Cover both R and Python" in `CLAUDE.md`.)
5. Mark the leaf `(test)` in the same PR.
