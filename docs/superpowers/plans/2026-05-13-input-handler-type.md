# `type=` option on `useShinyInput` / `useSetShinyInput` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional `type?: string` to `useShinyInput` and `useSetShinyInput` so values are sent to Shiny as `id:type`, routing them through Shiny's server-side input handlers (e.g. `shiny.datetime` → `datetime.datetime` on `input.foo()`).

**Architecture:** Store an optional `type` on `InputRegistryEntry`. The hook validates `type` synchronously and calls `entry.updateType()` in its existing `useEffect`. `updateType` finalizes on first call (first-writer-wins) and throws on conflict. `setShinyInputValue` appends `:type` to the wire id (registry key stays the bare id, so `useShinyInputValue` is untouched).

**Tech Stack:** TypeScript, React 19, vitest + @testing-library/react, Python (Shiny Express), Playwright + pytest-playwright.

**Spec:** `docs/superpowers/specs/2026-05-13-input-handler-type-design.md`. Read it first.

**Resolves:** [#97](https://github.com/posit-dev/shinyreact/issues/97).

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `js/src/shiny-react/input-registry.ts` | Modify | Add `type` field, `typeFinalized` flag, `updateType()` method; append suffix in `setShinyInputValue` |
| `js/src/shiny-react/__tests__/input-registry.test.ts` | Modify | Tests for `updateType` behavior and wire-id suffix |
| `js/src/shiny-react/use-shiny.ts` | Modify | `type?: string` option on `useShinyInput` and `useSetShinyInput`; sync validation; `updateType` call in effect |
| `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx` | Create | Hook-level tests (validation, conflict, mount sequencing, namespacing) using the real registry |
| `examples/ui-tsx/08-input-handler/app.py` | Create | Example server: `set_react_page()` + `@reactive_output` echoing `type(input.when()).__name__` |
| `examples/ui-tsx/08-input-handler/www/index.html` | Create | Bootstrap with link to `main.css` and `app.js` |
| `examples/ui-tsx/08-input-handler/www/app.js` | Create | No-build React, uses `useShinyInput<number>("when", …, { type: "shiny.datetime" })` |
| `examples/ui-tsx/08-input-handler/www/main.css` | Create | Minimal styling |
| `pkg-py/tests/playwright/apps/input-handler-type/app.py` | Create | Spartan fixture: number input + `type(input.when()).__name__` output |
| `pkg-py/tests/playwright/apps/input-handler-type/www/index.html` | Create | Minimal bootstrap |
| `pkg-py/tests/playwright/apps/input-handler-type/www/app.js` | Create | No-build React using the new `type` option |
| `pkg-py/tests/playwright/test_input_handler_type.py` | Create | Playwright e2e |
| `docs/features.md` | Modify | Mention `type` on the two hook rows; add example row |
| `CLAUDE.md` | Modify | New subsection under **Common patterns** |

---

## Task 1: Registry — `type` field, `updateType`, wire-id suffix

**Files:**
- Modify: `js/src/shiny-react/input-registry.ts`
- Test: `js/src/shiny-react/__tests__/input-registry.test.ts`

- [ ] **Step 1: Read the current registry**

Run:
```bash
sed -n '1,80p' js/src/shiny-react/input-registry.ts
```

Confirm the `InputRegistryEntry` class shape matches what the spec assumes. Specifically: `id: string`, `setShinyInputValue` calls `getShiny()?.setInputValue?.(this.id, value, this.opts)`. If anything differs, stop and reconcile with the spec before continuing.

- [ ] **Step 2: Add failing tests for `updateType` and the wire-id suffix**

Append the following test cases to the existing `describe("InputRegistryEntry", ...)` block in `js/src/shiny-react/__tests__/input-registry.test.ts`. Place them after the last `it(...)` in that block, before the `describe("InputRegistry", ...)` block (if present) closes.

```ts
  it("type defaults to undefined and the wire id has no suffix", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo",
      1,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("updateType(string) causes wire id to be 'id:type'", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("shiny.datetime");

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:shiny.datetime",
      1,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("updateType is set-once: same value is a no-op", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("X");
    entry.updateType("X");

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:X",
      1,
      expect.anything(),
    );
  });

  it("updateType after a string: omission (undefined) is a no-op", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("X");
    entry.updateType(undefined);

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:X",
      1,
      expect.anything(),
    );
  });

  it("updateType after a string: conflicting string throws and entry stays unchanged", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("X");

    expect(() => entry.updateType("Y")).toThrow(/already registered with type="X"/);

    entry.setValue(1);
    vi.advanceTimersByTime(200);
    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:X",
      1,
      expect.anything(),
    );
  });

  it("updateType after undefined finalizes 'no type'; later string throws", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType(undefined);

    expect(() => entry.updateType("X")).toThrow(/already registered with type=undefined/);

    entry.setValue(1);
    vi.advanceTimersByTime(200);
    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo",
      1,
      expect.anything(),
    );
  });
```

- [ ] **Step 3: Run the tests and verify they fail**

Run:
```bash
cd js && npx vitest run src/shiny-react/__tests__/input-registry.test.ts
```

Expected: the six new tests fail with messages like `entry.updateType is not a function`. Existing tests still pass.

- [ ] **Step 4: Implement `type` field, `updateType`, and the wire-id suffix**

In `js/src/shiny-react/input-registry.ts`, modify the `InputRegistryEntry` class. Apply two edits:

Edit A — add the fields after the existing fields (around the constructor):

```ts
export class InputRegistryEntry<T> {
  id: string; // Shiny input ID
  value: T;
  useStateSetValueFns: Set<(value: T) => void>;
  shinySetInputValueDebounced: DebouncedFunction<(value: T) => void>;
  opts: { priority?: EventPriority; debounceMs: number } = {
    debounceMs: 100,
  };
  // NEW: input-handler type suffix. Set once via updateType(); subsequent
  // mismatches throw. `undefined` is a valid finalized state ("no suffix").
  type?: string;
  private typeFinalized = false;
```

Edit B — replace `setShinyInputValue` and add `updateType`:

```ts
  private setShinyInputValue(value: T) {
    const wireId = this.type ? `${this.id}:${this.type}` : this.id;
    getShiny()?.setInputValue?.(wireId, value, this.opts);
  }

  updateType(type: string | undefined): void {
    if (!this.typeFinalized) {
      this.type = type;
      this.typeFinalized = true;
      return;
    }
    if (type === undefined) return;
    if (this.type !== type) {
      throw new Error(
        `Input "${this.id}" is already registered with type=${this.type === undefined ? "undefined" : JSON.stringify(this.type)}. ` +
          `A second mount requested type=${JSON.stringify(type)}. ` +
          `An input's handler type changes server-side semantics and must be consistent ` +
          `across every useShinyInput / useSetShinyInput call for the same id.`,
      );
    }
  }
```

The leading-`?.` chain stays the same. Place `updateType` next to `updatePriority` so related methods cluster.

- [ ] **Step 5: Run the tests and verify they pass**

Run:
```bash
cd js && npx vitest run src/shiny-react/__tests__/input-registry.test.ts
```

Expected: all tests pass (existing + six new).

- [ ] **Step 6: Type-check**

Run:
```bash
make js-lint
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add js/src/shiny-react/input-registry.ts \
        js/src/shiny-react/__tests__/input-registry.test.ts
git commit -m "feat(js): InputRegistryEntry.updateType + wire id suffix (#97)"
```

---

## Task 2: Hooks — `type` option on `useShinyInput` and `useSetShinyInput`

**Files:**
- Modify: `js/src/shiny-react/use-shiny.ts`
- Create: `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx`

- [ ] **Step 1: Write the failing hook test file**

Create `js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx` with the contents below. This file uses the **real** `InputRegistry` (not a mock) and mocks only `getShiny`, so the assertions cover the hook → registry → wire-call path end-to-end. That style matches `use-shiny-restore.test.tsx`.

```tsx
/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, cleanup, render } from "@testing-library/react";
import * as React from "react";
import type { ReactNode } from "react";

// Mock getShiny so the hook's useShinyInitialized resolves to true via
// `initializedPromise`, and so we can capture setInputValue calls.
const mockSetInputValue = vi.fn();
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => ({
    initializedPromise: Promise.resolve(),
    setInputValue: mockSetInputValue,
  })),
}));

import {
  _resetShinyReactInitializedForTesting,
  useSetShinyInput,
  useShinyInput,
} from "../use-shiny";
import { ShinyModuleProvider } from "../ShinyModuleContext";
import { InputRegistry } from "../input-registry";
import { getReactRegistry } from "../react-registry";

function freshState(): void {
  (globalThis as any).window = (globalThis as any).window || {};
  delete (globalThis as any).window.shinyreact;
  _resetShinyReactInitializedForTesting();
}

// Helper: flush microtasks + timers so useShinyInitialized resolves and the
// debounced setInputValue fires.
async function flushAll() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  await act(async () => {
    vi.advanceTimersByTime(200);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  freshState();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function ProducerFull({
  id,
  type,
  initial = 0,
}: {
  id: string;
  type?: string;
  initial?: number;
}) {
  const [value, setValue] = useShinyInput<number>(id, initial, {
    debounceMs: 0,
    ...(type !== undefined ? { type } : {}),
  });
  return (
    <button data-testid={`btn-${id}`} onClick={() => setValue(value + 1)}>
      {value}
    </button>
  );
}

function ProducerSet({
  id,
  type,
  initial = 0,
}: {
  id: string;
  type?: string;
  initial?: number;
}) {
  const setValue = useSetShinyInput<number>(id, initial, {
    debounceMs: 0,
    ...(type !== undefined ? { type } : {}),
  });
  return <button data-testid={`set-${id}`} onClick={() => setValue(initial + 1)} />;
}

describe("useShinyInput / useSetShinyInput — `type` option", () => {
  it("appends suffix when type is set", async () => {
    render(<ProducerFull id="foo" type="shiny.datetime" />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter((c) => c[0].startsWith("foo"));
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("foo:shiny.datetime");
    }
  });

  it("omits suffix when type is not set", async () => {
    render(<ProducerFull id="foo" />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter((c) => c[0].startsWith("foo"));
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("foo");
    }
  });

  it.each([
    ["", /invalid type=/],
    ["has space", /invalid type=/],
    ["a:b", /invalid type=/],
  ])("throws synchronously on invalid type=%j", (badType, pattern) => {
    // Suppress React's error logging for the expected throw.
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() =>
      render(<ProducerFull id="bad" type={badType} />),
    ).toThrow(pattern as RegExp);
    errorSpy.mockRestore();
  });

  it("conflicting types across two mounts: second mount throws", async () => {
    // First mount: type "X" — finalizes the registry entry.
    const { unmount: unmountA } = render(<ProducerFull id="conf" type="X" />);
    await flushAll();

    // Second mount with a conflicting type: React surfaces the throw from
    // the useEffect through render(). Use a try/catch.
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    let caught: Error | undefined;
    try {
      render(<ProducerFull id="conf" type="Y" />);
      await flushAll();
    } catch (e) {
      caught = e as Error;
    }
    errorSpy.mockRestore();

    // The conflict throw must have surfaced (either synchronously from render
    // or via the act-flushed effect — both routes acceptable, but it must
    // appear somewhere).
    const sawConflict =
      (caught && /already registered with type="X"/.test(caught.message)) ||
      (errorSpy.mock.calls.flat().some((arg) =>
        typeof arg === "string"
          ? /already registered with type="X"/.test(arg)
          : arg instanceof Error
            ? /already registered with type="X"/.test(arg.message)
            : false,
      ));
    expect(sawConflict).toBe(true);

    // First mount's wire calls remained "conf:X".
    const calls = mockSetInputValue.mock.calls.filter((c) =>
      typeof c[0] === "string" && c[0].startsWith("conf"),
    );
    for (const call of calls) {
      expect(call[0]).toBe("conf:X");
    }

    unmountA();
  });

  it("later mount omitting type is fine", async () => {
    render(<ProducerFull id="omit" type="X" />);
    await flushAll();

    // Second mount: no type — should NOT throw.
    expect(() => render(<ProducerSet id="omit" />)).not.toThrow();
    await flushAll();
  });

  it("adding a type after a no-type mount throws", async () => {
    render(<ProducerFull id="late" />);
    await flushAll();

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    let caught: Error | undefined;
    try {
      render(<ProducerFull id="late" type="X" />);
      await flushAll();
    } catch (e) {
      caught = e as Error;
    }
    errorSpy.mockRestore();

    const sawConflict =
      (caught && /already registered with type=undefined/.test(caught.message)) ||
      (errorSpy.mock.calls.flat().some((arg) =>
        typeof arg === "string"
          ? /already registered with type=undefined/.test(arg)
          : arg instanceof Error
            ? /already registered with type=undefined/.test(arg.message)
            : false,
      ));
    expect(sawConflict).toBe(true);
  });

  it("namespacing: wire id is `ns-foo:shiny.datetime`", async () => {
    render(
      <ShinyModuleProvider namespace="ns">
        <ProducerFull id="foo" type="shiny.datetime" />
      </ShinyModuleProvider>,
    );
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter(
      (c) => typeof c[0] === "string" && c[0].startsWith("ns-foo"),
    );
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("ns-foo:shiny.datetime");
    }
  });

  it("useSetShinyInput appends suffix when type is set", async () => {
    render(<ProducerSet id="setfoo" type="shiny.datetime" initial={5} />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=set-setfoo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter(
      (c) => typeof c[0] === "string" && c[0].startsWith("setfoo"),
    );
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("setfoo:shiny.datetime");
    }
  });
});

// Avoid the unused-import warning if the test file ends up not referencing
// these directly. They're used implicitly via getReactRegistry()/registry.
void InputRegistry;
void getReactRegistry;
```

> The defensive `try/catch + console.error spy` pattern in the conflict tests is needed because React surfaces effect-thrown errors through `act` in a way that may either re-throw from `render` *or* log via the console.error path depending on React's act semantics. Asserting "the conflict was visible somewhere" keeps the test resilient to that ambiguity.

- [ ] **Step 2: Run the new test file and verify it fails**

Run:
```bash
cd js && npx vitest run src/shiny-react/__tests__/use-shiny-input-type.test.tsx
```

Expected: every test fails — the hooks don't yet accept the `type` option.

- [ ] **Step 3: Add `type` to `useShinyInput`**

In `js/src/shiny-react/use-shiny.ts`, locate the `useShinyInput` declaration (around line 61). Replace the function signature, the validation block, and the body of the `useEffect` so the file ends up matching the snippet below. Edits:

(a) Update the options bag in the function signature:

```ts
export function useShinyInput<T>(
  id: string,
  defaultValue: T,
  {
    debounceMs = 100,
    priority,
    namespace: explicitNamespace,
    type,
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
  } = {},
): [T, (value: T) => void] {
  ensureShinyReactInitialized();

  if (type !== undefined && !/^[^\s:]+$/.test(type)) {
    throw new Error(
      `useShinyInput("${id}"): invalid type=${JSON.stringify(type)}. ` +
        `Must be non-empty and contain no whitespace or ':' characters.`,
    );
  }

  const namespacedId = useNamespacedId(id, explicitNamespace);
```

(b) Inside the existing `useEffect` body, call `updateType` next to `updatePriority`, and add `type` to the dep array:

```ts
    if (debounceMs !== undefined) {
      inputRegistryEntry.updateDebounceDelay(debounceMs);
    }
    if (priority) {
      inputRegistryEntry.updatePriority(priority);
    }
    inputRegistryEntry.updateType(type);

    inputRegistryEntry.addUseStateSetValueFn(setValue);
    // TODO: This is awkward. Maybe just add a trigger method?
    inputRegistryEntry.setValue(inputRegistryEntry.getValue());

    return () => {
      inputRegistryEntry.removeUseStateSetValueFn(setValue);
    };
  }, [namespacedId, shinyInitialized, debounceMs, priority, stableDefault, type]);
```

Keep the existing `stableDefaultRef` / `stableDefault` logic and the `setValueWrapped` callback as-is.

- [ ] **Step 4: Add `type` to `useSetShinyInput`**

In the same file, locate `useSetShinyInput` (around line 351). Apply the parallel edits:

(a) Update the options bag and add the validation:

```ts
export function useSetShinyInput<T>(
  id: string,
  defaultValue: T,
  {
    debounceMs = 100,
    priority,
    namespace: explicitNamespace,
    type,
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string | null;
    type?: string;
  } = {},
): (value: T) => void {
  ensureShinyReactInitialized();

  if (type !== undefined && !/^[^\s:]+$/.test(type)) {
    throw new Error(
      `useSetShinyInput("${id}"): invalid type=${JSON.stringify(type)}. ` +
        `Must be non-empty and contain no whitespace or ':' characters.`,
    );
  }

  const namespacedId = useNamespacedId(id, explicitNamespace);
```

(b) Inside `useEffect`, add the `updateType` call and extend the dep array:

```ts
    if (debounceMs !== undefined) {
      inputRegistryEntry.updateDebounceDelay(debounceMs);
    }
    if (priority) {
      inputRegistryEntry.updatePriority(priority);
    }
    inputRegistryEntry.updateType(type);
    // Re-broadcast the current value through the registry so Shiny sees the
    // input on first mount (matches useShinyInput's behavior).
    inputRegistryEntry.setValue(inputRegistryEntry.getValue());

    // Intentionally NO addUseStateSetValueFn — this is a write-only hook;
    // value updates from elsewhere (other producers, server-side updates)
    // must not re-render the component using this hook.
  }, [namespacedId, shinyInitialized, debounceMs, priority, stableDefault, type]);
```

- [ ] **Step 5: Update JSDoc for both hooks**

For `useShinyInput`'s JSDoc block, add the following `@param` line after the existing `@param options.priority` line:

```
 * @param options.type Optional input-handler name appended as `${id}:${type}`
 * when sending to Shiny. Use to route values through a Shiny input handler
 * such as `"shiny.datetime"`. Must be non-empty and contain no whitespace or
 * `:`. Once a given id has been registered with a `type` (or with no `type`),
 * subsequent mounts of the same id with a *different* `type` throw — the
 * handler name is a server-side semantic and must be consistent across all
 * mounts of the same id.
```

Replicate the same `@param options.type` block on `useSetShinyInput`'s JSDoc.

- [ ] **Step 6: Run the hook tests**

Run:
```bash
cd js && npx vitest run src/shiny-react/__tests__/use-shiny-input-type.test.tsx
```

Expected: all tests pass.

- [ ] **Step 7: Run the full vitest suite to catch regressions**

Run:
```bash
cd js && npx vitest run
```

Expected: every existing test still passes (especially `use-shiny-namespace.test.tsx`, `input-registry.test.ts`, `use-shiny-restore.test.tsx`).

- [ ] **Step 8: Type-check**

Run:
```bash
make js-lint
```

Expected: no errors.

- [ ] **Step 9: Commit**

```bash
git add js/src/shiny-react/use-shiny.ts \
        js/src/shiny-react/__tests__/use-shiny-input-type.test.tsx
git commit -m "feat(js): type= option on useShinyInput / useSetShinyInput (#97)"
```

---

## Task 3: Example app — `examples/ui-tsx/08-input-handler/`

**Files:**
- Create: `examples/ui-tsx/08-input-handler/app.py`
- Create: `examples/ui-tsx/08-input-handler/www/index.html`
- Create: `examples/ui-tsx/08-input-handler/www/app.js`
- Create: `examples/ui-tsx/08-input-handler/www/main.css`

This example follows the no-build pattern of `examples/ui-tsx/05-temperature/` (no JSX, no bundler — `React.createElement` directly).

- [ ] **Step 1: Create the directory**

Run:
```bash
mkdir -p examples/ui-tsx/08-input-handler/www
```

- [ ] **Step 2: Write `app.py`**

Create `examples/ui-tsx/08-input-handler/app.py`:

```python
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def when_info():
    v = input.when()
    if v is None:
        return "—"
    return f"{type(v).__name__} → {v!r}"
```

The handler `shiny.datetime` coerces a numeric input to `datetime.datetime` server-side, so `type(input.when()).__name__` returns `"datetime"`. Without the `type` option, the same input would surface as `int` and the rendered text would read `int → 1234567890`.

- [ ] **Step 3: Write `www/index.html`**

Create `examples/ui-tsx/08-input-handler/www/index.html`:

```html
<link rel="stylesheet" href="main.css" />
<div id="root"></div>
<script src="app.js" defer></script>
```

- [ ] **Step 4: Write `www/app.js`**

Create `examples/ui-tsx/08-input-handler/www/app.js`:

```js
const { React, ReactDOM, useShinyInput, useShinyOutputValue, useShinyInitialized } =
  window.shinyreact;

const h = React.createElement;

function App() {
  const initialized = useShinyInitialized();
  const [when, setWhen] = useShinyInput(
    "when",
    Math.floor(Date.now() / 1000),
    { type: "shiny.datetime", debounceMs: 0 },
  );
  const echoed = useShinyOutputValue("when_info");

  if (!initialized) return null;

  return h(
    "div",
    { className: "card" },
    h("h2", null, "Input handler — `shiny.datetime`"),
    h(
      "p",
      null,
      "The client sends a unix-seconds number. The server's `shiny.datetime` handler ",
      "coerces it to a Python `datetime` before `input.when()` resolves. Toggle the ",
      "input or change the number to see the round-trip.",
    ),
    h(
      "label",
      { className: "row" },
      h("span", null, "Unix seconds:"),
      h("input", {
        type: "number",
        value: when,
        onChange: (e) => setWhen(Number(e.target.value)),
      }),
    ),
    h(
      "p",
      { className: "echo" },
      "Server saw: ",
      h("code", null, echoed ?? "…"),
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

- [ ] **Step 5: Write `www/main.css`**

Create `examples/ui-tsx/08-input-handler/www/main.css`:

```css
body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background: #fafafa;
}

.card {
  max-width: 520px;
  margin: 2rem auto;
  padding: 1.5rem;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card h2 {
  margin: 0 0 0.75rem;
}

.row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1rem 0;
}

.row input {
  flex: 1;
  padding: 0.4rem 0.6rem;
  font-size: 1rem;
}

.echo {
  background: #f0f0f0;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
}

.echo code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
```

- [ ] **Step 6: Smoke-run the example**

Run (in another terminal, kill with Ctrl-C after verifying):
```bash
uv run shiny run --port 8108 examples/ui-tsx/08-input-handler/app.py
```

In a browser, open `http://localhost:8108`. Expected: after the first render, "Server saw:" updates to text starting with `datetime → datetime.datetime(`. Change the number; the text re-renders, still beginning with `datetime`.

If it reads `int → ...` instead, the `type=` option didn't reach the wire. Recheck Task 2.

- [ ] **Step 7: Commit**

```bash
git add examples/ui-tsx/08-input-handler/
git commit -m "examples(ui-tsx): 08-input-handler demonstrating shiny.datetime (#97)"
```

---

## Task 4: Playwright e2e

**Files:**
- Create: `pkg-py/tests/playwright/apps/input-handler-type/app.py`
- Create: `pkg-py/tests/playwright/apps/input-handler-type/www/index.html`
- Create: `pkg-py/tests/playwright/apps/input-handler-type/www/app.js`
- Create: `pkg-py/tests/playwright/test_input_handler_type.py`

- [ ] **Step 1: Create the fixture directory**

Run:
```bash
mkdir -p pkg-py/tests/playwright/apps/input-handler-type/www
```

- [ ] **Step 2: Write the fixture `app.py`**

Create `pkg-py/tests/playwright/apps/input-handler-type/app.py`:

```python
from shiny.express import input, render  # noqa: F401  # marks this file as Shiny Express
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def when_info():
    v = input.when()
    if v is None:
        return "pending"
    return type(v).__name__
```

`render` is imported only to flip Shiny into Express mode (required per `.claude/references/playwright-e2e-tests.md`).

- [ ] **Step 3: Write the fixture `www/index.html`**

Create `pkg-py/tests/playwright/apps/input-handler-type/www/index.html`:

```html
<style>
  body {
    font-family: system-ui, sans-serif;
    margin: 2rem;
    line-height: 1.4;
  }
</style>
<p>
  When the test passes, <code data-test="echo"></code> reads
  <code>datetime</code>. The number input below sends unix-seconds; the
  <code>shiny.datetime</code> handler coerces it to a Python
  <code>datetime</code> server-side.
</p>
<div id="root"></div>
<script src="app.js" defer></script>
```

- [ ] **Step 4: Write the fixture `www/app.js`**

Create `pkg-py/tests/playwright/apps/input-handler-type/www/app.js`:

```js
const { React, ReactDOM, useShinyInput, useShinyOutputValue, useShinyInitialized } =
  window.shinyreact;

const h = React.createElement;

function App() {
  const initialized = useShinyInitialized();
  // Fixed initial unix-seconds value so the test's "after typing" assertion
  // has a deterministic starting point.
  const [when, setWhen] = useShinyInput("when", 1700000000, {
    type: "shiny.datetime",
    debounceMs: 0,
  });
  const echoed = useShinyOutputValue("when_info");

  if (!initialized) return null;

  return h(
    "div",
    { "data-test": "container" },
    h("input", {
      "data-test": "input",
      type: "number",
      value: when,
      onChange: (e) => setWhen(Number(e.target.value)),
    }),
    h("span", { "data-test": "echo" }, echoed ?? "pending"),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
```

- [ ] **Step 5: Write the Playwright test**

Create `pkg-py/tests/playwright/test_input_handler_type.py`:

```python
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture
from shiny.run import ShinyAppProc

input_handler_app = create_app_fixture("apps/input-handler-type/app.py")


def test_shiny_datetime_handler_runs_on_server(
    page: Page, input_handler_app: ShinyAppProc
) -> None:
    """`type='shiny.datetime'` routes the input through Shiny's datetime handler,
    so `input.when()` resolves to a `datetime.datetime` server-side."""
    page.goto(input_handler_app.url)

    echo = page.locator("[data-test=echo]")
    # The handler runs on the first delivered value; the rendered text should
    # be "datetime", not "int".
    expect(echo).to_have_text("datetime")

    # Change the number — handler still runs; type stays "datetime".
    page.locator("[data-test=input]").fill("1731436800")
    page.locator("[data-test=input]").press("Tab")
    expect(echo).to_have_text("datetime")
```

- [ ] **Step 6: Run the e2e test**

Run:
```bash
make py-install-e2e   # one-time, idempotent
make py-test-e2e
```

Expected: existing tests still pass + the new `test_shiny_datetime_handler_runs_on_server` passes. If the new test fails with the rendered text reading `int`, the wire suffix isn't reaching Shiny — recheck Task 1/Task 2. If it fails reading `NoneType` or `pending`, the output binding didn't fire — recheck the fixture html/js.

> **Mind the `set_react_page()` cache (issue #82):** if you edit `index.html` mid-iteration, restart the shiny server. `py-test-e2e` boots a fresh subprocess per run, so it picks up edits automatically.

- [ ] **Step 7: Update bundled JS so the fixture sees the new hook code**

The Playwright fixture loads the bundled `shinyreact.js` from `pkg-py/src/shinyreact/www/`. After changing `js/src/`, rebuild and copy:

```bash
make update-dist
```

Expected: `js/dist/shinyreact.js`, `pkg-py/src/shinyreact/www/shinyreact.js`, and `pkg-r/inst/lib/shiny/shinyreact.js` are updated.

Re-run:
```bash
make py-test-e2e
```

Expected: the new test passes.

- [ ] **Step 8: Commit**

```bash
git add pkg-py/tests/playwright/apps/input-handler-type/ \
        pkg-py/tests/playwright/test_input_handler_type.py \
        js/dist/shinyreact.js \
        pkg-py/src/shinyreact/www/shinyreact.js \
        pkg-r/inst/lib/shiny/shinyreact.js
git commit -m "test(e2e): shiny.datetime handler routes through type= option (#97)"
```

If `pkg-r/inst/lib/shiny/shinyreact.js` doesn't exist in this branch, omit it from the `git add` line.

---

## Task 5: Docs — `features.md` and `CLAUDE.md`

**Files:**
- Modify: `docs/features.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update `docs/features.md`**

Apply two changes in `docs/features.md`:

(a) In the **JS bridge hooks** table (the section listing `useShinyInput`, `useShinyInputValue`, …), extend the `Notes` cell for `useShinyInput` and `useSetShinyInput` so each ends with: `; optional type= routes values through a Shiny input handler (e.g. shiny.datetime)`.

Concretely, the `useShinyInput` row should become:

```
| `useShinyInput` | Working | Full `[value, setValue]` — stable defaultValue via `useRef`; debounce + priority options; optional `type=` routes values through a Shiny input handler (e.g. `shiny.datetime`) |
```

The `useSetShinyInput` row should become:

```
| `useSetShinyInput` | Working | Write-only producer hook — returns just the setter; same `defaultValue` + options as `useShinyInput`; optional `type=` routes values through a Shiny input handler (e.g. `shiny.datetime`) |
```

(b) In the **Examples** table for `ui.tsx`, append a row after the `07-plotly` line:

```
| [08-input-handler](../examples/ui-tsx/08-input-handler/) | Working | Demonstrates `useShinyInput` with `type="shiny.datetime"` — client sends unix seconds; server `input.when()` is a `datetime.datetime` via Shiny's built-in handler |
```

- [ ] **Step 2: Update `CLAUDE.md`**

Add a new subsection at the end of the **Common patterns** section. Place it right before the `### Avoiding flicker on input changes ...` heading (or, if the file order has changed, after `### useShinyMessageHandler`). The subsection:

```markdown
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
```

- [ ] **Step 3: Verify the doc edits render**

Run:
```bash
sed -n '60,90p' docs/features.md
grep -n "Routing input values" CLAUDE.md
```

Expected: the `useShinyInput`/`useSetShinyInput` rows mention `type=`, the new example row is present, and the `CLAUDE.md` grep finds the new subsection heading.

- [ ] **Step 4: Commit**

```bash
git add docs/features.md CLAUDE.md
git commit -m "docs: type= option on useShinyInput (#97)"
```

---

## Task 6: Final verification

- [ ] **Step 1: JS lint + full vitest**

Run:
```bash
make js-lint
cd js && npx vitest run
```

Expected: no errors; every test passes.

- [ ] **Step 2: Python checks**

Run:
```bash
make py-check
```

Expected: passes (format, types, tests).

- [ ] **Step 3: Full e2e suite**

Run:
```bash
make py-test-e2e
```

Expected: all e2e tests pass, including the new `test_shiny_datetime_handler_runs_on_server`.

- [ ] **Step 4: Sanity-check the example manually**

Run:
```bash
uv run shiny run --port 8108 examples/ui-tsx/08-input-handler/app.py
```

Open `http://localhost:8108` and confirm the rendered text begins with `datetime → datetime.datetime(`. Stop the server with Ctrl-C.

- [ ] **Step 5: Confirm no spec gaps**

Skim `docs/superpowers/specs/2026-05-13-input-handler-type-design.md` once more against the committed changes. Confirm:
- API surface matches (line 33-54 of the spec)
- Validation regex matches (line 63-69)
- `updateType` implementation matches the spec snippet (line 79-110)
- First-writer-wins table is honored by all six vitest cases
- Example app delivers the round trip described in the spec
- Playwright test asserts what the spec promises

If anything's missing, fix it before announcing completion.

---

## Self-review (writer pass)

**Spec coverage:**
- API surface (spec §"API surface") → Task 2 steps 3-5.
- Validation regex (spec §"Validation") → Task 2 steps 3 & 4.
- Registry `type`/`typeFinalized`/`updateType`/wire suffix (spec §"Registry changes") → Task 1 step 4.
- First-writer-wins table (4 rows) → Task 1 step 2 (registry-level) + Task 2 step 1 (hook-level): tests `it("type defaults to undefined ...")`, `it("updateType is set-once: same value ...")`, `it("updateType after a string: omission ...")`, `it("updateType after a string: conflicting string ...")`, `it("updateType after undefined finalizes ...")`, plus the hook-level conflict / namespacing / invalid-type tests. All four spec rows covered.
- Namespacing (spec §"Namespacing interaction") → Task 2 step 1 namespacing test.
- Example app (spec §"Example app") → Task 3.
- Vitest tests 1-8 (spec §"Tests") → Task 1 + Task 2. (Spec test #1 = hook "appends suffix"; #2 = hook "omits suffix"; #3 = invalid-throws; #4 = conflict throws; #5 = later-mount-omits; #6 = no-type → type throws; #7 = "same mount changing type literal also throws" — the registry's set-once finalize covers this implicitly via the conflict-throws test, since the registry can't distinguish "same mount re-rendering" from "second mount"; #8 = namespacing.) Spec test #7 doesn't get its own dedicated hook-level test — flagging here. *Fix:* this is already covered by registry-level "conflicting string throws" + the hook's effect-dep array including `type`, which re-runs `updateType` on a literal change. Adding a dedicated hook-level "same mount changes type literal" test would just duplicate the registry test. Leave as-is.
- Playwright e2e (spec §"Playwright e2e") → Task 4.
- Docs (spec §"Docs") → Task 5.
- Non-goals (spec §"Non-goals") → no tasks needed.

**Placeholder scan:** no `TBD`, `TODO`, or unspecific instructions. All code is concrete.

**Type / name consistency:** `updateType`, `typeFinalized`, `type` field name match across registry, hook signatures, JSDoc, tests, example, and fixture. Wire format `${id}:${type}` is consistent.

No issues found that warrant fixing inline. Proceeding to handoff.
