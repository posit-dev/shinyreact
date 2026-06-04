# Hot reloading for the `ui.tsx` pattern (React Fast Refresh)

**Issue:** [#132](https://github.com/posit-dev/shinyreact/issues/132)
**Date:** 2026-06-04
**Status:** Design approved and **de-risking spike PASSED** (see "Spike results"
below). Approach A (bring-your-own dev React) delivers true Fast Refresh on a
Shiny-served page with no backend change. Ready for an implementation plan.

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
  // www/app.js — generated in dev (gitignored, like the built bundle).
  // Installs the React Fast Refresh preamble, then dynamically imports the HMR
  // client + entry. See "Spike results" for why the preamble + dynamic import
  // are mandatory.
  import RefreshRuntime from "http://localhost:5173/@react-refresh";
  RefreshRuntime.injectIntoGlobalHook(window);
  window.$RefreshReg$ = () => {};
  window.$RefreshSig$ = () => (type) => type;
  window.__vite_plugin_react_preamble_installed__ = true;
  await import("http://localhost:5173/@vite/client");
  await import("http://localhost:5173/src/ui.tsx");
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

## Constraint: `window.shinyreact.React` is a production React

The obvious dev approach — alias `react` → `window.shinyreact.React` so dev
modules share the one React instance — keeps a single instance, but it's the
**production** build:

- `js/vite.config.ts` hardcodes `define: { "process.env.NODE_ENV":
  JSON.stringify("production") }` and bundles React with no externals.
- The shipped `js/dist/shinyreact.js` contains only `"production"` and no
  `react-refresh` / `jsxDEV` markers.

React **Fast Refresh requires the development build** (prod strips the refresh
hooks `react-refresh` drives). Aliasing to the shared prod instance would make
Vite fall back to a **full page reload** — defeating the "partial refresh" ask.
The page's React is fixed by the backend-injected `shinyreact.js` dependency, so
an example alone cannot change it to a dev build.

## React handling in dev: bring-your-own dev React (Approach A)

Resolve the constraint without a backend change by accepting a dev/prod
asymmetry in *the example's build*:

- **Prod (`vite build`)** — externalize `react` / `react-dom` / `react-dom/client`
  to `window.shinyreact.*` via `rollupOptions.output.globals` (today's pattern),
  so the shipped bundle shares the one React.
- **Dev (`vite` serve)** — do **not** alias to `window.shinyreact`. Let the dev
  modules bundle their **own dev React** (`react`/`react-dom` from
  `node_modules`, `NODE_ENV=development`) and a **dev copy of the `shiny-react`
  hooks** (from the vendored source), so `@vitejs/plugin-react` Fast Refresh has a
  refresh-capable React to drive.

Two React copies then coexist on the page in dev: the prod one inside
`shinyreact.js` (which, in the `ui.tsx` pattern, renders nothing — there are no
`.shinyreact-output` placeholders) and the dev one that owns `#root`. The
`shiny-react` hooks talk to the global `window.Shiny` client, so the dev copy can
drive inputs/outputs independently.

Pin the example's dev `react`/`react-dom` to the vendored major
(`^19.2.3`, per `js/package.json`), and `resolve.dedupe: ["react", "react-dom"]`
so the user's components and the bundled `shiny-react` source share one React
copy.

**Why the two copies don't conflict (confirmed by code + spike):**
`shiny-react`'s registry init (`ensureShinyReactInitialized` →
`initializeReactRegistry` + `createReactOutputBinding`) is **lazy** — called from
inside each hook (`js/src/shiny-react/use-shiny.ts:84,218,…`), guarded by a
module-level flag. In the `ui.tsx` pattern the prod `shinyreact.js` bundle runs
*no* hooks itself, so it never initializes the registry. Only the dev copy does,
exactly once, storing the registry on the shared `window.Shiny.reactRegistry`
singleton — no double-binding, no duplicate output ids.

## Spike results (2026-06-04) — PASSED

A throwaway spike (`.context/spike-hmr/`, gitignored) ran the real stack: Shiny
serving `www/index.html` + the committed prod `shinyreact.js`, a Vite dev server
on `:5173` serving the user modules with their own dev React + the vendored
`shiny-react` source, driven through a browser.

Confirmed:
- **Round-trip works.** Clicking the counter pushed `count` to Shiny and read
  back the server-computed `doubled` (3 → 6) — the dev copy's freshly-initialized
  registry talks to the server with no conflict from the prod bundle.
- **True Fast Refresh.** Editing the heading text updated the DOM while the React
  `count` state stayed at 3 **and** a `window.__spikeMarker` planted before the
  edit survived — i.e. no full page reload. A second edit behaved identically.
- **Clean console** on normal component edits (only a benign `favicon.ico` 404).

Two **load-bearing structural requirements** the spike surfaced — both must be
baked into the example:

1. **Split the mount from the components.** A single file that both defines the
   component *and* calls `createRoot().render()` is **not** a Fast Refresh
   boundary — `@vitejs/plugin-react` bails to a full page reload (count reset to
   0, marker gone). Fix: components live in `App.tsx` (exported = refresh
   boundary); the entry `ui.tsx` only imports `App` and mounts it. Editing
   `App.tsx` → Fast Refresh; editing `ui.tsx` → full reload (rare, acceptable).
2. **The dev stub must install the React Fast Refresh preamble and use *dynamic*
   imports.** Because Shiny (not Vite) serves the page, the preamble
   `@vitejs/plugin-react` normally injects into HTML must be installed by the
   stub itself, *before* the entry evaluates. Static `import` statements hoist
   and would run the entry first, so the stub installs the preamble then
   `await import(...)`s `@vite/client` and the entry. Working stub:

   ```js
   import RefreshRuntime from "http://localhost:5173/@react-refresh";
   RefreshRuntime.injectIntoGlobalHook(window);
   window.$RefreshReg$ = () => {};
   window.$RefreshSig$ = () => (type) => type;
   window.__vite_plugin_react_preamble_installed__ = true;
   await import("http://localhost:5173/@vite/client");
   await import("http://localhost:5173/src/ui.tsx");
   ```

Vite config notes from the spike: `server.cors` is on by default (cross-origin
module load from `:5173` into the `:8000` page works); `server.fs.allow` had to
include the repo root only because the spike imported the *in-repo* vendored
`shiny-react` source — a downstream app installs `@posit/shiny-react` as a normal
dependency and won't need that. `server.strictPort: true` keeps the stub's
hard-coded `:5173` honest.

## Example

A new minimal example: **`examples/ui-tsx/09-hmr`** (09 is the next free number;
01–08 are taken).

- A counter whose state visibly **survives** a `.tsx` edit — the whole point is
  to demonstrate Fast Refresh, so state preservation is front-and-center.
- **Component/mount split is mandatory** (see Spike results): `src/App.tsx`
  exports the component (the refresh boundary); `src/ui.tsx` only imports `App`
  and calls `createRoot().render()`. Keep `createRoot` in the entry alone.
- Carries the reference `vite.config` (the dev-stub plugin, `resolve.dedupe`,
  `server` block) that other authors copy.
- Dev imports the `shiny-react` hooks (in this repo, from the **vendored source**
  at `js/src/shiny-react/` via relative path + `server.fs.allow`, as the spike
  did, since `shiny-react` is vendored not published — see `decisions/`;
  downstream apps would use a published `@posit/shiny-react` instead); prod
  externalizes them to `window.shinyreact`. A small per-mode indirection module
  (aliased in `serve` vs `build`) keeps `App.tsx` import lines identical. *(How
  the example references the vendored hooks cleanly is the main open detail for
  the plan.)*
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

- **Fallback if the spike fails — "instant full reload":** keep the Vite dev
  server (so saves are near-instant, no `vite build --watch` wait) but accept a
  fast *full* page reload. Component state is lost; not true partial refresh.
- **The "correct" larger fix (Approach B):** ship a dev variant of the
  `shinyreact` bundle (`shinyreact.dev.js`, React dev + `react-refresh`). Because
  that bundle is injected by the page dependency, loading it in dev needs a
  backend dev switch — deliberately deferred, as it breaks the JS-only and
  example-only scope.
- A shipped `shinyreact` dev helper or CLI that automates the stub so authors
  don't copy `vite.config` boilerplate.
- A single `dev` command wrapping both processes.
- R-side parity is automatic (JS-only), but an R example could mirror the Python
  one later.
