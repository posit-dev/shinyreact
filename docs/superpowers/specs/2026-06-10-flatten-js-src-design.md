# Flatten and reorganize `js/src/` TS files

**Issue:** [#54](https://github.com/posit-dev/shinyreact/issues/54)
**Date:** 2026-06-10
**Type:** Refactor only — no public API change. The IIFE bundle output and `window.shinyreact` surface stay identical.

## Goal

Every top-level file under `js/src/` states its responsibility in one sentence, and `index.ts` reads as a boot sequence rather than a kitchen sink.

## Background — what the issue already got, and what's left

Issue #54's "Current layout" snapshot is stale; the directory evolved since it was filed. Status of its five proposals:

| # | Proposal | Status |
|---|----------|--------|
| 1 | Extract `ShinyreactOutputBinding` + roots WeakMap | **Partial** — `roots.ts` already extracted; the binding class still lives in `index.ts` |
| 2 | Rename `spec.ts` → `types.ts` | **Not done** — `spec.ts` is still pure TS types |
| 3 | Colocate/consolidate the test | **Done** — a top-level `js/src/__tests__/` holds all three test files |
| 4 | Group global wiring into `global.ts` | **Not done** — `declare global` block + `window.shinyreact =` assignment still in `index.ts` |
| 5 | Vendored `shiny-react/` | Out of scope (un-vendoring is downstream of [#28](https://github.com/posit-dev/shinyreact/issues/28); reorganizing it in place is explicitly excluded) |

This spec executes the remaining actionable work: **proposals 1, 2, and 4.**

## Design

### Target file layout

```
js/src/
  index.ts          entry point — boot sequence only (~8 lines)
  global.ts         declares Window.shinyreact + installGlobal() assigns window.shinyreact (the public global API)
  output-binding.ts ShinyreactOutputBinding class + registerShinyreactOutputBinding()
  types.ts          (was spec.ts) wire-tree TS types: Element, Spec, ComponentRegistry, …
  registry.ts       component registry (unchanged)
  roots.ts          React-root-per-element WeakMap (unchanged)
  renderer.tsx      wire-tree → React walker (unchanged)
  inline-spec.tsx   static-mount seeding + observer (unchanged)
  shiny-output.tsx  <ShinyOutput> component (unchanged)
  shiny.d.ts        ambient Shiny global decls (doc comment updated to point at output-binding.ts)
  shinyreact.css    (unchanged)
  __tests__/        (unchanged — proposal 3 already satisfied)
  shiny-react/      (untouched — out of scope, #28)
```

### What moves where

**1. `output-binding.ts` (new)** — the `ShinyreactOutputBinding` class, currently `index.ts:84–112`. Exports a `registerShinyreactOutputBinding()` function that performs the `Shiny.outputBindings.register(new ShinyreactOutputBinding(), "shinyreact.output")` call. The class itself need not be exported unless a test wants it. Imports `Spec` from `./types`, `ShinyreactRenderer` from `./renderer`, and `getOrCreateRoot` / `hasRoot` / `unmountRoot` from `./roots`.

**2. `global.ts` (new)** — owns the `declare global { interface Window { shinyreact: {...} } }` block and the "why we bundle React into one IIFE" doc comment that explains it. Exports `installGlobal()`, which performs the `window.shinyreact = Object.assign(window.shinyreact || {}, { … })` assignment (preserving any pre-bundle assignment such as `window.shinyreact._restore`). Imports the re-exported hooks from `./shiny-react`, plus local `registerComponents`, `ShinyOutput`, `seedInlineSpecs`, `React`, `ReactDOM`.

**3. `types.ts` (renamed from `spec.ts`)** — `git mv spec.ts types.ts`. Exported type *names* are unchanged (`Element`, `Spec`, `ComponentElement`, `TagElement`, `TextElement`, `HtmlElement`, `RegisteredComponentProps`, `ComponentRegistry`). Update the import path in the five importers:
- `renderer.tsx`
- `inline-spec.tsx`
- `registry.ts`
- `index.ts` (the `Spec` import disappears entirely once the binding moves out; verify after extraction)
- `__tests__/renderer.test.tsx` (`../spec` → `../types`)

**4. `shiny.d.ts`** — update the doc comment ("Used only by the output binding in index.ts") to reference `output-binding.ts`. No declaration changes.

### Resulting `index.ts`

```ts
import "./shinyreact.css"; // side-effect import is how Vite bundles CSS — no alternative

import { installGlobal } from "./global";
import { registerShinyreactOutputBinding } from "./output-binding";
import { installInlineSpecSeeding } from "./inline-spec";

installGlobal();
registerShinyreactOutputBinding();
installInlineSpecSeeding();
```

### Design decisions

- **No import-time side effects for our own modules.** Both `installGlobal()` and `registerShinyreactOutputBinding()` are explicit exported functions called from `index.ts`, so the boot order is visible at the entry point rather than hidden in import statements. (The `shinyreact.css` import is the one unavoidable side-effect import — it is how Vite includes the stylesheet in the bundle; there is no function-call equivalent.)
- **`installGlobal()` runs before `registerShinyreactOutputBinding()`** to preserve today's ordering (global assignment first, then binding registration, then inline-spec seeding). The seeding-last order matters for the `#123` registry-completeness reasoning already documented in `inline-spec.tsx`.

## Out of scope

- Any change to the IIFE entry point's external behavior or `window.shinyreact` surface.
- Changes to `vite.config.ts` / how the bundle is built.
- Anything inside `js/src/shiny-react/` (vendored upstream, #28).
- Renaming exported types (`Spec`, `Element`, `ComponentRegistry`, …) — only the file holding them is renamed.

## Verification

- `make js-build` produces a byte-similar `js/dist/shinyreact.js` (modulo bundler-internal source ordering); IIFE behavior and `window.shinyreact` surface identical.
- `make js-lint` (tsc `--noEmit`) passes.
- `cd js && npx vitest run` passes with no test logic changes beyond the one `../spec` → `../types` import path.
- Manual read: `index.ts` is a short boot sequence; each top-level `js/src/` file's responsibility is statable in one sentence (see layout table).
- After building, run `make update-dist` so `pkg-py/src/shinyreact/www/` and `pkg-r/inst/lib/shiny/` pick up the rebuilt bundle (even though it should be byte-similar).
