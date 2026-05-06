# Merge `shinyjsonold` back into a renamed `shinyreact`

**Date:** 2026-05-05
**Status:** Design — awaiting implementation plan
**Related issues:** #38 (rename), #44 (docs), #37 (closed: retire `shinyjsonold` — reversed by this design), #51 (rename `render_json` — superseded)

## Summary

Replace the two-package split (`shinyjson` SPA-first + `shinyjsonold` JSON-spec) with a single package, `shinyreact`, that ships **both** patterns as first-class options. Pursue the rename in #38 without retiring the traditional pattern, and clear the way for the comparison docs in #44.

## Motivation

The current split assumes the SPA-first prototype will eventually subsume the traditional JSON-spec model (see #37's exit criteria). That assumption no longer holds: the traditional pattern is a legitimate, valuable option for users who don't want a client-side build step or who are writing form/report-style apps. Shipping two PyPI packages indefinitely would bloat the test matrix, fragment docs, and force users to pick a package before they understand the patterns.

One package with both patterns under one name lets users learn the *patterns* (not the package landscape) and pick per-app.

## Goals

- One PyPI package: `shinyreact`. Zero references to `shinyjson` or `shinyjsonold` in code.
- Both patterns supported as peers — neither is the "main" path.
- A unified server decorator that handles both `Spec`/`Node` trees (traditional) and plain JSON (SPA).
- Clean wire-protocol naming so server-side names mirror client-side hooks.
- Examples organized by pattern.

## Non-goals

- R package work (still a placeholder).
- Renaming `Spec`, `Node`, `Element`, `SpaApp`, or `page_react` — only renames driven by name collisions land here.
- Typed-contract work in #30 / #50.
- Performance changes.
- Any compatibility shim or alias inside `shinyreact`.

## Public Python API: `shinyreact`

Flat namespace. No aliases. No `shinyjson` or `shinyjsonold` references anywhere.

| Symbol | Origin | Purpose |
|---|---|---|
| `SpaApp` | from new `shinyjson` | SPA-first app constructor |
| `page_react` | from `shinyjsonold` | Traditional page constructor |
| `page_bare` | from `shinyjsonold` | Bare page variant |
| `page_react_dep` | from `shinyjsonold` | The shared `HTMLDependency` |
| `ui_output` | from `shinyjsonold` | Output container `<div class="shinyreact-output">`; accepts `extra_deps` for downstream JS/CSS injection |
| `reactive_output` | **unified (new)** | Server decorator; see below |
| `send_message` | **renamed** | Server→client custom message; pairs with `useShinyMessageHandler` |
| `Spec`, `Node`, `Element` | from `shinyjsonold` | JSON-spec data model |

### `reactive_output` — unified decorator

Replaces both `shinyjson.render_json` and `shinyjsonold.render`.

- Accepts `Spec | Node | Jsonifiable`.
- `Spec` → flattened via `Spec.to_dict()`.
- `Node` → flattened via `Node.to_spec().to_dict()`.
- Other `Jsonifiable` → passed through unchanged (consumed by `useShinyOutput()` on the client).
- Implements `auto_output_ui()` so Express mode auto-generates `ui_output(id)` for traditional apps. Harmless in `SpaApp` (which doesn't use Express's auto-UI machinery).
- **No `extra_deps`** attribute or class hook. Downstream packages (e.g. `shinyshadcn`) inject their JS/CSS through `ui_output(id, extra_deps=[...])` on the UI side, which already supports it.

Shape:

```python
class reactive_output(Renderer[Spec | Node | Jsonifiable]):
    async def transform(self, value): ...
    def auto_output_ui(self) -> Tag: ...
```

### `send_message` — renamed wire helper

Replaces both `shinyjson.send_json` and `shinyjsonold.post_message` (which were byte-identical except for name). Same signature: `send_message(session, type, data)`. Wire protocol unchanged: `shinyReactMessage` custom message with `{type, data}`.

The new name pairs the server side with the client hook (`useShinyMessageHandler`). `post_message` was misleading (no `window.postMessage` involvement). `send_json` was inconsistent with the JS message vocabulary.

## JS-side renames (clean swap, no aliases)

| Old | New |
|---|---|
| `window.shinyjson` | `window.shinyreact` |
| `class="shinyjson-output"` (OutputBinding selector) | `class="shinyreact-output"` |
| `HTMLDependency(name="shinyjson", ...)` | `HTMLDependency(name="shinyreact", ...)` |
| `js/src/shinyjson.css` | `js/src/shinyreact.css` |
| `js/dist/shinyjson.js` | `js/dist/shinyreact.js` |
| `pkg-py/src/shinyjson/www/` | `pkg-py/src/shinyreact/www/` |

## Repo layout

- `pkg-py/src/shinyjson/` and `pkg-py/src/shinyjsonold/` merge into `pkg-py/src/shinyreact/`.
- `pkg-py/tests/` and `pkg-py/tests/old/` merge into `pkg-py/tests/`. Subdivide by pattern (`tests/spa/`, `tests/traditional/`) if and only if it improves navigability — flat is fine if it does.
- `pkg-py/examples/` reorganized into `pkg-py/examples/traditional/` and `pkg-py/examples/spa/`. Numeric prefixes dropped or restarted inside each subdir. Every example imports `shinyreact`.
- `pyproject.toml`: `name = "shinyreact"`; hatchling package path `pkg-py/src/shinyreact`.
- `Makefile` paths updated; targets keep their existing names.
- `pkg-r/inst/lib/shiny/` continues to track the JS bundle (filename now `shinyreact.js`).

## Migration (hard cut)

No compatibility shims inside `shinyreact`. The package is fresh:

1. **Final `shinyjson` release on PyPI.** Deprecation-only version. README and import-time message say "renamed and merged into `shinyreact`; install that." No re-exports.
2. **Final `shinyjsonold` release on PyPI.** Same treatment.
3. **First `shinyreact` release on PyPI.** Full new API, no aliases.
4. **Single migration doc** covers all renames in one place:
   - Package: `shinyjson` / `shinyjsonold` → `shinyreact`.
   - Decorators: `render_json`, `render` → `reactive_output`.
   - Function: `post_message`, `send_json` → `send_message`.
   - JS: `window.shinyjson` → `window.shinyreact`; `shinyjson-output` → `shinyreact-output`; `HTMLDependency` name.

## Docs

- `docs/spa-vs-traditional.md` (delivers #44). Lands as part of this work — the merged package is the place where the two-pattern comparison makes sense. Examples link from each pattern's section into `examples/traditional/` and `examples/spa/`.
- `docs/features.md` and `docs/features-shinyjson-old.md` collapse into one `docs/features.md`, organized by pattern.
- `docs/todos.md` rewritten: drop entries about retiring `shinyjsonold`; rename references.
- `CLAUDE.md`, `DESIGN.md`, `decisions/*` — `shinyjson` / `shinyjsonold` references rewritten to `shinyreact`. `DESIGN.md` §1 / §8 reframed: SPA-first is no longer "the prototype that may replace the JSON-spec model"; both are first-class.

## Open-issue updates

This is part of the deliverable, not a follow-up:

- **#38** — restate: rename happens; the traditional pattern is *kept*. Trim retirement-related sections.
- **#37** (closed) — post a comment that the retirement track is reversed; link this design. Leave closed (no action) or reopen-and-close-with-reason — pick whichever GitHub flow keeps history cleanest.
- **#51** — mark superseded by this design: `reactive_output` is now the unified decorator with the broader `Spec | Node | Jsonifiable` signature, not just a rename.
- **#44** — update naming references; note this work delivers the doc directly.
- **#33, #34** — update to `shinyreact` and the merged-pattern reality.
- **#27, #28, #30, #31, #32, #35, #36, #39, #49, #50** — pure rename pass: `shinyjson` / `shinyjsonold` → `shinyreact`, keeping semantics.

## Risks

- **Naming collision in user code.** Anyone with `import shinyjson as sj` must update. Hard cut means a PR-sized change for each downstream app. Acceptable: pre-1.0, small audience, single migration doc.
- **Downstream `extra_deps` extension hook removed from `reactive_output`.** Downstream packages must shift to `ui_output(id, extra_deps=[...])`. This is a deliberate API simplification: the decorator no longer mixes wire-format concerns with UI-dependency wiring.
- **Express auto-UI behavior depends on a `Spec | Node` payload at type-check time.** When the decorator returns plain JSON for `useShinyOutput`, Express still emits a container — but the container is unused. Document; don't add machinery to detect.

## Acceptance

- `pkg-py/src/shinyreact/` is the only Python package. `pkg-py/src/shinyjson/` and `pkg-py/src/shinyjsonold/` deleted.
- `grep -r shinyjson pkg-py/ pkg-r/ js/ docs/ decisions/ Makefile pyproject.toml CLAUDE.md DESIGN.md` returns nothing (other than the migration doc and historical commit log).
- `make py-check` and `make js-build` pass.
- All examples in `examples/traditional/` and `examples/spa/` run.
- `docs/spa-vs-traditional.md` exists and links to runnable examples in both subdirs.
- Listed open issues edited per the section above.
