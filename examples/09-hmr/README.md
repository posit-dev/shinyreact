# 09 — Hot reload (React Fast Refresh)

A `ui.tsx`-pattern example that gives you **React Fast Refresh** while Shiny
serves the page: edit a component and it hot-swaps in place, keeping component
state — no full page reload, no `vite build` wait.

This is the **npm-tier** example: the client imports the hooks from
`@posit/shinyreact` and bundles its own React, in both modes. That is what
makes Fast Refresh possible — Fast Refresh needs a *development* React build,
and the React inside the server-shipped IIFE bundle is production-only.

Because the client ships the runtime itself, the server must not serve
`shinyreact.js` too — two copies on one page. Hence
`set_react_page(shinyreact_js="client")` in `app.py`. The `#shinyreact-config`
tag is still emitted, and the npm client requires it.

Until `@posit/shinyreact` is published, `package.json` depends on it as
`file:../../pkg-js` — repo-relative, so it only resolves inside a checkout of
this repo. Copy this example elsewhere and that line becomes
`"@posit/shinyreact": "^<version>"` from npm. In the meantime, build the
package first:

```bash
cd ../../pkg-js && npm install && npm run build
```

## How it works

Shiny serves a `set_react_page()`-generated page (which loads `www/ui.js` as a module) and the
reactive WebSocket. A Vite dev server serves your React modules with Fast
Refresh. The dev server writes `www/ui.js` as a tiny stub that pulls the HMR
client + your entry from the dev server; `npm run build` overwrites it with the
real bundle. The served page never changes between modes.

Component code lives in `src/App.tsx` (the Fast Refresh boundary). The entry
`src/ui.tsx` only mounts it — keep `createRoot()` there, never in a file that
also defines components, or Fast Refresh falls back to a full reload.

## Develop (two terminals)

```bash
# terminal 1 — Vite dev server (writes www/ui.js as a dev stub, serves HMR)
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
npm run build          # writes www/ui.js (the real bundle)
uv run shiny run app.py
```

## Test

```bash
npm test               # unit-tests the dev-stub generator
```
