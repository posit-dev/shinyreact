# shinyreact.default Input Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make array-of-objects `useShinyInput` values arrive on the R server as a clean list of records (matching Python's list of dicts), with zero changes required in JS components.

**Architecture:** shinyreact's JS hooks default every untyped input's wire id to the `:shinyreact.default` suffix. shinyreact registers two input handlers in both R and Python: `shinyreact.default` (the global default — in R a smart handler that preserves arrays-of-objects but still flattens scalar arrays as Shiny does; in Python a no-op) and `shinyreact.asis` (an opt-in pure pass-through). An explicit `type=` still overrides the default.

**Tech Stack:** TypeScript/React (Vite IIFE, vitest), R (`shiny::registerInputHandler`, testthat), Python (`shiny.input_handler`, pytest).

**Design reference:** `docs/superpowers/specs/2026-06-04-shinyreact-default-input-handler-design.md`

---

## File Structure

- `js/src/shiny-react/input-registry.ts` — add `DEFAULT_TYPE` constant; default the wire suffix in `setShinyInputValue`. (modify)
- `js/src/shiny-react/__tests__/input-registry.test.ts` — flip bare-id assertions to `:shinyreact.default`. (modify)
- `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx` — flip the "no suffix" case to the default suffix. (modify)
- `pkg-r/R/input-handler.R` — `default_input_handler()` + `asis_input_handler()` as named, directly-testable functions. (create)
- `pkg-r/R/zzz.R` — `.onLoad` registers both handlers. (create)
- `pkg-r/tests/testthat/test-input-handler.R` — unit tests for both handlers + registration presence. (create)
- `pkg-py/src/shinyreact/_input_handler.py` — register both handlers at import. (create)
- `pkg-py/src/shinyreact/__init__.py` — import `_input_handler` for its side effect. (modify)
- `pkg-py/tests/test_input_handler.py` — unit tests for both handlers. (create)
- `examples/app-r/02-inputs/app.R` — simplify `output$fileout` to iterate the clean records. (modify)
- `CLAUDE.md`, `docs/features.md`, `docs/todos.md` — docs. (modify)

---

## Task 1: JS — default the wire suffix to `shinyreact.default`

**Files:**
- Modify: `js/src/shiny-react/input-registry.ts:7-37`
- Test: `js/src/shiny-react/__tests__/input-registry.test.ts`, `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx`

- [ ] **Step 1: Update the existing "no suffix" registry test to expect the default suffix**

In `js/src/shiny-react/__tests__/input-registry.test.ts`, replace the test at lines 147-161:

```ts
  it("type defaults to undefined and the wire id has the shinyreact.default suffix", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:shinyreact.default",
      1,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd js && npx vitest run src/shiny-react/__tests__/input-registry.test.ts -t "shinyreact.default suffix"`
Expected: FAIL — actual call is `"foo"`, expected `"foo:shinyreact.default"`.

- [ ] **Step 3: Implement the default suffix**

In `js/src/shiny-react/input-registry.ts`, add the constant inside the class (after line 7's `export class InputRegistryEntry<T> {`) and change `setShinyInputValue` (lines 34-37):

```ts
export class InputRegistryEntry<T> {
  /** Wire-id suffix applied when no explicit `type` is set, so untyped inputs
   * route through shinyreact's server-side handler (clean records on R). */
  private static readonly DEFAULT_TYPE = "shinyreact.default";

  id: string; // Shiny input ID
```

```ts
  private setShinyInputValue(value: T) {
    const wireId = `${this.id}:${this.type ?? InputRegistryEntry.DEFAULT_TYPE}`;
    getShiny()?.setInputValue?.(wireId, value, this.opts);
  }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd js && npx vitest run src/shiny-react/__tests__/input-registry.test.ts -t "shinyreact.default suffix"`
Expected: PASS

- [ ] **Step 5: Fix the now-broken bare-id assertions in `input-registry.test.ts`**

Three remaining assertions still expect the bare id `"test"`. Update each `expect(mockSetInputValue).toHaveBeenCalledWith(` block:

- Lines 75-79 (`"calls Shiny.setInputValue when Shiny is available"`): change `"test"` → `"test:shinyreact.default"`.
- Lines 113-117 (`"real value after MISSING calls setInputValue"`): change `"test"` → `"test:shinyreact.default"`.
- Lines 129-133 (`"null value (without MISSING) still calls setInputValue"`): change `"test"` → `"test:shinyreact.default"`.
- Lines 245-249 (`"updateType after undefined finalizes 'no type'; later string throws"`): change `"foo"` → `"foo:shinyreact.default"`.

Leave the explicit-type assertions (`"foo:shiny.datetime"`, `"foo:X"`) unchanged.

- [ ] **Step 6: Fix the "no suffix" case in `use-shiny-input-type.test.tsx`**

Replace the test at lines 127-141 of `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx`:

```tsx
  it("uses the shinyreact.default suffix when type is not set", async () => {
    render(<ProducerFull id="foo" />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter((c) => c[0].startsWith("foo"));
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("foo:shinyreact.default");
    }
  });
```

- [ ] **Step 7: Run the full JS test suite + typecheck**

Run: `cd js && npx vitest run && npm run lint` (or `make js-lint`)
Expected: all tests PASS, `tsc --noEmit` clean.

- [ ] **Step 8: Rebuild and copy the bundles**

Run: `make update-dist`
Expected: rebuilds `js/dist/` and copies into `pkg-py/src/shinyreact/www/` and `pkg-r/inst/lib/shiny/`.

- [ ] **Step 9: Commit**

```bash
git add js/src/shiny-react/input-registry.ts js/src/shiny-react/__tests__/ js/dist/ pkg-py/src/shinyreact/www/ pkg-r/inst/lib/shiny/
git commit -m "feat(js): default untyped inputs to the shinyreact.default handler (#124)"
```

---

## Task 2: R — register `shinyreact.default` and `shinyreact.asis` handlers

**Files:**
- Create: `pkg-r/R/input-handler.R`
- Create: `pkg-r/R/zzz.R`
- Test: `pkg-r/tests/testthat/test-input-handler.R`

- [ ] **Step 1: Write the failing tests**

Create `pkg-r/tests/testthat/test-input-handler.R`:

```r
test_that("default_input_handler preserves arrays of objects as a list of records", {
  records <- list(
    list(name = "a", size = 1L),
    list(name = "b", size = 2L)
  )
  expect_identical(default_input_handler(records), records)
})

test_that("default_input_handler flattens scalar arrays to atomic vectors", {
  expect_equal(default_input_handler(list(0, 100)), c(0, 100))
  expect_equal(default_input_handler(list("a", "b")), c("a", "b"))
})

test_that("default_input_handler leaves scalars and single objects unchanged", {
  expect_equal(default_input_handler(5L), 5L)
  expect_identical(default_input_handler(list(a = 1L)), list(a = 1L))
})

test_that("default_input_handler returns NULL for an empty array and flattens nested arrays", {
  expect_null(default_input_handler(list()))
  expect_equal(default_input_handler(list(list(1, 2), list(3, 4))), c(1, 2, 3, 4))
})

test_that("asis_input_handler returns the value completely untouched", {
  expect_identical(asis_input_handler(list(0, 100)), list(0, 100))
  records <- list(list(name = "a"), list(name = "b"))
  expect_identical(asis_input_handler(records), records)
})

test_that("both handlers are registered with shiny on load", {
  expect_false(is.null(shiny:::inputHandlers$get("shinyreact.default")))
  expect_false(is.null(shiny:::inputHandlers$get("shinyreact.asis")))
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-input-handler.R")'`
Expected: FAIL — `could not find function "default_input_handler"`.

- [ ] **Step 3: Implement the handler functions**

Create `pkg-r/R/input-handler.R`:

```r
# Built-in shinyreact input handlers, registered with shiny in .onLoad (zzz.R).
# See docs/superpowers/specs/2026-06-04-shinyreact-default-input-handler-design.md.

#' Default shinyreact input handler (internal)
#'
#' Applied to every untyped `useShinyInput` value. Preserves an array of objects
#' (an unnamed list whose every element is a named list) as a list of records,
#' matching Python's list-of-dicts. For all other shapes it reproduces shiny's
#' default no-type coercion: unnamed lists of scalars are flattened with
#' `unlist()`, everything else is returned as-is.
#' @keywords internal
default_input_handler <- function(value, session = NULL, name = NULL) {
  is_records <- is.list(value) && is.null(names(value)) &&
    length(value) > 0 &&
    all(vapply(
      value,
      function(el) is.list(el) && !is.null(names(el)),
      logical(1)
    ))
  if (is_records) {
    return(value)
  }
  if (is.list(value) && is.null(names(value))) {
    return(unlist(value, recursive = TRUE))
  }
  value
}

#' As-is shinyreact input handler (internal)
#'
#' Opt-in via `type = "shinyreact.asis"`. Returns the parsed value completely
#' untouched (no flattening), for nested structures the default would coerce.
#' @keywords internal
asis_input_handler <- function(value, session = NULL, name = NULL) {
  value
}
```

- [ ] **Step 4: Implement the registration**

Create `pkg-r/R/zzz.R`:

```r
.onLoad <- function(libname, pkgname) {
  shiny::registerInputHandler("shinyreact.default", default_input_handler, force = TRUE)
  shiny::registerInputHandler("shinyreact.asis", asis_input_handler, force = TRUE)
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd pkg-r && Rscript -e 'devtools::load_all("."); testthat::test_file("tests/testthat/test-input-handler.R")'`
Expected: PASS (all 6 tests).

- [ ] **Step 6: Regenerate docs and format**

Run: `make r-format` (and `cd pkg-r && Rscript -e 'devtools::document(".")'` if NAMESPACE/Rd need updating — these functions are internal so no exports change).
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add pkg-r/R/input-handler.R pkg-r/R/zzz.R pkg-r/tests/testthat/test-input-handler.R
git commit -m "feat(r): register shinyreact.default and shinyreact.asis input handlers (#124)"
```

---

## Task 3: Python — register `shinyreact.default` and `shinyreact.asis` handlers

**Files:**
- Create: `pkg-py/src/shinyreact/_input_handler.py`
- Modify: `pkg-py/src/shinyreact/__init__.py`
- Test: `pkg-py/tests/test_input_handler.py`

- [ ] **Step 1: Write the failing tests**

Create `pkg-py/tests/test_input_handler.py`:

```python
from shiny.input_handler import input_handlers

import shinyreact  # noqa: F401  (import registers the handlers)


def test_both_handlers_are_registered():
    assert "shinyreact.default" in input_handlers
    assert "shinyreact.asis" in input_handlers


def test_default_handler_returns_value_unchanged():
    handler = input_handlers["shinyreact.default"]
    records = [{"name": "a", "size": 1}, {"name": "b", "size": 2}]
    assert handler(records, None, None) == records
    assert handler([0, 100], None, None) == [0, 100]
    assert handler(5, None, None) == 5
    assert handler([], None, None) == []


def test_asis_handler_returns_value_unchanged():
    handler = input_handlers["shinyreact.asis"]
    records = [{"name": "a"}, {"name": "b"}]
    assert handler(records, None, None) == records
    assert handler([0, 100], None, None) == [0, 100]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest pkg-py/tests/test_input_handler.py -v`
Expected: FAIL — `"shinyreact.default" not in input_handlers` (KeyError / assertion).

- [ ] **Step 3: Implement the handlers**

Create `pkg-py/src/shinyreact/_input_handler.py`:

```python
"""Built-in shinyreact input handlers, registered on import.

See docs/superpowers/specs/2026-06-04-shinyreact-default-input-handler-design.md.

Python's deserializer never simplifies the way R's does (an array of objects is
already a list of dicts), so both handlers are no-ops here. They exist so that
the ``:shinyreact.default`` / ``:shinyreact.asis`` wire suffixes do not raise
"No input handler registered for type" on the Python server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shiny.input_handler import input_handlers

if TYPE_CHECKING:
    from shiny.module import ResolvedId
    from shiny.session import Session


@input_handlers.add("shinyreact.default", force=True)
def _(value: Any, name: ResolvedId, session: Session) -> Any:
    return value


@input_handlers.add("shinyreact.asis", force=True)
def _(value: Any, name: ResolvedId, session: Session) -> Any:
    return value
```

- [ ] **Step 4: Import it for its registration side effect**

In `pkg-py/src/shinyreact/__init__.py`, add after the existing `from ._spec import Node` line (line 6):

```python
from . import _input_handler as _input_handler  # noqa: F401  (registers input handlers)
```

(Do not add it to `__all__` — it is a side-effect import, not public API.)

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest pkg-py/tests/test_input_handler.py -v`
Expected: PASS (all 3 tests).

- [ ] **Step 6: Format + typecheck**

Run: `make py-format && make py-check-types`
Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add pkg-py/src/shinyreact/_input_handler.py pkg-py/src/shinyreact/__init__.py pkg-py/tests/test_input_handler.py
git commit -m "feat(py): register shinyreact.default and shinyreact.asis input handlers (#124)"
```

---

## Task 4: Example — simplify `examples/app-r/02-inputs` to the clean records shape

**Files:**
- Modify: `examples/app-r/02-inputs/app.R:176-208`

- [ ] **Step 1: Replace the `output$fileout` reshaping workaround**

In `examples/app-r/02-inputs/app.R`, replace the entire `output$fileout <- reactive_output({ ... })` block (lines 176-208) with:

```r
  output$fileout <- reactive_output({
    files <- input$filein
    if (is.null(files) || length(files) == 0) {
      return(NULL)
    }
    # shinyreact's default input handler delivers the JS file-metadata array as
    # a clean list of records (one named list per file), matching Python's
    # list of dicts — so we can index each file's fields directly.
    summaries <- vapply(
      files,
      function(f) {
        size_kb <- round(as.numeric(f$size) / 1024, 1)
        type_str <- if (nzchar(f$type)) f$type else "unknown type"
        paste0(f$name, " (", size_kb, " KB, ", type_str, ")")
      },
      character(1)
    )
    paste(summaries, collapse = "\n")
  })
```

- [ ] **Step 2: Verify the example runs (manual smoke test)**

Run: `cd examples/app-r/02-inputs && Rscript -e 'shiny::runApp(".", launch.browser = FALSE, port = 8000)'` (Ctrl-C to stop), then in a browser upload two files and confirm the file-output card lists `name (size KB, type)` per file with no R error in the console.
Expected: each uploaded file is summarized; no `$ operator is invalid for atomic vectors` error.

- [ ] **Step 3: Commit**

```bash
git add examples/app-r/02-inputs/app.R
git commit -m "docs(example): simplify app-r/02-inputs fileout to clean records (#124)"
```

---

## Task 5: Docs — CLAUDE.md, features.md, todos.md

**Files:**
- Modify: `CLAUDE.md` (the "Common patterns" section)
- Modify: `docs/features.md`
- Modify: `docs/todos.md`

- [ ] **Step 1: Add a "Common patterns" subsection to CLAUDE.md**

In `CLAUDE.md`, under `## Common patterns`, add a new subsection (place it after the existing "Routing input values through Shiny input handlers (`type=`)" subsection):

```markdown
### Arrays of records arrive clean on R (zero config)

shinyreact routes every untyped `useShinyInput` value through a built-in
`shinyreact.default` input handler (the JS hook appends `:shinyreact.default`
to the wire id automatically). On R this means a JS component sending an array
of objects — e.g. `[{name, size, type}, ...]` — arrives as a clean list of
records, so `for (f in input$x) f$size` works just like Python's
`for f in input.x(): f["size"]`. Scalar arrays (`[0, 100]`, `["a", "b"]`) are
still flattened to atomic vectors, exactly as Shiny does by default.

If you need the parsed value returned completely untouched (e.g. a nested array
the default would flatten), opt into the pass-through handler:

```js
useShinyInput("coords", [], { type: "shinyreact.asis" });
```

Both `shinyreact.default` and `shinyreact.asis` are registered in R and Python,
so the same React component is portable across both servers.
```

- [ ] **Step 2: Note the handlers in features.md**

In `docs/features.md`, add an entry (in the JS-bridge / input section) noting the two built-in input handlers: `shinyreact.default` (applied automatically to untyped inputs; clean list of records on R) and `shinyreact.asis` (opt-in pure pass-through via `type="shinyreact.asis"`).

- [ ] **Step 3: Resolve the related TODO**

In `docs/todos.md`, remove (or trim to a "done" pointer to issue #124) the "Python-side input handlers for useShinyInput values" item and any array-of-objects R wire-shape note, since #124 resolves the R footgun.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/features.md docs/todos.md
git commit -m "docs: document shinyreact.default / shinyreact.asis input handlers (#124)"
```

---

## Task 6: Full verification across all three packages

**Files:** none (verification only)

- [ ] **Step 1: JS**

Run: `make js-lint && cd js && npx vitest run`
Expected: typecheck clean, all vitest tests PASS.

- [ ] **Step 2: Python**

Run: `make py-check`
Expected: format check, pyright, and pytest all PASS.

- [ ] **Step 3: R**

Run: `make r-check`
Expected: format check, testthat, and R CMD check PASS.

- [ ] **Step 4: Confirm bundles are in sync**

Run: `git status --porcelain`
Expected: clean working tree — if `make update-dist` (Task 1 Step 8) produced uncommitted bundle changes, commit them now:

```bash
git add js/dist/ pkg-py/src/shinyreact/www/ pkg-r/inst/lib/shiny/
git commit -m "chore: sync built bundles (#124)"
```
