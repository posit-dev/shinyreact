# Playwright Testing Architecture for shinyreact

**Date:** 2026-03-17
**Status:** Exploration complete, decision deferred — code-gen approach recommended

## Context

shinyreact is a monorepo with three sub-packages: `js/` (TypeScript/React), `pkg-py/` (Python Shiny), and `pkg-r/` (R Shiny, placeholder). The JS bundle renders JSON specs into React components via an in-house Spec walker. Currently there are 10 Python unit tests (pytest) but zero JavaScript or browser tests — no Playwright, Cypress, or any browser testing infrastructure exists.

The goal is to add end-to-end browser testing with a **controllers pattern** similar to `shiny.playwright.controllers`, where reusable controller classes wrap UI elements with locator properties, action methods (`set()`, `click()`), and assertion methods (`expect_value()`, `expect_label()`).

The key architectural requirement: **TypeScript should be the single source of truth** for controller definitions. Python and R should consume the same testing logic rather than independently maintaining parallel controller implementations.

## The `shiny.playwright.controllers` Pattern (Reference)

The existing Shiny pattern that we want to mirror works as follows:

- **Base classes** (`UiBase`, `UiWithContainer`, `UiWithLabel`) accept a `Page` and `id`, converting CSS selectors into Playwright `Locator` objects.
- **Mixin classes** provide reusable capabilities (`_SetTextM`, `_ExpectTextInputValueM`, `WidthContainerStyleM`) using Python `Protocol`-typed `self` for type safety.
- **Concrete controllers** compose mixins + base class via multiple inheritance, each defining a CSS selector in `__init__` that targets a specific Shiny UI element.
- **Three method categories** per controller: locator properties (`self.loc`, `self.loc_container`), action methods (`set()`, `click()`), and assertion methods (`expect_value()`, `expect_label()`).
- **All assertions** delegate to `playwright_expect(locator)` — Playwright's built-in expect API with auto-retry, actionability checks, and rich error messages. Bare `assert` is never used.
- **All methods** accept a `timeout` parameter for Playwright's retry mechanism.
- **Design principles** (from source comments): mirror Playwright API naming, no properties (only methods, to allow timeout params), use locators/playwright_expect exclusively, only add `set` methods for user-performable actions.

Example usage:
```python
text_input = controller.InputText(page, "name")
text_input.expect_label("Your Name")
text_input.set("Alice")
output = controller.OutputText(page, "result")
output.expect_value("Hello, Alice!")
```

## Critical Constraint: Where Playwright's APIs Run

**Playwright's `expect()` and actionability checks run in the host process (Node.js or Python), not in the browser.** They communicate with the browser via the Chrome DevTools Protocol (CDP). Code running inside `page.evaluate()` has access to standard browser APIs (`querySelector`, `textContent`, etc.) but NOT to Playwright's locator, expect, or actionability APIs.

This constraint eliminates the originally envisioned architecture where Python/R would call `page.evaluate()` to run JS-based controllers that use Playwright's expect internally. That approach is architecturally impossible.

## Approaches Evaluated

### Approach 1: Node.js Bridge (RPC)

**Description:** Controllers are written in TypeScript using Playwright's Node.js API (`Page`, `Locator`, `expect()`). A small Node.js server or process exposes these controllers via an RPC mechanism (HTTP, WebSocket, or stdin/stdout). Python/R call the API to invoke controller methods. The Node.js process holds the Playwright browser instance.

**Pros:**
- 100% real Playwright expect and actionability checks
- Single source of truth in TypeScript
- Controllers are independently testable via `@playwright/test`

**Cons:**
- **Two processes required** — a Node.js process for Playwright and a Python/R process for the Shiny app. These must coordinate browser instance sharing, app lifecycle, and error propagation.
- **Browser ownership conflict** — if Python starts a Playwright browser (as `shiny.playwright` does), and Node.js also needs to control it, they must share the CDP endpoint via `browserType.connect()`. This adds fragile coordination.
- **Heavy architecture** — RPC serialization, error marshaling, timeout propagation across process boundaries, and connection lifecycle management are all non-trivial.
- **Debugging difficulty** — stack traces span two processes, making test failures harder to diagnose.
- **Dependency burden** — downstream packages and users must have Node.js installed and manage npm dependencies alongside their Python/R environment.

**Verdict:** Too much architectural complexity for the current project maturity. The coordination overhead between two processes outweighs the benefit of sharing literal TS code.

### Approach 2: Shell Out to TypeScript Test Runner

**Description:** Python/R only start the Shiny app server. All browser interaction is handled by TypeScript via `npx playwright test`. Python/R invoke the TS test runner as a subprocess, passing the app URL and test parameters. Results come back via exit code and stdout/stderr.

**Example:**
```python
# Python test
def test_output_renders(app: AppFixture):
    result = subprocess.run(
        ["npx", "playwright", "test",
         "--grep", "output renders correctly",
         "--base-url", app.url],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
```

```typescript
// TypeScript test (the real logic)
import { test, expect } from '@playwright/test';
import { ShinyreactOutput } from '../controllers';

test('output renders correctly', async ({ page, baseURL }) => {
  await page.goto(baseURL!);
  const output = new ShinyreactOutput(page, 'my_output');
  await output.expectValue('hello');
});
```

**Pros:**
- 100% real Playwright with zero reimplementation
- Single source of truth — all test logic lives in TypeScript
- TS tests are independently runnable
- Dead simple Python/R code (just subprocess calls)

**Cons:**
- **Two test runners** — pytest and Playwright test must coordinate. Test discovery, filtering, parallelism, and reporting are split across two systems.
- **Subprocess overhead** — each test invocation spawns a new Node.js process, adding latency (cold start ~1-2 seconds per test).
- **No interleaving** — cannot mix Python/R assertions with browser assertions in the same test. If a test needs to verify server-side state AND browser state, it requires two separate test files or a custom protocol.
- **Poor debuggability** — Python sees only exit codes and stderr text. No programmatic access to which assertion failed, what the expected vs actual values were, or screenshots from failure.
- **App lifecycle coordination** — Python must start the app, wait for it to be ready, pass the URL to the subprocess, and tear it down after. Race conditions are possible.
- **Node.js required** — same dependency burden as Approach 1.

**Verdict:** Simple but too coarse-grained. The inability to interleave host-language and browser assertions makes it unsuitable for real-world Shiny testing where server state and UI state must be verified together.

### Approach 3: Browser-Native Assertion Library

**Description:** Build a lightweight assertion/wait library in TypeScript that runs inside the browser (via `page.evaluate()`). Controllers are browser-resident JS objects that use `MutationObserver`, DOM polling, and visibility checks to implement expect-like behavior. Python/R call `page.evaluate()` to invoke controller methods, which return Promises that resolve when assertions pass or reject on timeout.

**Example:**
```python
# Python
page.evaluate("await shinyreactTest.output('my_output').expectValue('hello')")
```

```typescript
// Browser-resident controller
class ShinyreactOutput {
  constructor(private id: string) {}

  async expectValue(expected: string, timeout = 5000): Promise<void> {
    const el = document.getElementById(this.id);
    await pollUntil(() => el?.textContent === expected, timeout);
  }
}
```

**What's straightforward (~80%):**
- Poll-until-condition-or-timeout — well-understood pattern, used by `@testing-library/dom`'s `waitFor`
- DOM queries — `querySelector`, `textContent`, `getAttribute` are reliable
- Basic visibility — `getBoundingClientRect()`, `getComputedStyle('display')`, `offsetParent`
- `MutationObserver` — reactive DOM change detection

**What's risky (~20% of work, ~80% of bugs):**
- **Timing/race conditions** — Playwright has years of engineering around React re-renders, concurrent mode, and animation frames. A custom implementation will miss edge cases, leading to flaky tests.
- **Actionability gaps** — Playwright checks whether an element is stable, receiving pointer events, and not covered by overlays. These checks are non-trivial to replicate correctly.
- **Error messages** — Playwright shows rich diffs (expected vs actual) with context. Building comparable diagnostics is significant work.

**Mitigating factors:**
- Bounded scope — we're testing our own components, not arbitrary pages
- React is predictable — JSON-rendered components produce consistent DOM
- Precedent exists — `@testing-library/dom` implements `waitFor`/assertion patterns in-browser successfully
- Can start simple and harden incrementally

**Pros:**
- True "self-testing browser" — no external process needed for assertions
- Python/R integration is trivial — just `page.evaluate()` calls
- No Node.js dependency for test execution (only for building the assertion library)
- Lightweight — no RPC, no subprocess, no code generation

**Cons:**
- **Reimplements Playwright's expect** — duplicates battle-tested assertion logic with years of edge-case fixes
- **Flaky test risk** — the #1 pain point in browser testing, and we'd be using a less mature assertion engine
- **No actionability checks** — or we implement our own, which is a significant undertaking
- **Maintenance burden** — we own the assertion library forever; Playwright's improvements don't flow to us
- **Divergent behavior** — our browser-native assertions will behave differently from Playwright's expect in subtle ways, making it harder to reason about test failures

**Verdict:** Moderate risk, feasible for shinyreact's bounded scope. However, it sacrifices the robustness of Playwright's expect for architectural convenience. The flaky-test risk is the primary concern.

### Approach 4: Code Generation from TypeScript to Python/R (Recommended)

**Description:** Controllers are defined in TypeScript as the single source of truth. A code generation step produces native Python and R controller classes that use each language's own Playwright bindings (`playwright` for Python, an R equivalent) with the same CSS selectors and assertion patterns. The generated controllers call `playwright_expect(locator)` directly — real Playwright expect, real actionability checks, real auto-retry.

**Example TypeScript source (source of truth):**
```typescript
// controllers/shinyreact-output.ts
import { Page, Locator, expect } from '@playwright/test';

export class ShinyreactOutput {
  readonly loc: Locator;

  constructor(readonly page: Page, readonly id: string) {
    this.loc = page.locator(`#${id}.shinyreact-output`);
  }

  async expectSpec(value: Record<string, unknown>, timeout?: number) {
    // Assert the rendered output matches the expected spec
    await expect(this.loc).toContainText(JSON.stringify(value), { timeout });
  }

  async expectVisible(timeout?: number) {
    await expect(this.loc).toBeVisible({ timeout });
  }

  async expectHidden(timeout?: number) {
    await expect(this.loc).toBeHidden({ timeout });
  }
}
```

**Generated Python controller:**
```python
# shinyreact/playwright/controllers/_shinyreact_output.py  (generated)
from playwright.sync_api import Page, Locator, expect

class ShinyreactOutput:
    def __init__(self, page: Page, id: str):
        self.page = page
        self.id = id
        self.loc: Locator = page.locator(f"#{id}.shinyreact-output")

    def expect_spec(self, value: dict, *, timeout: float | None = None):
        expect(self.loc).to_contain_text(json.dumps(value), timeout=timeout)

    def expect_visible(self, *, timeout: float | None = None):
        expect(self.loc).to_be_visible(timeout=timeout)

    def expect_hidden(self, *, timeout: float | None = None):
        expect(self.loc).to_be_hidden(timeout=timeout)
```

**Generated R controller (future):**
```r
# shinyreact/R/playwright-controllers.R  (generated)
ShinyreactOutput <- R6::R6Class("ShinyreactOutput",
  public = list(
    initialize = function(page, id) {
      self$page <- page
      self$id <- id
      self$loc <- page$locator(sprintf("#%s.shinyreact-output", id))
    },
    expect_spec = function(value, timeout = NULL) {
      self$loc$expect()$to_contain_text(jsonlite::toJSON(value), timeout = timeout)
    },
    expect_visible = function(timeout = NULL) {
      self$loc$expect()$to_be_visible(timeout = timeout)
    }
  )
)
```

## Why Code Generation Is the Best Approach

### It uses real Playwright in every language

Each generated controller calls the native Playwright bindings for its language. Python uses `playwright.sync_api.expect`, R would use its Playwright equivalent. There is no reimplementation of expect, no custom polling, no browser-native assertion workaround. Every test gets Playwright's full auto-retry, actionability checks, rich error messages, and timeout handling — the same battle-tested behavior that the broader Playwright ecosystem relies on.

This is the fundamental advantage over Approach 3 (browser-native). We don't sacrifice assertion quality for architectural convenience.

### Single source of truth without process coordination

Unlike Approaches 1 and 2, there is no Node.js process running alongside Python/R during test execution. The code generation happens at build time (or as a dev workflow step), not at runtime. During test execution, it's a single process: Python running pytest with Playwright, or R running testthat with its Playwright bindings.

This eliminates the browser ownership conflicts, RPC serialization, subprocess coordination, and cross-process error propagation that make Approaches 1 and 2 fragile.

### Full integration with each language's test ecosystem

Generated Python controllers integrate natively with pytest, pytest fixtures, `shiny.testing.AppFixture`, and the existing `shiny.playwright.controllers` pattern. Generated R controllers will integrate with testthat and shinytest2. Tests can freely interleave server-side assertions with browser assertions in the same test function — something Approach 2 (shell out) cannot do.

### TypeScript remains the authoritative definition

The controller logic (selectors, method signatures, assertion types) is defined once in TypeScript. When a selector changes or a new assertion is added, the change is made in one place and propagated to Python and R via code generation. This prevents drift between languages — a real risk with manual maintenance (Approach "write controllers separately in each language").

### The TS controllers are independently testable

The TypeScript controllers are real Playwright test code, not just schema definitions. They can be run directly via `npx playwright test` for JS-only testing scenarios (e.g., testing the JS bundle in isolation without a Python/R server, or for downstream JS-only packages). This makes the TS code both the source of truth AND a functional test suite.

### Incremental adoption

Code generation can start simple — even hand-maintained Python/R controllers that follow the TS structure, with automated generation added later. The architecture doesn't require a perfect code-gen pipeline on day one. The key is establishing the convention that TS controllers are authoritative and Python/R controllers mirror them.

### Downstream extensibility

When downstream packages like `shinyshadcn` define their own controllers in TypeScript, they can use the same code-gen pipeline to produce Python/R controller classes. The pattern scales to the ecosystem, not just shinyreact.

## Open Questions (Deferred)

The following questions were explored but not resolved during this brainstorming session. They should be addressed before implementation:

### Code generation mechanism

Three sub-options were considered:

1. **Schema-driven:** Define controllers in a JSON/YAML schema. Both TS and Python/R controllers are generated from the schema. Pro: language-agnostic source of truth. Con: the schema becomes a DSL that must express selectors, method signatures, assertion types, and Playwright API mappings — essentially reimplementing TypeScript's type system in YAML.

2. **TS-as-source with AST parsing:** Write real TS controller classes. A codegen script uses the TypeScript compiler API to parse the AST, extract class definitions, method signatures, and Playwright API calls, then generates equivalent Python/R code. Pro: TS is real, runnable code. Con: the codegen script must understand Playwright's API mapping between languages (e.g., `toContainText` in TS -> `to_contain_text` in Python).

3. **Manual with conventions:** Write TS controllers and manually write Python/R controllers following strict naming conventions. No automated codegen. Pro: zero tooling overhead. Con: drift risk grows with the number of controllers.

None of these felt right during the brainstorming session. The tension is between wanting a truly automated single-source-of-truth pipeline and the complexity of cross-language Playwright API translation. This is the primary design problem to solve before implementation.

### Playwright API mapping

Playwright's TypeScript and Python APIs use different naming conventions:
- TS: `toContainText()`, `toBeVisible()`, `toHaveAttribute()`
- Python: `to_contain_text()`, `to_be_visible()`, `to_have_attribute()`

A code-gen approach needs a reliable mapping between these. The mapping is mechanical (camelCase to snake_case) but must also handle parameter differences, return type differences, and any API surface gaps between the two Playwright implementations.

### R Playwright bindings

No mature R Playwright binding exists today. The R story depends on what becomes available (e.g., `chromote` provides CDP access but not Playwright's high-level API). This may require R controllers to use a different assertion strategy or wait for ecosystem maturity.

### Test app fixtures

How should test apps be defined and started? Options include:
- Inline Shiny app definitions in test files (like `shiny.testing` does today)
- Separate app directories with `app.py` / `app.R` files
- Shared fixture apps in the repo that both TS and Python/R tests use

## Summary Table

| Criterion | Node.js Bridge | Shell Out | Browser-Native | Code-Gen (Recommended) |
|---|---|---|---|---|
| Real Playwright expect | Yes | Yes | No (reimplemented) | Yes |
| Actionability checks | Yes | Yes | Partial | Yes |
| Single source of truth | Yes (TS) | Yes (TS) | Yes (TS) | Yes (TS) |
| Single process at runtime | No (2 processes) | No (subprocess) | Yes | Yes |
| pytest/testthat integration | Poor (RPC) | Poor (subprocess) | Good | Native |
| Interleave server + browser assertions | Possible but complex | No | Yes | Yes |
| Node.js required at runtime | Yes | Yes | No | No |
| Flaky test risk | Low | Low | Medium-High | Low |
| Implementation complexity | High | Low | Medium | Medium |
| Maintenance burden | High (RPC layer) | Low | High (assertion lib) | Medium (codegen) |
| Debugging experience | Poor (cross-process) | Poor (subprocess) | Good | Good |
