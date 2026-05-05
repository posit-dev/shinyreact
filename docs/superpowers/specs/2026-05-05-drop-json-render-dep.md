# Drop `@json-render/react` dependency

**Date:** 2026-05-05
**Status:** Proposal — pending decision
**Related:** #37 (retire shinyjsonold), #38 (rename → shinyreact), #44 (SPA vs traditional docs), DESIGN.md §326–351

## Summary

Replace the `@json-render/core` + `@json-render/react` (Vercel Labs, pre-1.0) dependency with an in-house ~30-LOC recursive Spec renderer. The dep ships ~3,500 LOC and ~50 public exports; we use 4 of them. Every feature it offers beyond the `Renderer` component duplicates a model Shiny already owns.

## Context

`shinyjson` must continue to support, in addition to the new SPA-first model:

- **Legacy `shinyjsonold`** — Python builds a `Spec`, the JS bundle renders it as React.
- **Hybrid Shiny apps** — e.g. `examples/9-blended`, `examples/16-shadcn`, where Python emits a Spec containing element types whose React implementations live in a downstream package's bundle.

The `@json-render/react` package powers the Spec → React tree step in both modes.

### What we actually use

From `js/src/renderer.tsx` and `js/src/index.ts`:

| Import | Source | Purpose |
|---|---|---|
| `Renderer` | `@json-render/react` | Walks the Spec, calls registered components |
| `JSONUIProvider` | `@json-render/react` | Combines state / action / validation / visibility contexts |
| `ComponentRegistry` (type) | `@json-render/react` | `Record<string, ComponentType<{element, children, ...}>>` |
| `Spec` (type) | `@json-render/core` | Flat map of `{ root, elements }` |

Four imports. That is the entire surface area.

### What we ship but do not use

Each of these is loaded into every shinyjson page and is functionally redundant with Shiny:

- **State model** — `StateProvider`, `useStateStore`, `useStateValue`, `useBoundProp`, `$bindState`, `$bindItem`. Shiny owns reactive state via `useShinyInput` / `useShinyOutput`.
- **Actions** — `ActionProvider`, `useAction`, `ConfirmDialog`, action bindings, navigation. Shiny owns event dispatch via `useShinyInput` with `priority: "event"` and via `@reactive.event`.
- **Repeat / visibility / computed** — `RepeatScopeProvider`, `VisibilityProvider`, `$computed`. Specs from Python already render the final tree; there is no client-side template language.
- **AI streaming** — `useUIStream`, `useChatUI`, `buildSpecFromParts`, `getTextFromParts`, `useJsonRenderMessage`. Shiny streams over a websocket; partial-update support, when added (#36), will be JSON-Patch over Shiny's existing channel — not LLM token streams.
- **Catalog tooling** — `defineRegistry`, `createRenderer`, schema inference helpers.

`@json-render/react` is, per its own README, a **generative UI framework** for AI-streamed interfaces. The framing is the right marketing, wrong substrate, for `shinyjson`: Shiny is the generative source, the wire is the websocket, and reactive state belongs on the server.

### What is genuinely useful but unused today

- **`ValidationProvider` / `useFieldValidation`** — client-side form validation with touched/validated/result state, custom catalog-defined validation functions, and field-level lifecycle hooks. Shiny's server-side validation works but pays a websocket round-trip per keystroke; client-side field validation is the kind of capability a downstream `shinyshadcn`-style forms package would plausibly want. We don't use it today, but it's the one part of the dep that isn't trivially redundant with Shiny's own model.

  This is a real cost of dropping the dep. Mitigations: (a) most downstream form packages will want their own validation primitives anyway (zod, react-hook-form, etc.) and won't rely on json-render's; (b) if we later need it, ~150 LOC of context + hook code can be vendored from json-render's source under its Apache-2.0 license without re-adding the entire dep.

## Proposal

### What we keep

- The component registry concept and `window.shinyjson.registerComponents(catalog, registry)` entry point — already implemented in `js/src/registry.ts`, no dep change needed.
- The `Spec` / `Element` shape — already owned in `pkg-py/src/shinyjsonold/_spec.py` and consumed by downstream packages. Mirror as a TypeScript type in `js/src/spec.ts`.
- The `{ element, children }` arg shape passed to registered components — preserves source compatibility for `examples/9-blended`, `examples/15-columns-shadcn`, `examples/16-shadcn`, and any downstream package authored against the current API.

### What we replace

`js/src/renderer.tsx` becomes a ~30-LOC recursive function:

```ts
function renderNode(id: string, spec: Spec, registry: Registry): ReactNode {
  const el = spec.elements[id];
  if (!el) return null;
  const Comp = registry[el.type] ?? el.type;
  const children = (el.children ?? []).map((cid) =>
    typeof cid === "string" ? renderNode(cid, spec, registry) : cid,
  );
  // Registered components receive { element, children }; intrinsic tags receive props + children directly.
  return typeof Comp === "string"
    ? React.createElement(Comp, el.props, ...children)
    : React.createElement(Comp, { element: el, children, key: id });
}
```

`JSONUIProvider` is removed entirely — none of its contexts are wired to anything we use.

### What we drop

- `@json-render/core`
- `@json-render/react`
- The transitive bundle weight of state/action/validation/streaming subsystems.

## Approach options

**A. Drop the dep now; verify hybrid + legacy + shadcn examples render identically.** *(Recommended.)*

- Pros: immediate bundle reduction, removes labs-tier (pre-1.0, single-vendor) supply-chain dependency, full control over edge cases (missing `type`, empty `children`, intrinsic vs registered components), no API drift to track.
- Cons: one-time migration; we own renderer correctness — small, but ours.

**B. Keep the dep indefinitely.**

- Pros: `ValidationProvider` available the moment a downstream forms package wants it; future `$bindState` / generative streaming capability if `shinyjson` ever adopts LLM-driven UI generation.
- Cons: ships ~3,500 LOC for one feature we don't use yet and several we never will. The state/action/streaming subsystems conflict directly with Shiny's model — keeping them in the bundle creates two ways to do the same thing for downstream package authors to disambiguate.

## Recommendation

**Option A.** Frame the work as "drop after we confirm the three hybrid/shadcn/legacy paths render identically with our own walker." If parity holds, drop the dep. If anything in those examples fails to migrate trivially, the parity-blocking case becomes its own scoped issue rather than a reason to keep the dep.

## Risk and migration

- **Verification scope:** `examples/9-blended`, `examples/15-columns-shadcn`, `examples/16-shadcn`, and the legacy `shinyjsonold` snapshot tests in `pkg-py/tests/old/`.
- **Source compatibility for downstream packages:** preserved — registered components continue to receive `{ element, children }`.
- **Type compatibility:** `ComponentRegistry` becomes a local type alias with the same shape.
- **Bundle delta:** report before/after `js/dist/shinyjson.js` size in the PR.

## Acceptance

- `@json-render/core` and `@json-render/react` removed from `js/package.json` and `js/package-lock.json`.
- `js/src/renderer.tsx` and `js/src/registry.ts` no longer import from `@json-render/*`.
- `js/src/spec.ts` defines `Spec`, `Element`, and `ComponentRegistry` locally.
- All examples in `examples/` render identically (manual visual check + any existing snapshot tests).
- `pkg-py/tests/old/` passes unchanged or with reviewed snapshot diffs.
- Bundle size delta reported in the PR description.

## Future direction: client-side state model (deliberate non-goal for now)

`@json-render/react` ships a substantial client-side state model — JSON Pointer paths, `$state` / `$bindState` / `$bindItem` / `$cond` / `$template` / `$computed` expressions, repeat scopes, and a pluggable `StateStore`. We do not use any of it today; every example, including the hybrid ones, declares state through `useShinyInput` (server-observable) and `useState` (component-internal). This proposal does not adopt the state model and does not preserve it.

This section records what we'd be giving up and why we're choosing to give it up *now* without closing the door on it.

### What the state model would buy us

- **Two components sharing UI state without a server round-trip.** Today the only path between components is through Shiny inputs. With `$bindState`, a `<Wizard>`'s current step and a `<StepIndicator>`'s display can share `/step` purely client-side.
- **State usage as part of the component contract.** The currently-unused `catalog` argument to `registerComponents(catalog, registry)` is the natural place for components to declare which props bind, which paths they own internally, and what shape the state takes — making collisions detectable at registration time instead of "silent, last writer wins."
- **Spec-author-controlled client state.** A Python author could wire ephemeral UI state (active tab, accordion open/closed, drag position) through Spec JSON without writing JS.

### Why we're not adopting it now

- **It's not preservation, it's a new direction.** Keeping the dep doesn't enable any of the above by itself. We'd still need to design the catalog format, the path-to-Shiny-input bridge convention, and the namespacing rules for component-internal paths. The dep is sitting in the bundle waiting for a design decision that hasn't been made.
- **The integration shape is unsettled.** Three plausible shapes: (1) local store coexisting with `useShinyInput`, (2) `StateStore` backed entirely by Shiny inputs (every binding round-trips), (3) hybrid prefix routing (`/shiny/...` vs `/local/...`). Each has real trade-offs and none has been chosen.
- **Re-adoption is cheap if and when we commit.** The package is Apache-2.0; we can re-add the dep, or vendor the relevant ~500 LOC (binding resolver, path engine, contexts), at the moment we decide which integration shape to ship. Keeping it now buys an option whose strike price we haven't priced.

### What we lose by dropping now

- The declarative binding syntax in Spec JSON. Component authors continue to coordinate state via `useShinyInput` (round-trips) or document-level conventions (no round-trip but no machine-checkable contract).
- Forward compatibility with any downstream package that started leaning on `$bindState` / `useStateStore`. None do today.

If a concrete use case for client-side shared state surfaces, file a follow-up issue with a proposed integration shape (1/2/3 above). At that point we revisit re-adopting or vendoring.

## Out of scope

- JSON Patch wire format for partial updates — tracked in #36.
- Renaming `shinyjson` → `shinyreact` — tracked in #38.
- Retiring `shinyjsonold` — tracked in #37. This proposal is independent: dropping the dep is valuable whether or not `shinyjsonold` retires.
