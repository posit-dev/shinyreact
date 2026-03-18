# Integrate shiny-react module namespace support

**Date:** 2026-03-18
**Source PR:** https://github.com/wch/shiny-react/pull/3
**Status:** Approved

## Goal

Integrate `wch/shiny-react#3` (Shiny module namespace support) into shinyjson's vendored copy and bring the upstream examples as reference material.

## Context

shinyjson vendors `@posit/shiny-react` at `js/src/shiny-react/`. The upstream PR adds module namespace support so that multiple instances of the same React widget can coexist on a page without ID conflicts, matching Shiny's server-side `moduleServer` / `@module.server` pattern.

## Parts

### 1. Vendored shiny-react source changes

**New files in `js/src/shiny-react/`:**

- `ShinyModuleContext.tsx` — `ShinyModuleProvider` (React context provider), `useShinyModuleNamespace()` hook, `applyNamespace(id, namespace)` utility
- `ShinyReactComponentElement.tsx` — Base `HTMLElement` subclass for custom web elements that render React components. Handles slot preservation, `data-*` to props parsing, auto-`ShinyModuleProvider` wrapping, and Shiny `bindAll`/`unbindAll` lifecycle.

**Modified files in `js/src/shiny-react/`:**

- `use-shiny.ts` — `useShinyInput`, `useShinyOutput`, `useShinyMessageHandler` each gain an optional `namespace` in their options. Auto-reads from `ShinyModuleContext` if no explicit namespace. Uses `namespacedId` for all registry lookups and effect deps.
- `ImageOutput.tsx` — Same namespace pattern applied to the `id` prop and `clientdata_output_*` input IDs.
- `index.ts` — Adds exports: `ShinyModuleProvider`, `useShinyModuleNamespace`, `ShinyReactComponentElement`.

### 2. Python `post_message` fix

In `pkg-py/src/shinyjson/_post_message.py`, wrap the message type in `shiny.module.resolve_id()` so that messages sent inside a Shiny module are correctly namespaced. This is a one-liner and is backwards-compatible (`resolve_id` is a no-op outside module context).

### 3. Examples

Copy all content from the PR branch into `examples/shiny-react-upstream/`:

```
examples/shiny-react-upstream/
  README.md             # shiny-react README with PR changes
  1-hello-world/
  2-inputs/
  3-outputs/
  4-messages/
  5-shadcn/
  6-dashboard/
  7-chat/
  8-modules/            # New in PR
  9-blended/            # New in PR
```

Add `examples/shiny-react-upstream/*/www/` to `.gitignore`.

These are verbatim upstream copies. They use `@posit/shiny-react` as a local `file:` dependency and the copy-paste `shinyreact.py`/`shinyreact.R` helper pattern. They will not run as-is within shinyjson. They serve as reference material for future adaptation.

### 4. Build and export wiring

**`js/src/index.ts` global API additions:**

Expose on `window.shinyjson`:
- `ShinyModuleProvider` — downstream IIFE bundles wrap components in namespace providers
- `ShinyReactComponentElement` — downstream packages extend the base custom element class

**Build verification:**
1. `make js-build` — TypeScript compiles, Vite bundles
2. `make update-dist` — copy built assets to `pkg-py/` and `pkg-r/`
3. `make py-check` — Python type checking and tests pass

### 5. JavaScript unit tests

**Test framework:** Vitest + jsdom + `@testing-library/react`

- Vitest because the project already uses Vite
- jsdom for DOM environment (spec-compliant custom element support matters here)
- `@testing-library/react` for `renderHook()` and React component tests

**Dev dependencies to add in `js/package.json`:**
- `vitest`
- `@testing-library/react` (pulls in `@testing-library/dom`)

**Makefile target:** `make js-test`

**What to test:**

`applyNamespace` (pure function):
- `applyNamespace("count", "mod1")` returns `"mod1-count"`
- `applyNamespace("count", null)` returns `"count"`

`ShinyModuleContext` (React context):
- `ShinyModuleProvider` sets namespace, `useShinyModuleNamespace()` reads it
- Nested providers: inner namespace wins
- No provider: `useShinyModuleNamespace()` returns `null`

`use-shiny.ts` hooks (namespace integration):
- `useShinyInput` with explicit `namespace` option uses `namespace-id`
- `useShinyInput` inside `ShinyModuleProvider` auto-namespaces
- Explicit `namespace` overrides provider context
- Same patterns for `useShinyOutput` and `useShinyMessageHandler`

`ShinyReactComponentElement` (custom element, plain DOM tests):
- `getConfig()` parses `data-*` attributes (strings and JSON auto-parse)
- Element with `id` attribute wraps in `ShinyModuleProvider`
- Element without `id` renders without namespace wrapper
- Slot collection from `data-slot` children

## Decisions

- **Approach A chosen** over full upstream mirror (B) and pre-adapted examples (C). Keeps integration clean and scoped; examples land as reference for separate follow-up work.
- **jsdom over happy-dom** — small test suite where speed doesn't matter, but custom element spec compliance does.
- **`@testing-library/react` for hooks, plain DOM for custom elements** — right tool for each test category.
