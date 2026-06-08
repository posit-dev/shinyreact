# `ui.tsx` Hot Reload / React Fast Refresh Example — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one worked `ui.tsx` example (`examples/ui-tsx/09-hmr/`) that gives app authors true React Fast Refresh against a Shiny-served page, plus the docs to find it — entirely in the JS/build layer, with no Python/R API change.

**Architecture:** Shiny serves the page + reactive WebSocket as always. A Vite dev server (`:5173`) serves the React modules with Fast Refresh. The statically-served `www/app.js` is the swap point: in dev a Vite plugin writes it as a stub that installs the React Refresh preamble and dynamically imports the HMR client + entry from `:5173`; `vite build` overwrites it with the real bundle. `index.html` is written once (`<script type="module" src="app.js">`) and never swapped. In dev the example bundles its **own dev React** + the vendored `shiny-react` hooks (Fast Refresh needs a dev React; `window.shinyreact.React` is production); in prod it externalizes both to `window.shinyreact`.

**Tech Stack:** Vite 5 (lib IIFE build + dev server), `@vitejs/plugin-react` (Fast Refresh), React 19, Shiny for Python (Express), the vendored `shiny-react` source at `js/src/shiny-react/`.

**Spec:** `docs/superpowers/specs/2026-06-04-ui-tsx-hot-reload-hmr-design.md` (read the "Spike results" section — it is the proven blueprint for everything below).

---

## File structure

All paths under `examples/ui-tsx/09-hmr/` unless noted.

| File | Responsibility |
|---|---|
| `package.json` | scripts (`build`/`dev`/`test`) + dev deps (react, react-dom, vite, plugin-react) |
| `vite-dev-stub.js` | `makeDevStub()` (pure stub-text generator) + `shinyreactDevStub()` (serve-only plugin that writes/cleans `www/app.js`) |
| `vite.config.js` | one config for both modes: `react()` + the stub plugin, `resolve.dedupe` + the `shiny-bridge` alias (dev vs prod), `server` block, prod lib/IIFE build with React externalized |
| `src/App.tsx` | the counter component — **exported**, so it is the Fast Refresh boundary |
| `src/ui.tsx` | entry/mount only — imports `App`, calls `createRoot().render()` |
| `src/shiny-bridge.dev.ts` | dev: re-exports the `shiny-react` hooks from the vendored source |
| `src/shiny-bridge.prod.ts` | prod: re-exports the same hooks from `window.shinyreact` |
| `www/index.html` | `#root` + `<script type="module" src="app.js">` (written once, never swapped) |
| `app.py` | Shiny Express server: `set_react_page()` + one `reactive_output` |
| `.gitignore` | `node_modules/`, `package-lock.json`, `www/app.js` |
| `test/dev-stub.test.mjs` | `node --test` unit test for `makeDevStub()` |
| `README.md` | two-terminal dev workflow + manual "verify HMR" checklist + prod build |
| `docs/app-py-vs-ui-tsx.md` (modify) | point the Vite-path dev workflow at the new example |
| `docs/features.md` (modify) | add HMR to the example inventory |
| `docs/todos.md` (modify) | record the deferred follow-ups (dev `shinyreact` bundle; dev helper/CLI) |

**Why two `shiny-bridge` files + an alias:** `App.tsx` always writes `import { ... } from "shiny-bridge"`. `vite.config` aliases `shiny-bridge` to the dev file in `serve` and the prod file in `build`, so the component's import lines never change between modes.

---

### Task 1: `makeDevStub()` pure function + unit test

**Files:**
- Create: `examples/ui-tsx/09-hmr/package.json`
- Create: `examples/ui-tsx/09-hmr/vite-dev-stub.js`
- Test: `examples/ui-tsx/09-hmr/test/dev-stub.test.mjs`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "hmr",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "vite build",
    "dev": "vite",
    "test": "node --test"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Write the failing test** at `test/dev-stub.test.mjs`

```js
import assert from "node:assert/strict";
import { test } from "node:test";

import { makeDevStub } from "../vite-dev-stub.js";

test("stub installs the Fast Refresh preamble before importing the entry", () => {
  const out = makeDevStub("http://localhost:5173", "src/ui.tsx");

  const refreshIdx = out.indexOf("@react-refresh");
  const clientIdx = out.indexOf("@vite/client");
  const entryIdx = out.indexOf("src/ui.tsx");

  assert.ok(refreshIdx >= 0, "imports @react-refresh");
  assert.match(out, /injectIntoGlobalHook/, "calls injectIntoGlobalHook");
  assert.match(out, /__vite_plugin_react_preamble_installed__/, "sets preamble flag");
  assert.ok(refreshIdx < clientIdx, "refresh preamble comes before @vite/client");
  assert.ok(clientIdx < entryIdx, "@vite/client comes before the entry");
  assert.match(
    out,
    /await import\("http:\/\/localhost:5173\/src\/ui\.tsx"\)/,
    "entry is loaded via dynamic import (so the preamble runs first)",
  );
});

test("stub honors a non-default origin", () => {
  const out = makeDevStub("http://localhost:5199", "src/ui.tsx");
  assert.match(out, /localhost:5199\/@vite\/client/);
  assert.match(out, /localhost:5199\/src\/ui\.tsx/);
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd examples/ui-tsx/09-hmr && node --test`
Expected: FAIL — `Cannot find module '../vite-dev-stub.js'`.

- [ ] **Step 4: Implement `makeDevStub` in `vite-dev-stub.js`**

```js
import fs from "node:fs";
import path from "node:path";

// The contents of the dev-mode `www/app.js`. Shiny serves this file statically.
// It (1) installs the React Fast Refresh preamble that @vitejs/plugin-react
// normally injects into the HTML it serves — but here Shiny serves the page, so
// we install it ourselves — then (2) dynamically imports Vite's HMR client and
// the real entry from the dev server. Dynamic `import()` is required: static
// imports are hoisted and would run the entry BEFORE the preamble, which makes
// Fast Refresh fall back to a full page reload.
export function makeDevStub(origin, entry) {
  return (
    `import RefreshRuntime from ${JSON.stringify(`${origin}/@react-refresh`)};\n` +
    `RefreshRuntime.injectIntoGlobalHook(window);\n` +
    `window.$RefreshReg$ = () => {};\n` +
    `window.$RefreshSig$ = () => (type) => type;\n` +
    `window.__vite_plugin_react_preamble_installed__ = true;\n` +
    `await import(${JSON.stringify(`${origin}/@vite/client`)});\n` +
    `await import(${JSON.stringify(`${origin}/${entry}`)});\n`
  );
}
```

(`fs`/`path` are imported now for the plugin added in Task 2; they are harmless here.)

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd examples/ui-tsx/09-hmr && node --test`
Expected: PASS — 2 tests, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add examples/ui-tsx/09-hmr/package.json examples/ui-tsx/09-hmr/vite-dev-stub.js examples/ui-tsx/09-hmr/test/dev-stub.test.mjs
git commit -m "feat(examples): add makeDevStub for the ui.tsx HMR example (#132)"
```

---

### Task 2: The dev-stub Vite plugin

**Files:**
- Modify: `examples/ui-tsx/09-hmr/vite-dev-stub.js`

- [ ] **Step 1: Append the `shinyreactDevStub` plugin factory to `vite-dev-stub.js`**

```js
// Vite plugin (serve only). On dev-server start it writes `outFile` (e.g.
// www/app.js) as the dev stub, and removes it on shutdown so a later plain
// `shiny run` doesn't load a stub pointing at a dead dev server. `vite build`
// (apply:"serve" excludes this plugin) overwrites `outFile` with the real bundle.
export function shinyreactDevStub({ entry, outFile }) {
  let stubPath;
  return {
    name: "shinyreact-dev-stub",
    apply: "serve",
    configResolved(config) {
      stubPath = path.resolve(config.root, outFile);
    },
    configureServer(server) {
      const port = server.config.server.port ?? 5173;
      const origin = `http://localhost:${port}`;
      fs.writeFileSync(stubPath, makeDevStub(origin, entry));
      server.config.logger.info(`  shinyreact: wrote dev stub ${outFile} -> ${origin}`);

      const remove = () => {
        try {
          fs.unlinkSync(stubPath);
        } catch {
          /* already gone */
        }
      };
      server.httpServer?.once("close", remove);
      for (const sig of ["SIGINT", "SIGTERM"]) {
        process.once(sig, () => {
          remove();
          process.exit(0);
        });
      }
    },
  };
}
```

- [ ] **Step 2: Re-run the unit test to confirm the module still loads**

Run: `cd examples/ui-tsx/09-hmr && node --test`
Expected: PASS — 2 tests (the new export adds no test but must not break import).

- [ ] **Step 3: Commit**

```bash
git add examples/ui-tsx/09-hmr/vite-dev-stub.js
git commit -m "feat(examples): add serve-only dev-stub Vite plugin (#132)"
```

---

### Task 3: App scaffold (components, entry, bridges, server, HTML, vite config)

**Files:**
- Create: `examples/ui-tsx/09-hmr/src/App.tsx`
- Create: `examples/ui-tsx/09-hmr/src/ui.tsx`
- Create: `examples/ui-tsx/09-hmr/src/shiny-bridge.dev.ts`
- Create: `examples/ui-tsx/09-hmr/src/shiny-bridge.prod.ts`
- Create: `examples/ui-tsx/09-hmr/www/index.html`
- Create: `examples/ui-tsx/09-hmr/app.py`
- Create: `examples/ui-tsx/09-hmr/vite.config.js`
- Create: `examples/ui-tsx/09-hmr/.gitignore`

- [ ] **Step 1: Create `src/App.tsx` (the Fast Refresh boundary — exported component, no mount)**

```tsx
import { useEffect, useState } from "react";

import { useShinyInitialized, useShinyInput, useShinyOutputValue } from "shiny-bridge";

// Exported component = a Fast Refresh boundary. Editing this file (e.g. the
// heading text below) hot-swaps the component WITHOUT losing `count`.
export default function App() {
  const initialized = useShinyInitialized();
  const [count, setCount] = useState(0);
  const [, setServerCount] = useShinyInput<number>("count", 0, { debounceMs: 0 });
  const doubled = useShinyOutputValue<number>("doubled", null);

  // Push the local count to the Shiny server whenever it changes.
  useEffect(() => {
    setServerCount(count);
  }, [count, setServerCount]);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 480, margin: "3rem auto" }}>
      {/* Edit this heading text while `npm run dev` + `shiny run` are running.
          The heading updates instantly and the count below keeps its value. */}
      <h1>Hot reload demo</h1>
      <p>Shiny initialized: {String(initialized)}</p>
      <button onClick={() => setCount((c) => c + 1)}>Count is {count}</button>
      <p>Server doubled it to: {doubled ?? "…"}</p>
    </main>
  );
}
```

- [ ] **Step 2: Create `src/ui.tsx` (entry/mount only — keep `createRoot` here, never in a component file)**

```tsx
import * as ReactDOM from "react-dom/client";

import App from "./App";

// Mount only. Component definitions live in App.tsx so the refresh boundary is
// clean. Editing THIS file triggers a full reload (rare); editing App.tsx does
// not. Calling createRoot in a file that also defines components would defeat
// Fast Refresh.
ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
```

- [ ] **Step 3: Create `src/shiny-bridge.dev.ts` (dev: hooks from the vendored source)**

```ts
// DEV path. The hooks come from the vendored shiny-react source and are bundled
// with this example's OWN dev React (Fast Refresh needs a dev React build;
// window.shinyreact.React is production). `resolve.dedupe` in vite.config keeps
// these and App.tsx on a single React copy. The relative path reaches the
// vendored source at the repo's js/src/shiny-react/ (served thanks to
// server.fs.allow in vite.config). Downstream apps would import a published
// @posit/shiny-react instead.
export {
  useShinyInitialized,
  useShinyInput,
  useShinyOutputValue,
} from "../../../../js/src/shiny-react/index";
```

- [ ] **Step 4: Create `src/shiny-bridge.prod.ts` (prod: hooks from the shared global)**

```ts
/* eslint-disable @typescript-eslint/no-explicit-any */
// PROD path. The hooks come from the shinyreact bridge global, sharing the one
// React instance that owns them. This file is aliased in by vite.config only for
// `vite build`.
const sr = (window as any).shinyreact;

export const useShinyInitialized = sr.useShinyInitialized;
export const useShinyInput = sr.useShinyInput;
export const useShinyOutputValue = sr.useShinyOutputValue;
```

- [ ] **Step 5: Create `www/index.html` (written once; works for both the stub and the built bundle)**

```html
<div id="root"></div>
<script type="module" src="app.js"></script>
```

- [ ] **Step 6: Create `app.py` (Shiny Express server)**

```python
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def doubled():
    # Echoes the client-pushed count, doubled — proves the Shiny round-trip
    # keeps working while you hot-edit the client.
    return input.count() * 2
```

- [ ] **Step 7: Create `vite.config.js` (one config, both modes)**

```js
import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import { shinyreactDevStub } from "./vite-dev-stub.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// examples/ui-tsx/09-hmr -> repo root (three levels up).
const repoRoot = path.resolve(__dirname, "../../..");
const ENTRY = "src/ui.tsx";

export default defineConfig(({ command }) => ({
  define: {
    "process.env.NODE_ENV": JSON.stringify(command === "build" ? "production" : "development"),
  },
  plugins: [
    react(),
    // serve only: writes www/app.js as the dev stub (apply:"serve" inside).
    shinyreactDevStub({ entry: ENTRY, outFile: "www/app.js" }),
  ],
  resolve: {
    // One React instance across App.tsx and the bundled shiny-react source.
    dedupe: ["react", "react-dom"],
    alias: {
      "shiny-bridge": path.resolve(
        __dirname,
        command === "serve" ? "src/shiny-bridge.dev.ts" : "src/shiny-bridge.prod.ts",
      ),
    },
  },
  server: {
    port: 5173,
    strictPort: true, // keep the stub's hard-coded :5173 honest
    // Allow serving the vendored shiny-react source that lives outside this dir.
    fs: { allow: [repoRoot] },
  },
  build: {
    outDir: "www",
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: path.resolve(__dirname, ENTRY),
      formats: ["iife"],
      name: "HmrExample",
      fileName: () => "app.js",
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-dom/client"],
      output: {
        globals: {
          react: "window.shinyreact.React",
          "react-dom": "window.shinyreact.ReactDOM",
          "react-dom/client": "window.shinyreact.ReactDOM",
        },
      },
    },
  },
}));
```

- [ ] **Step 8: Create `.gitignore`**

```
node_modules/
package-lock.json
www/app.js
```

- [ ] **Step 9: Commit**

```bash
git add examples/ui-tsx/09-hmr/src examples/ui-tsx/09-hmr/www/index.html examples/ui-tsx/09-hmr/app.py examples/ui-tsx/09-hmr/vite.config.js examples/ui-tsx/09-hmr/.gitignore
git commit -m "feat(examples): scaffold 09-hmr app, entry/component split, bridges (#132)"
```

---

### Task 4: Verify the production build path (no Vite running)

This proves the IIFE bundle loads correctly as a module script and the round-trip works without the dev server. **No new code unless a check fails.**

- [ ] **Step 1: Ensure the JS workspace deps exist** (the vendored source's `react` import resolves via the example's deps, but `make js-setup` keeps the repo consistent)

Run: `make js-setup`
Expected: completes (or "up to date").

- [ ] **Step 2: Install the example deps**

Run: `cd examples/ui-tsx/09-hmr && npm install`
Expected: installs react, react-dom, vite, @vitejs/plugin-react.

- [ ] **Step 3: Build the production bundle**

Run: `cd examples/ui-tsx/09-hmr && npm run build`
Expected: writes `www/app.js`.

- [ ] **Step 4: Confirm the bundle externalized React to the shared global**

Run: `grep -c "window.shinyreact.React" examples/ui-tsx/09-hmr/www/app.js`
Expected: count ≥ 1.

- [ ] **Step 5: Run the app on the prod bundle and verify in a browser**

Run (terminal 1): `cd examples/ui-tsx/09-hmr && uv run shiny run app.py --port 8011`
Then load `http://localhost:8011` in a browser (or Playwright MCP):
- Expected: heading "Hot reload demo", "Shiny initialized: true".
- Click the button 3 times → "Count is 3" and "Server doubled it to: 6" (round-trip).
- Console has no errors other than a `favicon.ico` 404.

If the page is blank or the console shows a module/parse error for `app.js`, the IIFE-as-module assumption failed — STOP and report; the fallback is to revisit the build `format` (see spec "Production entry format").

- [ ] **Step 6: Stop the server** (Ctrl-C / kill the port) and commit the verification note only if any config changed. Otherwise no commit.

---

### Task 5: Verify the dev / Fast Refresh path

- [ ] **Step 1: Start the Vite dev server**

Run (terminal 1): `cd examples/ui-tsx/09-hmr && npm run dev`
Expected: Vite ready on `:5173`, log line "shinyreact: wrote dev stub www/app.js -> http://localhost:5173". Confirm `www/app.js` now contains the preamble:

Run (terminal 3): `grep -q injectIntoGlobalHook examples/ui-tsx/09-hmr/www/app.js && echo OK`
Expected: `OK`.

- [ ] **Step 2: Start Shiny**

Run (terminal 2): `cd examples/ui-tsx/09-hmr && uv run shiny run app.py --port 8011`

- [ ] **Step 3: Verify the round-trip in a browser**

Load `http://localhost:8011`. Click +1 three times → "Count is 3", "Server doubled it to: 6".

- [ ] **Step 4: Verify Fast Refresh preserves state**

With count at 3, plant a marker in the browser console: `window.__m = "alive"`.
Edit `src/App.tsx` — change `<h1>Hot reload demo</h1>` to `<h1>Hot reload WORKS</h1>` and save.
Expected within ~1s, with NO full reload:
- Heading text updates to "Hot reload WORKS".
- "Count is 3" is unchanged (React state preserved).
- `window.__m` still returns `"alive"` (no document reload).

If the count resets to 0 / the marker is gone, Fast Refresh bailed to a full reload — STOP and report (most likely a component was defined in `ui.tsx` instead of `App.tsx`).

- [ ] **Step 5: Stop both servers.** Confirm the dev stub was cleaned up:

Run: `test -f examples/ui-tsx/09-hmr/www/app.js && echo "still present" || echo "removed"`
Expected: `removed` (the plugin deletes the stub on shutdown). No commit (no file changes — `www/app.js` is gitignored).

---

### Task 6: README

**Files:**
- Create: `examples/ui-tsx/09-hmr/README.md`

- [ ] **Step 1: Write `README.md`**

````markdown
# 09 — Hot reload (React Fast Refresh)

A `ui.tsx`-pattern example that gives you **React Fast Refresh** while Shiny
serves the page: edit a component and it hot-swaps in place, keeping component
state — no full page reload, no `vite build` wait.

## How it works

Shiny serves `www/index.html` (which loads `www/app.js` as a module) and the
reactive WebSocket. A Vite dev server serves your React modules with Fast
Refresh. The dev server writes `www/app.js` as a tiny stub that pulls the HMR
client + your entry from the dev server; `npm run build` overwrites it with the
real bundle. `index.html` never changes between modes.

Component code lives in `src/App.tsx` (the Fast Refresh boundary). The entry
`src/ui.tsx` only mounts it — keep `createRoot()` there, never in a file that
also defines components, or Fast Refresh falls back to a full reload.

In dev the example bundles its own dev React + the `shiny-react` hooks (Fast
Refresh needs a development React build). In the production build those are
externalized to the shared `window.shinyreact`.

## Develop (two terminals)

```bash
# terminal 1 — Vite dev server (writes www/app.js as a dev stub, serves HMR)
npm install
npm run dev

# terminal 2 — Shiny (serves the page + reactive WebSocket)
uv run shiny run --reload app.py
```

Open the URL Shiny prints. Editing `app.py` reloads via Shiny; editing
`src/App.tsx` hot-swaps via Fast Refresh.

## Verify HMR

1. Click **Count is 0** a few times so it reads e.g. **Count is 3**.
2. Edit the `<h1>` text in `src/App.tsx` and save.
3. The heading updates immediately, **the count stays at 3**, and the page does
   not fully reload.

## Build for production

```bash
npm run build          # writes www/app.js (the real bundle)
uv run shiny run app.py
```

## Test

```bash
npm test               # unit-tests the dev-stub generator
```
````

- [ ] **Step 2: Commit**

```bash
git add examples/ui-tsx/09-hmr/README.md
git commit -m "docs(examples): README for the 09-hmr Fast Refresh example (#132)"
```

---

### Task 7: Repo docs

**Files:**
- Modify: `docs/app-py-vs-ui-tsx.md` (the "`ui.tsx` — JSX + Vite path" dev-workflow block, around line 167-175)
- Modify: `docs/features.md`
- Modify: `docs/todos.md`

- [ ] **Step 1: Update the Vite-path dev workflow in `docs/app-py-vs-ui-tsx.md`**

Find:

```markdown
### `ui.tsx` — JSX + Vite path

1. Edit `app.py` and `src/ui.tsx` (or `App.jsx`)
2. Run `npm run build` (or `make watch`) to bundle `src/` → `www/`
3. Reload the app

The Vite build externalizes React to `window.shinyreact`, so the bundled client shares the same React instance as the `shinyreact` bridge hooks.

See [`examples/ui-tsx/03-columns-shadcn/`](../examples/ui-tsx/03-columns-shadcn/) and [`examples/ui-tsx/04-shadcn/`](../examples/ui-tsx/04-shadcn/) for the Vite path.
```

Replace the trailing paragraph + "See" line with:

```markdown
The Vite build externalizes React to `window.shinyreact`, so the bundled client shares the same React instance as the `shinyreact` bridge hooks.

For **hot reloading** (React Fast Refresh: edit a component and it hot-swaps while keeping state, no full reload), run a Vite **dev server** alongside Shiny instead of `npm run build`. See [`examples/ui-tsx/09-hmr/`](../examples/ui-tsx/09-hmr/) for the worked setup. (Editing `app.py` always reloads via Shiny's `--reload`; the no-build `www/app.js` path is picked up on the next browser load.)

See [`examples/ui-tsx/03-columns-shadcn/`](../examples/ui-tsx/03-columns-shadcn/) and [`examples/ui-tsx/04-shadcn/`](../examples/ui-tsx/04-shadcn/) for the Vite path, and [`examples/ui-tsx/09-hmr/`](../examples/ui-tsx/09-hmr/) for Fast Refresh.
```

- [ ] **Step 2: Add the example to `docs/features.md`**

Open `docs/features.md`, find the `ui.tsx` examples list/table, and add a row/bullet consistent with the existing format, e.g.:

```markdown
- `09-hmr` — React Fast Refresh in dev (Vite dev server alongside Shiny); the `app.py` and no-build `www/app.js` paths reload too.
```

(Match the exact surrounding format — table row vs bullet — used in that file.)

- [ ] **Step 3: Record the deferred follow-ups in `docs/todos.md`**

Add a new entry:

```markdown
## Hot reload: ship the ergonomics (follow-up to #132)

`examples/ui-tsx/09-hmr/` proves React Fast Refresh for the `ui.tsx` pattern with
no backend change (a Vite dev server alongside Shiny; the dev stub swaps
`www/app.js`). Two follow-ups remain:

- **Dev `shinyreact` bundle.** Today Fast Refresh works only because the example
  bundles its own dev React in dev — `window.shinyreact.React` is a production
  build (`js/vite.config.ts` pins `NODE_ENV=production`) and cannot drive
  `react-refresh`. A `shinyreact.dev.js` (React dev + refresh) would let the page
  itself share one dev React, but loading it requires a backend dev switch (the
  bundle is injected by the page dependency).
- **A shipped dev helper / CLI** so authors don't hand-copy the `vite.config`
  stub plugin + `shiny-bridge` indirection.
```

- [ ] **Step 4: Commit**

```bash
git add docs/app-py-vs-ui-tsx.md docs/features.md docs/todos.md
git commit -m "docs: point dev-workflow docs at the 09-hmr Fast Refresh example (#132)"
```

---

### Task 8: Final verification

- [ ] **Step 1: Unit tests pass**

Run: `cd examples/ui-tsx/09-hmr && node --test`
Expected: 2 tests pass.

- [ ] **Step 2: Production build still works**

Run: `cd examples/ui-tsx/09-hmr && npm run build && grep -c "window.shinyreact.React" www/app.js`
Expected: build succeeds, count ≥ 1.

- [ ] **Step 3: Clean tree except gitignored artifacts**

Run: `git status --porcelain examples/ui-tsx/09-hmr`
Expected: empty (— `www/app.js`, `node_modules/`, `package-lock.json` are gitignored).

- [ ] **Step 4: Confirm no stray references to the scratch spike**

Run: `grep -rn "spike-hmr\|.context/spike" examples/ui-tsx/09-hmr docs || echo "clean"`
Expected: `clean`.

- [ ] **Step 5: Remove the scratch spike** (it served its purpose; not part of the deliverable)

Run: `rm -rf .context/spike-hmr`
Expected: removed. (It is gitignored, so nothing to commit.)
