# `ShinyOutput` binding lifecycle error handling

**Date:** 2026-05-08
**Status:** Proposal — pending decision
**Resolves:** #56 (policy question), #60 (implementation)

## Summary

Wrap `Shiny.bindAll`/`Shiny.unbindAll` calls in `ShinyOutput`'s effect with try/catch (sync) and `.catch()` (async) so binding failures are logged with structured context and the component stays mounted. No escape hatch is added in this iteration; a TODO near the log flags a future `onError` callback if a downstream consumer needs telemetry or error-boundary integration.

## Context

`js/src/shiny-output.tsx` is the React → Shiny bridge that mounts an output element and binds it to Shiny's renderer. Today the effect is:

```ts
useEffect(() => {
  const el = ref.current;
  const scope = el?.parentElement;
  if (!el || !scope || !window.Shiny?.bindAll) return;
  void window.Shiny.bindAll(scope);
  return () => {
    window.Shiny?.unbindAll?.(el, true);
  };
}, [id, tagName]);
```

Two latent failure modes:

1. `bindAll` or `unbindAll` throws synchronously → React surfaces the exception, which (without a caller-supplied error boundary) takes down the surrounding tree.
2. `bindAll` returns a rejecting promise → `void`-discarded, surfaces as an unhandled rejection.

Issue #60 asks for try/catch + tests + "consider error boundary integration." Issue #56 asks the underlying policy question: fail-fast vs. graceful degradation, and whether an error boundary is needed.

## Policy decision (resolves #56)

**Graceful degradation, no escape hatch.**

- Both `bindAll` and `unbindAll` failures are logged via `console.error` and swallowed.
- The component remains mounted; sibling `ShinyOutput` instances are unaffected.
- React error boundaries upstream of `<ShinyOutput>` are *not* triggered by binding failures.

Rationale:
- Matches Shiny's renderer ecosystem — a single broken output (e.g. one plot binding failing to load a dependency) does not blank the page.
- Matches surrounding code style: `console.error` is the established logging surface in `js/src/` (see `js/src/shiny-react/use-shiny.ts`).
- Forcing every consumer to wrap every `<ShinyOutput>` in an error boundary is a poor default for a low-level bridge component.

A future `onError?: (err: unknown, phase: "bindAll" | "unbindAll") => void` prop is left as an explicit TODO comment near the log. If a downstream package (e.g. `shinyshadcn`) needs telemetry or error-boundary integration, the prop can be added non-breakingly. Not implemented now — no concrete consumer.

## Implementation (resolves #60)

Single change to `js/src/shiny-output.tsx`. The effect becomes:

```ts
useEffect(() => {
  const el = ref.current;
  const scope = el?.parentElement;
  if (!el || !scope || !window.Shiny?.bindAll) return;

  const logError = (err: unknown, phase: "bindAll" | "unbindAll") => {
    // TODO(future): expose an `onError?: (err, phase) => void` prop so
    // downstream callers can integrate telemetry or React error boundaries.
    console.error(
      `[shinyreact] ShinyOutput "${id}" ${phase} failed:`,
      { id, phase, error: err },
    );
  };

  try {
    const result = window.Shiny.bindAll(scope);
    if (result && typeof (result as Promise<unknown>).catch === "function") {
      (result as Promise<unknown>).catch((err) => logError(err, "bindAll"));
    }
  } catch (err) {
    logError(err, "bindAll");
  }

  return () => {
    try {
      window.Shiny?.unbindAll?.(el, true);
    } catch (err) {
      logError(err, "unbindAll");
    }
  };
}, [id, tagName]);
```

### Notes

- `bindAll`'s return value is treated as "thenable if it has `.catch`." Avoids assuming Shiny's exact Promise type and tolerates synchronous and asynchronous Shiny implementations.
- `logError` is defined inside the effect so it closes over the current `id`. When `id` changes, the effect re-runs and a fresh closure captures the new value.
- The cleanup closure still uses the prior render's `id`, so a failed unbind during re-bind logs with the id that was just removed — the correct id for debugging "what fell off."
- The `void` discard of the original code is replaced; the linter no longer needs to be told to ignore the return.

### Log shape

`console.error` is called with two arguments: a readable prefixed string (greppable, identifying the id and phase) and a structured object (browser devtools pretty-print) carrying the original error so the stack trace is preserved.

```
[shinyreact] ShinyOutput "my_plot" bindAll failed: { id: "my_plot", phase: "bindAll", error: Error }
```

## Tests (`js/src/__tests__/shiny-output.test.tsx`)

Add five cases. All use `vi.spyOn(console, "error")` (silenced via `.mockImplementation(() => {})`) and restore in `afterEach`.

1. **`bindAll` throws synchronously** — `mockBindAll.mockImplementationOnce(() => { throw new Error("boom"); })`. Assert: `console.error` called once with the prefix string matching `bindAll failed` and a structured payload of `{ id, phase: "bindAll", error: <Error> }`. Element still in the DOM.

2. **`bindAll` returns a rejecting promise** — `mockBindAll.mockReturnValueOnce(Promise.reject(new Error("async boom")))`. Await a microtask (`await Promise.resolve()` or `await vi.waitFor(...)`). Assert: `console.error` called with `phase: "bindAll"`. Element still mounted.

3. **`unbindAll` throws on unmount** — `mockUnbindAll.mockImplementationOnce(() => { throw new Error("teardown boom"); })`. Call `unmount()`. Assert: `console.error` called with `phase: "unbindAll"`, no re-throw escapes (the test would fail if it did).

4. **One sibling's `bindAll` failure does not affect others** — render three `<ShinyOutput>` siblings, configure `bindAll` to throw on the second only. Assert: all three elements present, `console.error` called once.

5. **Re-bind after `id` change where the new `bindAll` throws** — render with `id="first"`, then rerender with `id="second"` and `mockBindAll.mockImplementationOnce(() => { throw new Error(...) })` for the second call. Assert: `console.error` payload's `id` is `"second"` (the new id). Element still in the DOM.

## Out of scope

- No `onError` prop, no `throwOnError` prop, no `<ShinyErrorBoundary>` component.
- No changes to `js/src/shiny-react/use-shiny.ts` or other lifecycle modules. Both issues scope to `ShinyOutput`.
- No structured logger abstraction; `console.error` is consistent with the rest of `js/src/`.
- No changes to `bindAll`/`unbindAll` calling conventions (parent-as-scope for bind, `(el, true)` for unbind).

## Files touched

- `js/src/shiny-output.tsx` — error handling in the effect.
- `js/src/__tests__/shiny-output.test.tsx` — five new test cases.

## Verification

- `cd js && npx vitest run src/__tests__/shiny-output.test.tsx` — new tests pass.
- `make js-lint` — type-checks clean.
- `make update-dist` — bundle rebuilt and copied so `pkg-py/src/shinyreact/www/` reflects the change.
