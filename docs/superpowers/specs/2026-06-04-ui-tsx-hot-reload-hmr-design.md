# Hot reloading for the `ui.tsx` pattern (React Fast Refresh)

**Issue:** [#132](https://github.com/posit-dev/shinyreact/issues/132)
**Date:** 2026-06-04
**Status:** Design approved, pending spec review

## Problem

App authors want development-time hot reloading. The issue names three cases:

1. **`app.py` pattern (traditional).** Shiny's `--reload` restarts the server on
   `.py` changes; the browser reconnects. This already works — no work needed
   beyond documentation.
2. **`ui.tsx` no-build (`www/app.js` written by hand).** The file is served
   statically and picked up on the next browser load; editing `.py` triggers
   Shiny `--reload`. Works today; documentation only.
3. **`ui.tsx` bundled (`src/ui.tsx` → Vite).** Today `vite build --watch`
   rewrites `www/app.js`, Shiny autoreload sees the change, and the browser does
   a **full page reload**. The author wants a **partial refresh** — React Fast
   Refresh / HMR, "something that react.js apps can do today."

Case 3 is the substance of this issue. True Fast Refresh requires the Vite **dev
server** to serve the module graph; Vite *library mode* (what the examples build
with) cannot do HMR.

## Scope

- **Deliverable:** one new worked example plus a short README/doc proving HMR
  works against a Shiny-served page, with the dev-vs-prod swap contained entirely
  in the example's `vite.config`.
- **JS-only.** No changes to the Python (`set_react_page`) or R
  (`page_react_html`) packages. The mechanism lives in *the user's build*, so it
  works identically for both backends for free.
- **Two separate commands.** `npm run dev` (Vite dev server) and `shiny run`
  (Shiny) in two terminals — no single-command wrapper.
- **Out of scope (future follow-up):** any shipped backend dev switch, a
  `shinyreact dev` CLI launcher, or a single command that wraps both processes.
  Cases 1 and 2 need no code — only a documentation note that they already
  reload.

## Key constraints discovered in the codebase

- `set_react_page` (`pkg-py/src/shinyreact/_page.py`) and `page_react_html`
  (`pkg-r/R/page.R`) **read `index.html` once at startup** and inject the
  shinyreact `HTMLDependency` into `<head>` (which defines `window.shinyreact`).
  Per issue #82, editing `index.html` requires a server restart. **Therefore the
  dev switch must not live in `index.html`.**
- Every other file under `www/` (including `app.js`) **is served statically and
  picked up live** with no restart. This is the swap point.

## Architecture

Two long-running processes; the browser talks to both:

```
┌─────────── browser ───────────┐
│  page from Shiny (:8000)       │
│   <head> shinyreact.js  ───────┼──> window.shinyreact (React, hooks, output binding)
│   <body> www/app.js (module)   │
│            │                   │
│   ┌────────┴─ DEV ──────────┐  │
│   │ app.js = stub that      │  │   HMR / Fast Refresh over Vite's own WS
│   │ imports @vite/client +  ─┼──┼──> Vite dev server (:5173)
│   │ src/ui.tsx from :5173   │  │
│   └─────────────────────────┘  │
│   reactive values / outputs ───┼──> Shiny WebSocket (:8000, same origin)
└────────────────────────────────┘
```

- **Shiny (:8000)** always serves the page and the reactive WebSocket. Unchanged.
- **Vite dev server (:5173)** serves the React module graph with Fast Refresh —
  only in dev.
- The page's WebSocket to Shiny is **same-origin** (the page was served by
  :8000), so reactivity is unaffected by the cross-origin module load. Vite's
  HMR socket is a separate connection to :5173. No CORS entanglement on the
  Shiny side.
- **Two kinds of reload coexist and that is expected:** editing `.tsx` → Vite
  Fast Refresh (partial, state-preserving); editing `app.py` → Shiny `--reload`
  restart → browser reconnect (full).

## Mechanism: the dev-stub swap

A small **Vite plugin in the example's `vite.config`** owns both modes.

- **`npm run build`** → `vite build` → real bundle at `www/app.js` (today's
  behavior).
- **`npm run dev`** → `vite` dev server on `:5173`, plus the plugin writes a stub
  to `www/app.js` when the dev server starts:

  ```js
  // www/app.js — generated in dev (gitignored, like the built bundle)
  import "http://localhost:5173/@vite/client";
  import "http://localhost:5173/src/ui.tsx";
  ```

`index.html` is written once and never swapped across modes:

```html
<script type="module" src="app.js"></script>
```

`type="module"` is the only requirement — it loads the real bundle *and* the stub
identically. Because Shiny serves `app.js` statically, the swap is picked up with
no restart, and `index.html` (read-once, restart-bound per #82) is never touched.

**Script ordering:** `shinyreact.js` is hoisted to `<head>` with `defer` and runs
before the body's module script, so `window.shinyreact` exists before the entry
imports React.

**Production entry format:** `index.html` always uses `type="module"`. The
production bundle must therefore be loadable as a module script (build as ESM, or
confirm the IIFE output executes correctly when loaded as a module). The plan
should settle the build `format` so dev and prod share one `index.html`.

## React-singleton handling in dev

The production config externalizes React to the shared global:

```js
rollupOptions: {
  external: ["react", "react-dom", "react-dom/client"],
  output: { globals: { react: "window.shinyreact.React", /* … */ } },
}
```

`output.globals` is **build-only** — it does nothing for the dev server. In
`serve` mode the dev modules (and `@vitejs/plugin-react`'s Fast Refresh runtime)
would otherwise resolve their own copy of React, and the `window.shinyreact`
hooks — which dispatch against the IIFE's React — would throw "invalid hook
call" / dual-React errors.

Dev therefore needs an equivalent: a `resolve.alias` active only when
`command === "serve"`, mapping `react` / `react-dom` / `react-dom/client` to a
tiny shim module that re-exports from `window.shinyreact.React` /
`window.shinyreact.ReactDOM`. This keeps a single React instance across the IIFE
and the HMR'd modules.

This aliasing is the part most likely to need a **small spike early in
implementation** — named-export enumeration for the shim and Fast Refresh runtime
resolution are the unknowns.

## Example

A new minimal example: **`examples/ui-tsx/08-hmr`** (number to be confirmed
against the current example list at implementation time).

- A counter whose state visibly **survives** a `.tsx` edit — the whole point is
  to demonstrate Fast Refresh, so state preservation is front-and-center.
- Carries the reference `vite.config` (the stub plugin + the serve-mode alias)
  that other authors copy.
- `www/app.js` is gitignored (generated by either `build` or `dev`).
- README documents the two-terminal workflow and a manual "verify HMR" checklist.

## Testing

HMR is flaky to drive end-to-end in CI, so:

- **Automated (JS-land):** assert the dev-mode plugin writes the expected
  `www/app.js` stub, and that `npm run build` still produces a working bundle.
- **Manual / documented:** a README "verify HMR" checklist — edit the counter's
  label, watch it update with the count intact, no full reload. No Playwright HMR
  test in CI.

## Documentation

- New example README (workflow + verify-HMR checklist).
- A note in `docs/app-py-vs-ui-tsx.md` (dev-workflow section) that cases 1 and 2
  already reload, and pointing case 3 at the new example.
- Remove/replace the corresponding entry in `docs/todos.md` if present.

## Future follow-ups (explicitly not in this issue)

- A shipped `shinyreact` dev helper or CLI that automates the stub + alias so
  authors don't copy `vite.config` boilerplate.
- A single `dev` command wrapping both processes.
- R-side parity is automatic (JS-only), but an R example could mirror the Python
  one later.
