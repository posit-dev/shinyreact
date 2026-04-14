# Output Registry Reference-Counted Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace destructive `OutputRegistry.remove()` with subscriber-level cleanup via dispose functions, fixing the race condition when React unmounts and remounts output components in the same commit.

**Architecture:** `OutputRegistry.add()` returns a dispose function that removes only the specific subscriber callbacks. A private `scheduleCleanup()` method uses `requestAnimationFrame` to defer entry deletion until after React commits, so same-commit remounts re-populate before cleanup fires. The old `remove()` method is deleted entirely.

**Tech Stack:** TypeScript, Vitest, jsdom

---

### File map

| File | Action | Responsibility |
|------|--------|----------------|
| `js/src/shiny-react/output-registry.ts` | Modify | `isEmpty()`, `add()` returns dispose, `scheduleCleanup()`, delete `remove()` |
| `js/src/shiny-react/use-shiny.ts` | Modify | `useShinyOutput` cleanup uses dispose, remove stale TODOs |
| `js/src/shiny-react/__tests__/output-registry.test.ts` | Create | Unit tests for entry and registry |
| `docs/STATUS.md` | Modify | Remove TODO, add Recent fix |

---

### Task 1: Add `isEmpty()` to `OutputRegistryEntry` with tests

**Files:**
- Modify: `js/src/shiny-react/output-registry.ts:11-45`
- Create: `js/src/shiny-react/__tests__/output-registry.test.ts`

- [ ] **Step 1: Write the test file with `isEmpty()` tests**

Create `js/src/shiny-react/__tests__/output-registry.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";

// Mock getShiny — OutputRegistry constructor accesses document.body
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { OutputRegistryEntry } from "../output-registry";

describe("OutputRegistryEntry", () => {
  it("isEmpty returns true on fresh entry", () => {
    const entry = new OutputRegistryEntry("test");
    expect(entry.isEmpty()).toBe(true);
  });

  it("isEmpty returns false after adding setValue subscriber", () => {
    const entry = new OutputRegistryEntry("test");
    entry.addUseStateSetValueFn(vi.fn());
    expect(entry.isEmpty()).toBe(false);
  });

  it("isEmpty returns false after adding setRecalculating subscriber", () => {
    const entry = new OutputRegistryEntry("test");
    entry.addUseStateSetRecalculatingFn(vi.fn());
    expect(entry.isEmpty()).toBe(false);
  });

  it("isEmpty returns true after removing all subscribers", () => {
    const entry = new OutputRegistryEntry("test");
    const setVal = vi.fn();
    const setRecalc = vi.fn();
    entry.addUseStateSetValueFn(setVal);
    entry.addUseStateSetRecalculatingFn(setRecalc);

    entry.removeUseStateSetValueFn(setVal);
    entry.removeUseStateSetRecalculatingFn(setRecalc);
    expect(entry.isEmpty()).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd js && npx vitest run src/shiny-react/__tests__/output-registry.test.ts`
Expected: FAIL — `entry.isEmpty is not a function`

- [ ] **Step 3: Implement `isEmpty()` on `OutputRegistryEntry`**

In `js/src/shiny-react/output-registry.ts`, add this method to the `OutputRegistryEntry` class, after `setRecalculating()` (after line 43):

```ts
  isEmpty(): boolean {
    return (
      this.useStateSetValueFns.size === 0 &&
      this.useStateSetRecalculatingFns.size === 0
    );
  }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd js && npx vitest run src/shiny-react/__tests__/output-registry.test.ts`
Expected: PASS — all 4 tests

- [ ] **Step 5: Commit**

```bash
git add js/src/shiny-react/output-registry.ts js/src/shiny-react/__tests__/output-registry.test.ts
git commit -m "feat: add isEmpty() to OutputRegistryEntry"
```

---

### Task 2: Change `add()` to return dispose function, add `scheduleCleanup()`, delete `remove()`

**Files:**
- Modify: `js/src/shiny-react/output-registry.ts:47-129`

- [ ] **Step 1: Write tests for dispose and scheduleCleanup**

Append to the existing `output-registry.test.ts` file, after the `OutputRegistryEntry` describe block:

```ts
import { OutputRegistry } from "../output-registry";

// Need to set up jsdom globals that OutputRegistry constructor uses
beforeEach(() => {
  // OutputRegistry appends a container to document.body in its constructor
  // jsdom provides document.body by default in vitest
});

afterEach(() => {
  // Clean up any containers added to document.body
  document.querySelectorAll(".shiny-react-output-container").forEach((el) => el.remove());
});

describe("OutputRegistry", () => {
  it("add returns a dispose function", () => {
    const registry = new OutputRegistry();
    const dispose = registry.add("out1", vi.fn(), vi.fn());
    expect(typeof dispose).toBe("function");
  });

  it("dispose removes only its own subscribers", () => {
    const registry = new OutputRegistry();
    const setVal1 = vi.fn();
    const setRecalc1 = vi.fn();
    const setVal2 = vi.fn();
    const setRecalc2 = vi.fn();

    const dispose1 = registry.add("out1", setVal1, setRecalc1);
    registry.add("out1", setVal2, setRecalc2);

    dispose1();

    // Entry should still exist because subscriber 2 is still there
    const entry = registry.get("out1");
    expect(entry).toBeDefined();
    expect(entry!.isEmpty()).toBe(false);

    // Only subscriber 2 should receive values
    entry!.setValue("hello");
    expect(setVal1).not.toHaveBeenCalled();
    expect(setVal2).toHaveBeenCalledWith("hello");
  });

  it("scheduleCleanup removes entry and DOM when empty after RAF", async () => {
    const registry = new OutputRegistry();
    const dispose = registry.add("out1", vi.fn(), vi.fn());
    expect(registry.has("out1")).toBe(true);
    expect(document.getElementById("out1")).not.toBeNull();

    dispose();

    // Entry still exists synchronously (RAF hasn't fired)
    expect(registry.has("out1")).toBe(true);

    // Wait for RAF to fire
    await new Promise((resolve) => requestAnimationFrame(resolve));

    // Now the entry and DOM element should be cleaned up
    expect(registry.has("out1")).toBe(false);
    expect(document.getElementById("out1")).toBeNull();
  });

  it("scheduleCleanup preserves entry when re-subscribed before RAF", async () => {
    const registry = new OutputRegistry();
    const dispose1 = registry.add("out1", vi.fn(), vi.fn());

    dispose1();

    // Simulate remount — new subscriber added before RAF fires
    const setVal2 = vi.fn();
    registry.add("out1", setVal2, vi.fn());

    // Wait for RAF
    await new Promise((resolve) => requestAnimationFrame(resolve));

    // Entry should still exist — new subscriber saved it
    expect(registry.has("out1")).toBe(true);
    const entry = registry.get("out1");
    entry!.setValue("preserved");
    expect(setVal2).toHaveBeenCalledWith("preserved");
  });

  it("add reuses existing entry and DOM element", () => {
    const registry = new OutputRegistry();
    registry.add("out1", vi.fn(), vi.fn());
    const domBefore = document.getElementById("out1");

    registry.add("out1", vi.fn(), vi.fn());
    const domAfter = document.getElementById("out1");

    // Same DOM element, not a duplicate
    expect(domBefore).toBe(domAfter);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd js && npx vitest run src/shiny-react/__tests__/output-registry.test.ts`
Expected: FAIL — `add()` returns `undefined`, not a function; `remove` still exists

- [ ] **Step 3: Implement the changes to `OutputRegistry`**

Replace the `OutputRegistry` class in `js/src/shiny-react/output-registry.ts` (lines 47–129). The full new class:

```ts
export class OutputRegistry {
  private outputs: Map<string, OutputRegistryEntry<any>> = new Map();
  private bindAllScheduled = false;
  private container: HTMLElement;

  constructor() {
    const div = document.createElement("div");
    div.className = "shiny-react-output-container";
    div.style.visibility = "hidden";
    this.container = div;
    document.body.appendChild(this.container);
  }

  add<T>(
    outputId: string,
    setValue: (value: T) => void,
    setRecalculating: (value: boolean) => void,
  ): () => void {
    let outputEntry = this.get(outputId);
    if (!outputEntry) {
      // Need to create a dummy div element with the ID, so that we have
      // something to bind to.
      const div = document.createElement("div");
      div.className = "shiny-react-output";
      div.id = outputId;
      div.textContent = `This is the output div for ${outputId}`;
      this.container.appendChild(div);

      outputEntry = new OutputRegistryEntry(outputId);
      this.outputs.set(outputId, outputEntry);

      this.scheduleBindAll();
    }

    outputEntry.addUseStateSetValueFn(setValue);
    outputEntry.addUseStateSetRecalculatingFn(setRecalculating);

    return () => {
      outputEntry.removeUseStateSetValueFn(setValue);
      outputEntry.removeUseStateSetRecalculatingFn(setRecalculating);
      this.scheduleCleanup(outputId);
    };
  }

  has(outputId: string) {
    return this.outputs.has(outputId);
  }

  get(outputId: string) {
    return this.outputs.get(outputId);
  }

  private scheduleCleanup(outputId: string) {
    requestAnimationFrame(() => {
      const entry = this.outputs.get(outputId);
      if (!entry || !entry.isEmpty()) {
        return;
      }

      this.outputs.delete(outputId);
      const outputDiv = document.getElementById(outputId);
      if (outputDiv) {
        outputDiv.remove();
      }
      this.scheduleBindAll();
    });
  }

  /**
   * Schedules a Shiny binding operation to run after DOM updates are complete.
   *
   * Note: I'm not sure if this is 100% reliable. I believe we need to avoid
   * overlapping calls to bindAll(), and am not sure if requestAnimationFrame()
   * will provide perfect reliability for this.
   */
  private scheduleBindAll() {
    const shiny = getShiny();
    if (!shiny) {
      return;
    }

    if (this.bindAllScheduled) {
      return;
    }

    this.bindAllScheduled = true;

    // Use requestAnimationFrame to ensure DOM updates are complete
    requestAnimationFrame(() => {
      shiny.unbindAll?.(this.container);
      // eslint-disable-next-line @typescript-eslint/no-floating-promises
      shiny.bindAll?.(this.container);
      this.bindAllScheduled = false;
    });
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd js && npx vitest run src/shiny-react/__tests__/output-registry.test.ts`
Expected: PASS — all tests

- [ ] **Step 5: Run type check**

Run: `cd js && npx tsc --noEmit`
Expected: Error in `use-shiny.ts` — `outputs.remove` no longer exists. This is expected and will be fixed in Task 3.

- [ ] **Step 6: Commit**

```bash
git add js/src/shiny-react/output-registry.ts js/src/shiny-react/__tests__/output-registry.test.ts
git commit -m "feat: add dispose pattern and scheduleCleanup to OutputRegistry

add() now returns a dispose function that removes only the caller's
subscribers. Deferred RAF cleanup deletes entry+DOM only when no
subscribers remain, fixing the race condition on same-commit
unmount/remount (e.g. tab switching).

Removes the destructive remove() method."
```

---

### Task 3: Update `useShinyOutput` to use dispose pattern

**Files:**
- Modify: `js/src/shiny-react/use-shiny.ts:193-213`

- [ ] **Step 1: Update `useShinyOutput` cleanup**

In `js/src/shiny-react/use-shiny.ts`, replace the `useEffect` body in `useShinyOutput` (lines 193–203):

From:

```ts
  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }

    const reactRegistry = getReactRegistry();
    reactRegistry.outputs.add(namespacedOutputId, setValue, setRecalculating);
    return () => {
      reactRegistry.outputs.remove(namespacedOutputId);
    };
  }, [namespacedOutputId, shinyInitialized]);
```

To:

```ts
  useEffect(() => {
    if (!shinyInitialized) {
      return;
    }

    const reactRegistry = getReactRegistry();
    const dispose = reactRegistry.outputs.add(
      namespacedOutputId,
      setValue,
      setRecalculating,
    );
    return dispose;
  }, [namespacedOutputId, shinyInitialized]);
```

- [ ] **Step 2: Remove the stale TODOs**

Delete lines 208–214 (the TODO comments about reference counting and useShinyOutputValue):

```ts
// TODO: Also get error value?
//
// TODO: Use reference counter; when last reference to a particular output is
// removed, disable the output and/or remove the DOM element. And maybe remove
// from registry?

// TODO: (possible) Implement useShinyOutputValue and useShinyOutputRecalculating
```

Replace with just the remaining TODO:

```ts
// TODO: Also get error value?

// TODO: (possible) Implement useShinyOutputValue and useShinyOutputRecalculating
```

- [ ] **Step 3: Run type check**

Run: `cd js && npx tsc --noEmit`
Expected: PASS — no type errors

- [ ] **Step 4: Run all JS tests**

Run: `cd js && npx vitest run`
Expected: PASS — all tests including output-registry and existing tests

- [ ] **Step 5: Commit**

```bash
git add js/src/shiny-react/use-shiny.ts
git commit -m "feat: useShinyOutput cleanup uses dispose from add()

Replaces destructive outputs.remove() call with the dispose function
returned by add(). Removes the resolved reference-counting TODO."
```

---

### Task 4: Build JS bundle

**Files:**
- Modify: `js/dist/shinyjson.js` (generated)
- Modify: `pkg-py/src/shinyjson/www/shinyjson.js` (copied)
- Modify: `pkg-r/inst/lib/shiny/shinyjson.js` (copied)

- [ ] **Step 1: Build and copy dist**

Run: `make update-dist`
Expected: JS builds successfully, files copied to `pkg-py/` and `pkg-r/`

- [ ] **Step 2: Verify the built bundle no longer contains `remove(outputId)`**

Run: `grep -c "outputs.remove\|\.remove(outputId)" js/dist/shinyjson.js`
Expected: 0 matches (the `remove()` method no longer exists on `OutputRegistry`)

- [ ] **Step 3: Commit**

```bash
git add js/dist/ pkg-py/src/shinyjson/www/ pkg-r/inst/lib/shiny/
git commit -m "chore: rebuild JS bundle with output registry refcount"
```

---

### Task 5: Update STATUS.md

**Files:**
- Modify: `docs/STATUS.md:7-9` (remove TODO)
- Modify: `docs/STATUS.md:104+` (add Recent fix)

- [ ] **Step 1: Remove the TODO entry**

In `docs/STATUS.md`, delete the "Output registry `remove()` is destructive — needs reference counting" heading and its body paragraph (lines 7–9).

- [ ] **Step 2: Add a Recent fix bullet**

Add this bullet at the top of the `### Recent fixes` section:

```markdown
- **Output registry reference-counted cleanup**: `OutputRegistry.add()` now returns a dispose function that removes only the caller's subscribers. Deferred RAF cleanup deletes the entry and DOM element only when no subscribers remain, fixing the race condition where tab switching caused duplicate output bindings.
```

- [ ] **Step 3: Commit**

```bash
git add docs/STATUS.md
git commit -m "docs: update STATUS.md for output registry refcount fix"
```

---

### Task 6: Manual verification of 6-dashboard duplicate output warning

**Files:**
- Possibly modify: `docs/STATUS.md:93` (6-dashboard table entry)
- Possibly modify: `docs/timeline.md:41` (duplicate output IDs bullet)

- [ ] **Step 1: Run example 6-dashboard**

Run: `cd examples/6-dashboard && uv run shiny run app.py --port 8766`

- [ ] **Step 2: Test tab switching**

Open `http://localhost:8766` in a browser. Switch between tabs (Overview, Table, etc.) several times. Check the browser console for "duplicate output" warnings.

- [ ] **Step 3: If no warnings — update docs**

If the duplicate output warning is gone, update `docs/STATUS.md` line 93 to remove the note:

From:
```
| 6-dashboard | 8766 | Working | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters; duplicate output ID warning on tab switch |
```

To:
```
| 6-dashboard | 8766 | Working | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters |
```

And update `docs/timeline.md` line 41. Remove:
```
  - **Duplicate output IDs on tab navigation** — switching tabs unmounts/remounts useShinyOutput components, creating duplicate bindings. Fix output registry cleanup/re-registration or keep pages mounted.
```

- [ ] **Step 4: If warnings persist — leave docs as-is and note findings**

If warnings still appear, the root cause may be different (e.g., `ImageOutput` which bypasses the registry). Leave the STATUS.md and timeline.md entries unchanged.

- [ ] **Step 5: Commit (if docs were updated)**

```bash
git add docs/STATUS.md docs/timeline.md
git commit -m "docs: remove duplicate output ID warning from 6-dashboard

Verified that tab switching no longer produces duplicate binding
warnings after the output registry refcount fix."
```
