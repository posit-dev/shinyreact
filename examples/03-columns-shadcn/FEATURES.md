# examples/03-columns-shadcn — behavior

Example 02's app rendered with real shadcn/ui components, built by Vite in
IIFE lib mode.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Server (`app.py`, Express)

- three columns, ids `"A"`, `"B"`, `"C"`, seeded with `{A: [Apple, Apricot],
  B: [Banana, Blueberry], C: [Cherry, Cranberry]}`
  - held in a module-level `reactive.value`, so the state is shared by every
    session and survives a reload — it is not per-session
- output `column_data` → the whole `{col: item[]}` dict
- input `move_item` → `{item, from, to}`
  - handled by a `@reactive.effect` + `@reactive.event(input.move_item,
    ignore_init=True)`, so the initial `null` from mount is ignored
  - the move is applied to a copy of the dict, then `columns.set(...)` — the
    reactive value is replaced, not mutated in place
  - if `item` is not in `data[from]`, nothing changes (no error)
  - the item is appended to the end of the destination column, never inserted
- `[py]` only — this example has no R server
- this server is byte-for-byte the same file as example 02's; a divergence
  between the two apps is a bug in one of them

## Build

- `npm run build` → `vite build`; `npm run dev` → `vite build --watch` (a
  rebuild-on-change watcher, *not* a dev server with HMR — that is example 09)
- output: `www/ui.js` + `www/ui.css`, both gitignored, so the example does not
  run until it is built
  - `emptyOutDir: false` — the build writes into `www/` without wiping it
  - `assetFileNames: "ui.[ext]"` overrides Vite 5 lib mode's default
    `style.css`, so the emitted CSS matches the `ui.css` name `page_react()`
    discovery looks for
  - `cssCodeSplit: false` — one CSS file, not per-chunk
- `react`, `react-dom`, `react-dom/client` are `external`, mapped to
  `window.shinyreact.React` / `.ReactDOM`, so the bundle shares the React
  instance that owns the hooks
- `process.env.NODE_ENV` is defined as `"production"` unconditionally
- `@` resolves to `src/`
- Tailwind v4 via `@tailwindcss/vite`

## Client

- `src/ui.jsx` is mount-only: imports `@/index.css`, creates a `<div>` on
  `<body>`, renders `<App/>` — no component definitions
- `src/App.jsx` holds the UI and the hooks, destructured from
  `window.shinyreact` (not imported from a package)
- renders `null` until `useShinyInitialized()` is true
- same wire contract as example 02: `useShinyInput("move_item", null,
  {debounceMs: 0, priority: "event"})`, `useShinyOutputValue("column_data",
  null)`, columns from a hard-coded `["A", "B", "C"]`
- rendered with shadcn/ui `Card` / `CardHeader` / `CardTitle` / `CardContent`
  and `Button variant="outline" size="icon"`
- move buttons carry `aria-label` `"Move left"` / `"Move right"` and a
  lucide-react `ArrowLeft` / `ArrowRight` icon — there is no visible text label,
  so the accessible name is the only name
- an empty column renders `"(empty)"` in muted text
- three-column CSS grid, `max-w-3xl`, centered

## Not covered by tests

- the built bundle is gitignored, so no unit test mounts this client; the
  behavior claims above are shared with example 02, which is tested
