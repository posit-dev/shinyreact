# Flatten and reorganize `js/src/` TS files — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink `js/src/index.ts` to a readable boot sequence by extracting the output binding and global wiring into their own files, and rename `spec.ts` → `types.ts`, with zero change to the IIFE bundle's external behavior.

**Architecture:** Pure refactor of the IIFE entry module. Move three concerns out of `index.ts` — the `ShinyreactOutputBinding` class (→ `output-binding.ts`), the `window.shinyreact` global declaration + assignment (→ `global.ts`), and the wire-tree types (rename `spec.ts` → `types.ts`). Both extracted modules expose explicit `install`/`register` functions (no import-time side effects); `index.ts` calls them in order. Correctness is guaranteed by the existing test suite, `tsc --noEmit`, and a byte-similar build output — no new behavior, so no new tests.

**Tech Stack:** TypeScript, React 19, Vite (IIFE build), Vitest, vendored `@posit/shiny-react`.

**Spec:** `docs/superpowers/specs/2026-06-10-flatten-js-src-design.md`

**Note on TDD for this plan:** This is a behavior-preserving refactor already covered by `js/src/__tests__/`. The discipline here is *keep the suite + lint green after every task and commit each step*. Each task ends by running `npx vitest run` and `npm run lint` (tsc) from `js/`, both of which must stay green. Do not add new tests — there is no new behavior.

**Baseline (do this once before Task 1):**

- [ ] Capture the current build output hash so we can confirm byte-similarity at the end.

Run (from repo root):
```bash
cd js && npm run build && shasum dist/shinyreact.js && cd ..
```
Expected: build succeeds; record the printed hash (call it `BASELINE_HASH`). The hash may legitimately differ slightly after the refactor due to bundler source ordering — the final check is "diff is trivial / module-order only", not "identical hash".

- [ ] Confirm the suite and lint are green before starting.

Run (from `js/`):
```bash
npm run lint && npx vitest run
```
Expected: tsc reports no errors; all vitest tests PASS.

---

## File Structure

| File | Responsibility after refactor |
|------|-------------------------------|
| `js/src/index.ts` | Entry point — calls `installGlobal()`, `registerShinyreactOutputBinding()`, `installInlineSpecSeeding()` in order (~8 lines). |
| `js/src/global.ts` | **New.** `declare global { Window.shinyreact }` + `installGlobal()` performing the `window.shinyreact = Object.assign(...)` assignment. |
| `js/src/output-binding.ts` | **New.** `ShinyreactOutputBinding` class + `registerShinyreactOutputBinding()`. |
| `js/src/types.ts` | **Renamed** from `spec.ts`. Wire-tree TS types only; exported names unchanged. |
| `js/src/shiny.d.ts` | Ambient Shiny decls; doc-comment reference updated to `output-binding.ts`. |
| `js/src/registry.ts`, `roots.ts`, `renderer.tsx`, `inline-spec.tsx`, `shiny-output.tsx` | Unchanged except import path `./spec` → `./types` where present. |

---

### Task 1: Rename `spec.ts` → `types.ts`

Smallest mechanical change first; keeps later diffs clean.

**Files:**
- Rename: `js/src/spec.ts` → `js/src/types.ts`
- Modify imports in: `js/src/renderer.tsx`, `js/src/inline-spec.tsx`, `js/src/registry.ts`, `js/src/index.ts`, `js/src/__tests__/renderer.test.tsx`

- [ ] **Step 1: Rename the file via git**

Run (from repo root):
```bash
git mv js/src/spec.ts js/src/types.ts
```
Expected: no output; `git status` shows `renamed: js/src/spec.ts -> js/src/types.ts`. No edits inside the file — exported type names (`Element`, `Spec`, `ComponentRegistry`, …) stay as-is.

- [ ] **Step 2: Update the five import paths**

In each file, change the import source `"./spec"` → `"./types"` (and `"../spec"` → `"../types"` in the test). The exact lines:

`js/src/renderer.tsx:2`:
```ts
import type { ComponentRegistry, Element, Spec } from "./types";
```
`js/src/inline-spec.tsx:2`:
```ts
import type { Spec } from "./types";
```
`js/src/registry.ts:1`:
```ts
import type { ComponentRegistry } from "./types";
```
`js/src/index.ts:3`:
```ts
import type { ComponentRegistry, Spec } from "./types";
```
`js/src/__tests__/renderer.test.tsx:4`:
```ts
import type { Spec } from "../types";
```

- [ ] **Step 3: Verify lint and tests are green**

Run (from `js/`):
```bash
npm run lint && npx vitest run
```
Expected: tsc no errors (proves no dangling `./spec` import remains); all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add js/src/types.ts js/src/renderer.tsx js/src/inline-spec.tsx js/src/registry.ts js/src/index.ts js/src/__tests__/renderer.test.tsx
git commit -m "refactor(js): rename spec.ts to types.ts (#54)"
```

---

### Task 2: Extract `output-binding.ts`

Move the `ShinyreactOutputBinding` class out of `index.ts` into its own file with an explicit register function.

**Files:**
- Create: `js/src/output-binding.ts`
- Modify: `js/src/index.ts` (remove the class + the `Shiny.outputBindings.register(...)` line; add an import + call — done fully in Task 3, but this task leaves `index.ts` calling the new function)

- [ ] **Step 1: Create `js/src/output-binding.ts`**

```ts
import React from "react";
import type { Spec } from "./types";
import { ShinyreactRenderer } from "./renderer";
import { getOrCreateRoot, hasRoot, unmountRoot } from "./roots";

// Shiny output binding for .shinyreact-output elements.
class ShinyreactOutputBinding extends Shiny.OutputBinding {
  find(scope: Element): ArrayLike<Element> {
    return $(scope).find(".shinyreact-output");
  }

  renderValue(el: Element, data: Spec | null): void {
    if (!data) {
      if (hasRoot(el)) unmountRoot(el);
      return;
    }
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(React.createElement(ShinyreactRenderer, { spec: data }));
  }

  renderError(el: Element, err: { message: string }): void {
    const root = getOrCreateRoot(el as HTMLElement);
    root.render(
      React.createElement(
        "div",
        { style: { color: "red", padding: "8px" } },
        err.message,
      ),
    );
  }
}

/**
 * Register shinyreact's output binding with Shiny. Shiny is always loaded
 * before this runs because HTMLDependency ordering places Shiny's scripts
 * first.
 */
export function registerShinyreactOutputBinding(): void {
  Shiny.outputBindings.register(
    new ShinyreactOutputBinding(),
    "shinyreact.output",
  );
}
```

- [ ] **Step 2: Remove the class + register call from `index.ts`, wire in the new function**

In `js/src/index.ts`: delete the `ShinyreactOutputBinding` class definition (the `class ShinyreactOutputBinding extends Shiny.OutputBinding { ... }` block) and the `Shiny.outputBindings.register(new ShinyreactOutputBinding(), "shinyreact.output");` line and its comment. Add an import near the other local imports:
```ts
import { registerShinyreactOutputBinding } from "./output-binding";
```
And replace the deleted register line with a call (keep it before the `installInlineSpecSeeding()` call):
```ts
registerShinyreactOutputBinding();
```
Also remove now-unused imports from `index.ts` that were only used by the class: `ShinyreactRenderer` (from `./renderer`), `getOrCreateRoot`/`hasRoot`/`unmountRoot` (from `./roots`), and the `Spec` type (from `./types`) if it is no longer referenced. (tsc in Step 3 will flag any that are still needed or any left dangling.)

- [ ] **Step 3: Verify lint and tests are green**

Run (from `js/`):
```bash
npm run lint && npx vitest run
```
Expected: tsc no errors (no unused imports, no missing symbols); all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add js/src/output-binding.ts js/src/index.ts
git commit -m "refactor(js): extract ShinyreactOutputBinding into output-binding.ts (#54)"
```

---

### Task 3: Extract `global.ts` and reduce `index.ts` to a boot sequence

Move the `Window.shinyreact` declaration and assignment into `global.ts` behind an explicit `installGlobal()`.

**Files:**
- Create: `js/src/global.ts`
- Modify: `js/src/index.ts` (becomes ~8 lines)

- [ ] **Step 1: Create `js/src/global.ts`**

```ts
import React from "react";
import * as ReactDOM from "react-dom/client";
import type { ComponentRegistry } from "./types";
import { registerComponents } from "./registry";
import { ShinyOutput } from "./shiny-output";
import { seedInlineSpecs } from "./inline-spec";

// Re-export @posit/shiny-react hooks and components.
//
// We bundle @posit/shiny-react and React into this single IIFE so that:
// 1. All code shares a single React instance (React hooks break with multiple Reacts)
// 2. Downstream component authors get hooks via window.shinyreact.*
// 3. Downstream ESM builds can externalize React to window.shinyreact.React/ReactDOM
import {
  useSetShinyInput,
  useShinyBusy,
  useShinyInput,
  useShinyInputValue,
  useShinyOutputStatus,
  useShinyOutputValue,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
} from "./shiny-react";

// Extend window with shinyreact's public global API
declare global {
  interface Window {
    shinyreact: {
      registerComponents: (
        catalog: unknown,
        registry: ComponentRegistry,
      ) => void;
      useSetShinyInput: typeof useSetShinyInput;
      useShinyBusy: typeof useShinyBusy;
      useShinyInput: typeof useShinyInput;
      useShinyInputValue: typeof useShinyInputValue;
      useShinyOutputStatus: typeof useShinyOutputStatus;
      useShinyOutputValue: typeof useShinyOutputValue;
      useShinyMessageHandler: typeof useShinyMessageHandler;
      useShinyInitialized: typeof useShinyInitialized;
      ImageOutput: typeof ImageOutput;
      MISSING: typeof MISSING;
      ShinyModuleProvider: typeof ShinyModuleProvider;
      ShinyReactComponentElement: typeof ShinyReactComponentElement;
      ShinyOutput: typeof ShinyOutput;
      seedInlineSpecs: typeof seedInlineSpecs;
      React: typeof React;
      ReactDOM: typeof ReactDOM;
    };
  }
}

/**
 * Expose the public global API at `window.shinyreact`. Called once at bundle
 * boot. Preserves any pre-bundle assignment (e.g. `window.shinyreact._restore`
 * set by the head <script> emitted from Python's `_restore_script_tag`).
 */
export function installGlobal(): void {
  window.shinyreact = Object.assign(window.shinyreact || {}, {
    registerComponents,
    useSetShinyInput,
    useShinyBusy,
    useShinyInput,
    useShinyInputValue,
    useShinyOutputStatus,
    useShinyOutputValue,
    useShinyMessageHandler,
    useShinyInitialized,
    ImageOutput,
    MISSING,
    ShinyModuleProvider,
    ShinyReactComponentElement,
    ShinyOutput,
    seedInlineSpecs,
    React,
    ReactDOM,
  });
}
```

- [ ] **Step 2: Rewrite `js/src/index.ts` as the boot sequence**

Replace the entire contents of `js/src/index.ts` with:
```ts
import "./shinyreact.css"; // side-effect import is how Vite bundles CSS — no alternative

import { installGlobal } from "./global";
import { registerShinyreactOutputBinding } from "./output-binding";
import { installInlineSpecSeeding } from "./inline-spec";

installGlobal();
registerShinyreactOutputBinding();
installInlineSpecSeeding();
```

- [ ] **Step 3: Verify lint and tests are green**

Run (from `js/`):
```bash
npm run lint && npx vitest run
```
Expected: tsc no errors; all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add js/src/global.ts js/src/index.ts
git commit -m "refactor(js): extract window.shinyreact wiring into global.ts (#54)"
```

---

### Task 4: Update `shiny.d.ts` comment, rebuild dist, final verification

Tidy the stale doc reference and refresh the committed bundle copies.

**Files:**
- Modify: `js/src/shiny.d.ts` (doc comment only)
- Regenerate: `js/dist/`, `pkg-py/src/shinyreact/www/`, `pkg-r/inst/lib/shiny/`

- [ ] **Step 1: Update the doc comment in `shiny.d.ts`**

In `js/src/shiny.d.ts`, change the comment line:
```
 * Used only by the output binding in index.ts.
```
to:
```
 * Used only by the output binding in output-binding.ts.
```

- [ ] **Step 2: Verify lint and tests once more**

Run (from `js/`):
```bash
npm run lint && npx vitest run
```
Expected: tsc no errors; all tests PASS.

- [ ] **Step 3: Confirm build output is byte-similar to baseline**

Run (from repo root):
```bash
cd js && npm run build && shasum dist/shinyreact.js && cd ..
```
Expected: build succeeds. Compare against `BASELINE_HASH` from the baseline step. If hashes differ, confirm the difference is module-ordering/internal-only:
```bash
git diff --stat js/dist/shinyreact.js
```
Expected: either no diff, or a small diff attributable to bundler source ordering — no change to runtime behavior, exported names, or the `window.shinyreact` surface. If the diff shows substantive logic changes, stop and investigate.

- [ ] **Step 4: Refresh the Python and R bundle copies**

Run (from repo root):
```bash
make update-dist
```
Expected: rebuilds JS and copies into `pkg-py/src/shinyreact/www/` and `pkg-r/inst/lib/shiny/`.

- [ ] **Step 5: Commit**

```bash
git add js/src/shiny.d.ts js/dist pkg-py/src/shinyreact/www pkg-r/inst/lib/shiny
git commit -m "refactor(js): point shiny.d.ts comment at output-binding.ts; rebuild dist (#54)"
```

---

## Self-Review

**Spec coverage:**
- Proposal 1 (extract OutputBinding) → Task 2. ✓
- Proposal 2 (`spec.ts` → `types.ts`) → Task 1. ✓
- Proposal 4 (`global.ts` wiring) → Task 3. ✓
- `shiny.d.ts` comment update → Task 4. ✓
- Explicit install/register fns, no import side-effects (except CSS) → Tasks 2 & 3 use exported functions; `index.ts` in Task 3 Step 2 calls them. ✓
- Verification: byte-similar build, lint, vitest, `make update-dist` → Task 4. ✓
- Out-of-scope items (shiny-react/, vite.config, exported type names) → untouched by all tasks. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to" — every code step shows full content. ✓

**Type/name consistency:** `registerShinyreactOutputBinding` (defined Task 2, called Task 3), `installGlobal` (defined Task 3, called Task 3), `ShinyreactRenderer`/`getOrCreateRoot`/`hasRoot`/`unmountRoot` imported in `output-binding.ts` match `renderer.tsx`/`roots.ts` exports, `./types` import path matches Task 1 rename. ✓
