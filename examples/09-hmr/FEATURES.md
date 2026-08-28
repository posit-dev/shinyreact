# examples/09-hmr — behavior

React Fast Refresh against a running Shiny server: a Vite dev server serves the
client modules while Shiny serves the page. Editing `App.tsx` hot-swaps the
component without losing local state or the Shiny connection.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Server (`app.py`, Express)

- one output, `doubled` → `input.count() * 2`
- `set_react_page()` with no arguments — the same discovery as the no-build
  examples; nothing in the server knows about the dev server
- `[py]` only — this example has no R server

## Two modes, one entry

- `vite build` → `www/ui.js` is the real IIFE bundle, React externalized to
  `window.shinyreact`, `NODE_ENV=production`
- `vite` (dev) → `www/ui.js` is a **stub** that boots the dev server's modules;
  `NODE_ENV=development`
- `www/ui.js` is gitignored, so a fresh checkout must run one of the two before
  `shiny run` serves anything
- the switch is `resolve.alias["shiny-bridge"]`, chosen by Vite's `command`
  - `serve` → `src/shiny-bridge.dev.ts`, re-exporting the hooks from the
    repo's vendored `pkg-js/src/shiny-react/` source, bundled with this
    example's own **development** React (Fast Refresh cannot run against the
    production React inside `window.shinyreact`)
  - `build` → `src/shiny-bridge.prod.ts`, reading the hooks off
    `window.shinyreact`
  - `resolve.dedupe: ["react", "react-dom"]` keeps `App.tsx` and the vendored
    hooks on one React copy in dev
  - `server.fs.allow` is widened to the repo root so the vendored source
    outside this directory can be served

## The dev stub (`vite-dev-stub.js`)

- `makeDevStub(origin, entry)` returns module source that, in order `(test)`
  1. imports `RefreshRuntime` from `<origin>/@react-refresh`
  2. calls `injectIntoGlobalHook(window)` and sets `$RefreshReg$`,
     `$RefreshSig$`, `__vite_plugin_react_preamble_installed__`
  3. `await import(<origin>/@vite/client)`
  4. `await import(<origin>/<entry>)`
- the entry is loaded with a **dynamic** `import()`, not a static one: static
  imports hoist and would run the entry before the preamble, which silently
  degrades Fast Refresh to a full page reload `(test)`
- this preamble is what `@vitejs/plugin-react` normally injects into the HTML
  it serves — here Shiny serves the page, so the stub installs it
- a trailing slash on `origin` is stripped, so no URL contains `//` `(test)`
- a non-default origin is honored throughout `(test)`
- the `shinyreactDevStub({entry, outFile})` plugin is `apply: "serve"` only
  - on dev-server start it writes `outFile` and logs
    `"shinyreact: wrote dev stub <outFile> -> <origin>"`
  - it removes the file when the http server closes and on `SIGINT` /
    `SIGTERM`, so a later plain `shiny run` never loads a stub pointing at a
    dead dev server
  - `vite build` (which excludes the plugin) overwrites `outFile` with the real
    bundle
- the dev port is hard-coded to 5173 with `strictPort: true`, keeping the
  stub's baked-in origin honest — a busy port fails the dev server rather than
  silently shifting it

## Client

- `src/ui.tsx` is mount-only: `createRoot` on a `<div>` appended to `<body>`,
  renders `<App/>`
  - defining components here would defeat Fast Refresh, so editing `ui.tsx`
    triggers a full reload while editing `App.tsx` does not
- `src/App.tsx`
  - `count` is React `useState`, owned by the client; it is the value that must
    survive a hot edit
  - a `useEffect` pushes it to `useShinyInput("count", 0, {debounceMs: 0})` on
    every change
  - `doubled` is read with `useShinyOutputValue("doubled", null)` and rendered
    as `"Server doubled it to: N"`, `"…"` before the first value
  - the connection state is printed literally as `"Shiny initialized: true"` /
    `"false"` — unlike the other examples, this one renders *before*
    initialization rather than returning `null`

## Tests

- `test/dev-stub.test.mjs`, run with `npm test` (`node --test`) — pins the stub
  ordering, the dynamic import, and the trailing-slash handling
- nothing tests the plugin's file write/cleanup or the Fast Refresh behavior
  itself; those are manual
