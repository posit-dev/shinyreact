# examples/03-columns-shadcn — behavior

Example 02's app rendered with real shadcn/ui components, built by Vite in
IIFE lib mode.

Format rules: `../README.md` § "Example behavior trees".

## Server (`app.py`, Express)

- byte-for-byte the same server logic as `../02-columns/app.py`: module-level
  `reactive.value` seeded with `{A: [Apple, Apricot], B: [Banana, Blueberry],
  C: [Cherry, Cranberry]}`, a `move_item` event effect, a `column_data` output
- see `../02-columns/FEATURES.md` § "Server" for the per-claim detail; a
  divergence between the two files is a bug in one of the apps

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
