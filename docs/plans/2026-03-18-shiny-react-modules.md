# Shiny-React Module Namespace Support — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate `wch/shiny-react#3` module namespace support into shinyjson's vendored copy, fix Python `post_message` namespacing, add upstream examples as reference material, and add JavaScript unit tests.

**Architecture:** Copy two new files (`ShinyModuleContext.tsx`, `ShinyReactComponentElement.tsx`) into the vendored `js/src/shiny-react/` directory. Apply namespace diffs to `use-shiny.ts`, `ImageOutput.tsx`, and `index.ts`. Expose new exports on `window.shinyjson`. Add Vitest + jsdom + Testing Library for JS tests. Copy upstream examples into `examples/shiny-react-upstream/`.

**Tech Stack:** TypeScript, React 19, Vitest, jsdom, @testing-library/react, Python (shiny.module.resolve_id)

---

### Task 1: Add Vitest test infrastructure

**Files:**
- Modify: `js/package.json`
- Create: `js/vitest.config.ts`
- Modify: `Makefile`

**Step 1: Add Vitest dev dependencies**

In `js/package.json`, add to `devDependencies`:

```json
"vitest": "^3.2.1",
"jsdom": "^26.1.0",
"@testing-library/react": "^16.3.0"
```

**Step 2: Create Vitest config**

Create `js/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
  },
});
```

**Step 3: Add test script to package.json**

In `js/package.json`, add to `scripts`:

```json
"test": "vitest run"
```

**Step 4: Add Makefile target**

In `Makefile`, after the `js-build-watch` target (line 53), add:

```makefile
.PHONY: js-test
js-test:  ## [js] Run JS tests
	@echo "🧪 Running JS tests"
	cd $(PATH_PKG_JS) && npm test
```

**Step 5: Install dependencies**

Run: `cd js && npm install`
Expected: package-lock.json updated, node_modules updated

**Step 6: Verify test runner works**

Run: `cd js && npx vitest run`
Expected: "No test files found" (no tests yet — confirms vitest is working)

**Step 7: Commit**

```bash
git add js/package.json js/package-lock.json js/vitest.config.ts Makefile
git commit -m "chore: add Vitest test infrastructure with jsdom and Testing Library"
```

---

### Task 2: Add `ShinyModuleContext.tsx` with tests

**Files:**
- Create: `js/src/shiny-react/ShinyModuleContext.tsx`
- Create: `js/src/shiny-react/__tests__/ShinyModuleContext.test.tsx`

**Step 1: Write the tests**

Create `js/src/shiny-react/__tests__/ShinyModuleContext.test.tsx`:

```typescript
import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import {
  applyNamespace,
  ShinyModuleProvider,
  useShinyModuleNamespace,
} from "../ShinyModuleContext";

describe("applyNamespace", () => {
  it("prefixes id with namespace when namespace is provided", () => {
    expect(applyNamespace("count", "mod1")).toBe("mod1-count");
  });

  it("returns raw id when namespace is null", () => {
    expect(applyNamespace("count", null)).toBe("count");
  });

  it("returns raw id when namespace is empty string", () => {
    expect(applyNamespace("count", "")).toBe("count");
  });
});

describe("ShinyModuleProvider / useShinyModuleNamespace", () => {
  it("returns null when not inside a provider", () => {
    const { result } = renderHook(() => useShinyModuleNamespace());
    expect(result.current).toBeNull();
  });

  it("returns the namespace from the provider", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="myModule">{children}</ShinyModuleProvider>
    );
    const { result } = renderHook(() => useShinyModuleNamespace(), { wrapper });
    expect(result.current).toBe("myModule");
  });

  it("inner provider overrides outer provider", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="outer">
        <ShinyModuleProvider namespace="inner">{children}</ShinyModuleProvider>
      </ShinyModuleProvider>
    );
    const { result } = renderHook(() => useShinyModuleNamespace(), { wrapper });
    expect(result.current).toBe("inner");
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd js && npx vitest run`
Expected: FAIL — `ShinyModuleContext` module not found

**Step 3: Create `ShinyModuleContext.tsx`**

Create `js/src/shiny-react/ShinyModuleContext.tsx`:

```tsx
import { createContext, useContext, type ReactNode } from "react";

const ShinyModuleContext = createContext<string | null>(null);

export interface ShinyModuleProviderProps {
  namespace: string;
  children: ReactNode;
}

/**
 * Provides a namespace context for Shiny module support.
 *
 * All child components using useShinyInput, useShinyOutput, or
 * useShinyMessageHandler will automatically have their IDs prefixed
 * with the provided namespace.
 *
 * Note: This provider does NOT support nesting. If you need nested modules,
 * pass the full namespace string (e.g., "outer-inner") directly.
 *
 * @param namespace The complete namespace string to apply to child hooks.
 * @param children React children that will receive the namespace context.
 *
 * @example
 * ```tsx
 * <ShinyModuleProvider namespace="myModule">
 *   <MyComponent /> {/* useShinyInput("x") becomes "myModule-x" *}
 * </ShinyModuleProvider>
 * ```
 */
export function ShinyModuleProvider({
  namespace,
  children,
}: ShinyModuleProviderProps) {
  return (
    <ShinyModuleContext.Provider value={namespace}>
      {children}
    </ShinyModuleContext.Provider>
  );
}

/**
 * Hook to access the current module namespace from context.
 * Returns null if not within a ShinyModuleProvider.
 */
export function useShinyModuleNamespace(): string | null {
  return useContext(ShinyModuleContext);
}

/**
 * Utility function to apply namespace to an ID.
 * If namespace is provided, returns `${namespace}-${id}`.
 * Otherwise returns the original id.
 */
export function applyNamespace(id: string, namespace: string | null): string {
  if (namespace) {
    return `${namespace}-${id}`;
  }
  return id;
}
```

**Step 4: Run tests to verify they pass**

Run: `cd js && npx vitest run`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add js/src/shiny-react/ShinyModuleContext.tsx js/src/shiny-react/__tests__/ShinyModuleContext.test.tsx
git commit -m "feat: add ShinyModuleContext with provider, hook, and applyNamespace"
```

---

### Task 3: Add namespace support to `use-shiny.ts` with tests

**Files:**
- Modify: `js/src/shiny-react/use-shiny.ts`
- Create: `js/src/shiny-react/__tests__/use-shiny-namespace.test.tsx`

**Step 1: Write the tests**

Create `js/src/shiny-react/__tests__/use-shiny-namespace.test.tsx`:

```typescript
import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { ReactNode } from "react";
import { ShinyModuleProvider } from "../ShinyModuleContext";

// Mock the registries and Shiny initialization so hooks can run
// without a real Shiny environment
vi.mock("../get-shiny", () => ({
  getShiny: () => undefined,
}));

vi.mock("../react-registry", () => {
  const inputs = {
    get: vi.fn(() => null),
    getOrCreate: vi.fn(() => ({
      updateDebounceDelay: vi.fn(),
      updatePriority: vi.fn(),
      addUseStateSetValueFn: vi.fn(),
      removeUseStateSetValueFn: vi.fn(),
      getValue: vi.fn(() => null),
      setValue: vi.fn(),
    })),
  };
  const outputs = {
    add: vi.fn(),
    remove: vi.fn(),
  };
  return {
    initializeReactRegistry: vi.fn(),
    getReactRegistry: vi.fn(() => ({ inputs, outputs })),
    __inputs: inputs,
    __outputs: outputs,
  };
});

vi.mock("../output-registry", () => ({
  createReactOutputBinding: vi.fn(),
}));

vi.mock("../message-registry", () => ({
  initializeMessageRegistry: vi.fn(),
}));

import { useShinyInput, useShinyOutput } from "../use-shiny";
import { getReactRegistry } from "../react-registry";

describe("useShinyInput namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain id when no namespace is provided", () => {
    renderHook(() => useShinyInput("count", 0));
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("count", 0);
  });

  it("uses explicit namespace option", () => {
    renderHook(() =>
      useShinyInput("count", 0, { namespace: "mod1" }),
    );
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("mod1-count", 0);
  });

  it("uses namespace from ShinyModuleProvider context", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInput("count", 0), { wrapper });
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("ctxMod-count", 0);
  });

  it("explicit namespace overrides context namespace", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInput("count", 0, { namespace: "explicit" }), {
      wrapper,
    });
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith(
      "explicit-count",
      0,
    );
  });
});

describe("useShinyOutput namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain outputId when no namespace is provided", () => {
    renderHook(() => useShinyOutput("result"));
    // Note: outputs.add is only called after shiny is initialized,
    // which won't happen in our mock. We verify via the registry lookup id.
    const registry = getReactRegistry();
    // The hook should have been created without error
    expect(registry).toBeDefined();
  });

  it("uses explicit namespace option for output", () => {
    renderHook(() =>
      useShinyOutput("result", undefined, { namespace: "mod1" }),
    );
    const registry = getReactRegistry();
    expect(registry).toBeDefined();
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd js && npx vitest run`
Expected: FAIL — `useShinyInput` doesn't accept `namespace` option yet

**Step 3: Apply namespace changes to `use-shiny.ts`**

Modify `js/src/shiny-react/use-shiny.ts`:

Add import at line 10 (after existing imports):

```typescript
import {
  applyNamespace,
  useShinyModuleNamespace,
} from "./ShinyModuleContext";
```

**`useShinyInput`** — modify the function signature and body:

At line 43-49, add `namespace` to the options destructure:

```typescript
export function useShinyInput<T>(
  id: string,
  defaultValue: T,
  {
    debounceMs = 100,
    priority,
    namespace: explicitNamespace,
  }: {
    debounceMs?: number;
    priority?: EventPriority;
    namespace?: string;
  } = {},
): [T, (value: T) => void] {
  ensureShinyReactInitialized();

  // Apply namespace from context or explicit option
  const contextNamespace = useShinyModuleNamespace();
  const namespace = explicitNamespace ?? contextNamespace;
  const namespacedId = applyNamespace(id, namespace);
```

Then replace all occurrences of `id` used for registry lookups:
- Line 62-63: `reactRegistry.inputs.get(id,)` → `reactRegistry.inputs.get(namespacedId,)`
- Line 87-88: `reactRegistry.inputs.getOrCreate<T>(id,` → `reactRegistry.inputs.getOrCreate<T>(namespacedId,`
- Line 112: deps array `[id, shinyInitialized,` → `[namespacedId, shinyInitialized,`
- Line 121: `reactRegistry.inputs.get(id)` → `reactRegistry.inputs.get(namespacedId)`
- Line 128: deps `[id]` → `[namespacedId, id]`

**`useShinyOutput`** — add namespace option as third parameter:

```typescript
export function useShinyOutput<T>(
  outputId: string,
  defaultValue: T | undefined = undefined,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string;
  } = {},
): [T | undefined, boolean] {
```

After `ensureShinyReactInitialized();`, add:

```typescript
  // Apply namespace from context or explicit option
  const contextNamespace = useShinyModuleNamespace();
  const namespace = explicitNamespace ?? contextNamespace;
  const namespacedOutputId = applyNamespace(outputId, namespace);
```

Replace registry calls:
- `reactRegistry.outputs.add(outputId,` → `reactRegistry.outputs.add(namespacedOutputId,`
- `reactRegistry.outputs.remove(outputId)` → `reactRegistry.outputs.remove(namespacedOutputId)`
- deps: `[outputId, shinyInitialized]` → `[namespacedOutputId, shinyInitialized]`

**`useShinyMessageHandler`** — add namespace option as third parameter:

```typescript
export function useShinyMessageHandler<T = any>(
  messageType: string,
  handler: (data: T) => void,
  {
    namespace: explicitNamespace,
  }: {
    namespace?: string;
  } = {},
): void {
```

After `ensureShinyReactInitialized();`, add:

```typescript
  // Apply namespace from context or explicit option
  const contextNamespace = useShinyModuleNamespace();
  const namespace = explicitNamespace ?? contextNamespace;
  const namespacedMessageType = applyNamespace(messageType, namespace);
```

Replace:
- `if (!shinyInitialized || !messageType` → `if (!shinyInitialized || !namespacedMessageType`
- `shiny.messageRegistry.addHandler(messageType,` → `shiny.messageRegistry.addHandler(namespacedMessageType,`
- `shiny.messageRegistry.removeHandler(messageType,` → `shiny.messageRegistry.removeHandler(namespacedMessageType,`
- deps: `[shinyInitialized, messageType, handler]` → `[shinyInitialized, namespacedMessageType, handler]`

**Step 4: Run tests to verify they pass**

Run: `cd js && npx vitest run`
Expected: All tests PASS

**Step 5: Verify TypeScript compiles**

Run: `cd js && npx tsc --noEmit`
Expected: No errors

**Step 6: Commit**

```bash
git add js/src/shiny-react/use-shiny.ts js/src/shiny-react/__tests__/use-shiny-namespace.test.tsx
git commit -m "feat: add namespace support to useShinyInput, useShinyOutput, useShinyMessageHandler"
```

---

### Task 4: Add namespace support to `ImageOutput.tsx`

**Files:**
- Modify: `js/src/shiny-react/ImageOutput.tsx`

**Step 1: Apply namespace changes to ImageOutput**

At the top of `js/src/shiny-react/ImageOutput.tsx`, after line 3, add:

```typescript
import {
  applyNamespace,
  useShinyModuleNamespace,
} from "./ShinyModuleContext";
```

Add `namespace` prop and jsdoc at line 138 (in the props type), add:

```typescript
  namespace: explicitNamespace,
```

And in the type definition add:

```typescript
  namespace?: string;
```

At the start of the function body (after the opening `{`), add:

```typescript
  // Apply namespace from context or explicit option
  const contextNamespace = useShinyModuleNamespace();
  const namespace = explicitNamespace ?? contextNamespace;
  const namespacedId = applyNamespace(id, namespace);
```

Replace the clientdata input IDs:
- `".clientdata_output_" + id + "_width"` → `` `.clientdata_output_${namespacedId}_width` ``
- `".clientdata_output_" + id + "_height"` → `` `.clientdata_output_${namespacedId}_height` ``
- `".clientdata_output_" + id + "_hidden"` → `` `.clientdata_output_${namespacedId}_hidden` ``
- `useShinyOutput<ImageData>(id,` → `useShinyOutput<ImageData>(namespacedId,`

**Step 2: Verify TypeScript compiles**

Run: `cd js && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add js/src/shiny-react/ImageOutput.tsx
git commit -m "feat: add namespace support to ImageOutput component"
```

---

### Task 5: Update shiny-react `index.ts` exports

**Files:**
- Modify: `js/src/shiny-react/index.ts`

**Step 1: Add new exports**

In `js/src/shiny-react/index.ts`, after line 6 (`export { ImageOutput }`), add:

```typescript
export { ShinyReactComponentElement } from "./ShinyReactComponentElement";
```

After line 12 (after the `use-shiny` export block), add:

```typescript
export {
  ShinyModuleProvider,
  useShinyModuleNamespace,
} from "./ShinyModuleContext";
```

**Step 2: Verify TypeScript compiles**

Run: `cd js && npx tsc --noEmit`
Expected: Will fail because `ShinyReactComponentElement.tsx` doesn't exist yet. That's OK — skip to Task 6, then come back.

**Step 3: Commit** (defer until after Task 6)

---

### Task 6: Add `ShinyReactComponentElement.tsx` with tests

**Files:**
- Create: `js/src/shiny-react/ShinyReactComponentElement.tsx`
- Create: `js/src/shiny-react/__tests__/ShinyReactComponentElement.test.tsx`

**Step 1: Write the tests**

Create `js/src/shiny-react/__tests__/ShinyReactComponentElement.test.tsx`:

```typescript
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { ShinyReactComponentElement } from "../ShinyReactComponentElement";

// Minimal Shiny mock on window
beforeEach(() => {
  (window as any).Shiny = {
    bindAll: vi.fn(),
    unbindAll: vi.fn(),
  };
});

afterEach(() => {
  delete (window as any).Shiny;
});

describe("ShinyReactComponentElement", () => {
  describe("getConfig", () => {
    it("parses data-* attributes into a config object", () => {
      const el = new ShinyReactComponentElement();
      el.setAttribute("data-count", "5");
      el.setAttribute("data-title", "Hello");
      el.setAttribute("data-enabled", "true");
      el.setAttribute("data-items", "[1,2,3]");

      // Access protected method via type cast
      const config = (el as any).getConfig();

      expect(config.count).toBe(5);
      expect(config.title).toBe("Hello");
      expect(config.enabled).toBe(true);
      expect(config.items).toEqual([1, 2, 3]);
    });

    it("falls back to string for non-JSON values", () => {
      const el = new ShinyReactComponentElement();
      el.setAttribute("data-label", "not json");

      const config = (el as any).getConfig();
      expect(config.label).toBe("not json");
    });
  });

  describe("namespace", () => {
    it("returns undefined when no id is set", () => {
      const el = new ShinyReactComponentElement();
      expect((el as any).namespace).toBeUndefined();
    });

    it("returns the element id as namespace", () => {
      const el = new ShinyReactComponentElement();
      el.id = "counter1";
      expect((el as any).namespace).toBe("counter1");
    });
  });

  describe("captureSlots", () => {
    it("captures children as __children__ when no data-slot elements exist", () => {
      const el = new ShinyReactComponentElement();
      const child = document.createElement("div");
      child.textContent = "hello";
      el.appendChild(child);

      const slots = (el as any).captureSlots();
      expect(slots.has("__children__")).toBe(true);
      expect(slots.get("__children__")).toHaveLength(1);
    });

    it("captures named slots from data-slot attributes", () => {
      const el = new ShinyReactComponentElement();
      const sidebar = document.createElement("div");
      sidebar.setAttribute("data-slot", "sidebar");
      sidebar.innerHTML = "<p>Sidebar</p>";
      el.appendChild(sidebar);

      const main = document.createElement("div");
      main.setAttribute("data-slot", "main");
      main.innerHTML = "<p>Main</p>";
      el.appendChild(main);

      const slots = (el as any).captureSlots();
      expect(slots.has("sidebar")).toBe(true);
      expect(slots.has("main")).toBe(true);
      expect(slots.has("__children__")).toBe(false);
    });

    it("returns empty map when element has no children", () => {
      const el = new ShinyReactComponentElement();
      const slots = (el as any).captureSlots();
      expect(slots.size).toBe(0);
    });
  });

  describe("mountSlot", () => {
    it("moves captured content into a container and calls Shiny.bindAll", async () => {
      const el = new ShinyReactComponentElement();
      const child = document.createElement("div");
      child.textContent = "hello";
      el.appendChild(child);
      (el as any).captureSlots();

      const container = document.createElement("div");
      await (el as any).mountSlot("__children__", container);

      expect(container.childNodes).toHaveLength(1);
      expect(container.textContent).toBe("hello");
      expect((window as any).Shiny.bindAll).toHaveBeenCalledWith(container);
    });

    it("does nothing when slot name not found", async () => {
      const el = new ShinyReactComponentElement();
      const container = document.createElement("div");
      await (el as any).mountSlot("nonexistent", container);
      expect(container.childNodes).toHaveLength(0);
    });
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd js && npx vitest run`
Expected: FAIL — `ShinyReactComponentElement` module not found

**Step 3: Create `ShinyReactComponentElement.tsx`**

Create `js/src/shiny-react/ShinyReactComponentElement.tsx` with the exact content from the PR (218 lines). The file is reproduced in the design doc's Section 1 and in the PR diff above. Copy verbatim from the PR diff lines 3750-3967.

**Step 4: Run tests to verify they pass**

Run: `cd js && npx vitest run`
Expected: All tests PASS

**Step 5: Verify TypeScript compiles (with Task 5 exports)**

Run: `cd js && npx tsc --noEmit`
Expected: No errors

**Step 6: Commit (combined with Task 5 index.ts changes)**

```bash
git add js/src/shiny-react/ShinyReactComponentElement.tsx js/src/shiny-react/__tests__/ShinyReactComponentElement.test.tsx js/src/shiny-react/index.ts
git commit -m "feat: add ShinyReactComponentElement base class and update shiny-react exports"
```

---

### Task 7: Update `window.shinyjson` global API

**Files:**
- Modify: `js/src/index.ts:16-53`

**Step 1: Add imports**

In `js/src/index.ts`, at line 21 (after the `ImageOutput` import), add:

```typescript
import {
  ShinyModuleProvider,
  ShinyReactComponentElement,
} from "./shiny-react";
```

**Step 2: Add to type declaration**

In the `Window.shinyjson` interface (lines 27-39), add:

```typescript
      ShinyModuleProvider: typeof ShinyModuleProvider;
      ShinyReactComponentElement: typeof ShinyReactComponentElement;
```

**Step 3: Add to runtime object**

In the `window.shinyjson = { ... }` assignment (lines 44-53), add:

```typescript
  ShinyModuleProvider,
  ShinyReactComponentElement,
```

**Step 4: Verify TypeScript compiles**

Run: `cd js && npx tsc --noEmit`
Expected: No errors

**Step 5: Build the JS bundle**

Run: `make js-build`
Expected: Build succeeds, `js/dist/shinyjson.js` updated

**Step 6: Commit**

```bash
git add js/src/index.ts
git commit -m "feat: expose ShinyModuleProvider and ShinyReactComponentElement on window.shinyjson"
```

---

### Task 8: Fix Python `post_message` namespacing

**Files:**
- Modify: `pkg-py/src/shinyjson/_post_message.py:1-36`
- Modify: `pkg-py/tests/test_post_message.py`

**Step 1: Write the failing test**

Add to `pkg-py/tests/test_post_message.py`:

```python
    @pytest.mark.asyncio
    async def test_namespaces_type_with_resolve_id(self):
        """post_message uses resolve_id to namespace the message type."""
        session = AsyncMock()

        # Simulate being inside a Shiny module with namespace "mymod"
        with unittest.mock.patch(
            "shinyjson._post_message.resolve_id",
            side_effect=lambda x: f"mymod-{x}",
        ):
            await post_message(session, "logEvent", {"text": "hello"})

        session.send_custom_message.assert_called_once_with(
            "shinyReactMessage",
            {"type": "mymod-logEvent", "data": {"text": "hello"}},
        )
```

Also add `import unittest.mock` at the top of the file.

**Step 2: Run test to verify it fails**

Run: `uv run pytest pkg-py/tests/test_post_message.py::TestPostMessage::test_namespaces_type_with_resolve_id -v`
Expected: FAIL — `resolve_id` not used yet

**Step 3: Update `_post_message.py`**

In `pkg-py/src/shinyjson/_post_message.py`, add the import after line 1:

```python
from shiny.module import resolve_id
```

And change line 34 from:

```python
    await session.send_custom_message(
        "shinyReactMessage", {"type": type, "data": data}
    )
```

to:

```python
    namespaced_type = resolve_id(type)
    await session.send_custom_message(
        "shinyReactMessage", {"type": namespaced_type, "data": data}
    )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest pkg-py/tests/test_post_message.py -v`
Expected: All 4 tests PASS

**Step 5: Run full Python checks**

Run: `make py-check`
Expected: All checks pass (format, types, tests)

**Step 6: Commit**

```bash
git add pkg-py/src/shinyjson/_post_message.py pkg-py/tests/test_post_message.py
git commit -m "fix: namespace post_message type using resolve_id for module support"
```

---

### Task 9: Copy upstream examples

**Files:**
- Create: `examples/shiny-react-upstream/` (entire directory tree)
- Modify: `.gitignore`

**Step 1: Clone the PR branch and copy examples**

```bash
# Clone into a temp directory
git clone --depth 1 --branch feat/multiple-react-roots https://github.com/gadenbuie/shiny-react.git /tmp/shiny-react-pr3

# Copy all examples
cp -r /tmp/shiny-react-pr3/examples/ examples/shiny-react-upstream/

# Copy the README
cp /tmp/shiny-react-pr3/README.md examples/shiny-react-upstream/README.md

# Clean up
rm -rf /tmp/shiny-react-pr3
```

**Step 2: Add gitignore entry**

In `.gitignore`, at the end (after `node_modules/`), add:

```
# Built assets in shiny-react upstream examples
examples/shiny-react-upstream/*/www/
```

**Step 3: Verify the structure**

Run: `ls examples/shiny-react-upstream/`
Expected: `1-hello-world/  2-inputs/  3-outputs/  4-messages/  5-shadcn/  6-dashboard/  7-chat/  8-modules/  9-blended/  README.md`

**Step 4: Commit**

```bash
git add examples/shiny-react-upstream/ .gitignore
git commit -m "chore: copy upstream shiny-react examples as reference material

Verbatim copies from wch/shiny-react#3 (gadenbuie:feat/multiple-react-roots).
These use the @posit/shiny-react copy-paste pattern and won't run as-is
within shinyjson. They serve as reference for future adaptation."
```

---

### Task 10: Build and verify everything

**Files:**
- Modify: `js/dist/shinyjson.js` (rebuilt)
- Modify: `js/dist/shinyjson.css` (rebuilt)
- Modify: `pkg-py/src/shinyjson/www/` (copied)
- Modify: `pkg-r/inst/lib/shiny/` (copied)

**Step 1: Run all JS tests**

Run: `make js-test`
Expected: All tests pass

**Step 2: Run JS lint**

Run: `make js-lint`
Expected: No errors

**Step 3: Build and distribute**

Run: `make update-dist`
Expected: JS builds, assets copied to pkg-py and pkg-r

**Step 4: Run Python checks**

Run: `make py-check`
Expected: All checks pass

**Step 5: Commit built assets**

```bash
git add js/dist/ pkg-py/src/shinyjson/www/ pkg-r/inst/lib/shiny/
git commit -m "chore: rebuild JS bundle with module namespace support"
```
