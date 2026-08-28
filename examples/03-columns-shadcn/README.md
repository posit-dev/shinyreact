# Example 15 — drag-between-columns with shadcn/ui

Same drag-between-columns demo as [02-columns](../02-columns/), but rendered with real [shadcn/ui](https://ui.shadcn.com/) `Card` and `Button` components plus [lucide-react](https://lucide.dev/) arrow icons, styled with Tailwind v4. The Python server is identical — only the client changes.

The point: once you want a component library, you have to bring a build step. This example shows the canonical setup for `ui.tsx`-first apps that want shadcn — Vite in lib-mode IIFE, with React externalized to `window.shinyreact` — **and** the app owning its own `www/index.html` (served via `ReactApp`), rather than letting the server generate the page.

## What it shows

- Three columns rendered as shadcn `Card`s, each with a `CardHeader` / `CardTitle` / `CardContent`.
- Items rendered as bordered rows with shadcn `Button`s (`variant="outline" size="icon"`) wrapping `ArrowLeft` / `ArrowRight` icons from lucide.
- Click an arrow → `useShinyInput("move_item", ...)` ships a `{item, from, to}` event → server's `@reactive.event(input.move_item)` mutates a `reactive.value` → `@reactive_output` ships the new `{A:[...], B:[...], C:[...]}` dict → React re-renders.
- An app-owned `www/index.html`: your `<html lang>`, your `<meta viewport>`, your `<title>`, and a `Loading…` placeholder that shows before the bundle mounts.

## Layout

```
examples/03-columns-shadcn/
├── app.py                          # same server logic as 02-columns, Core API
├── package.json
├── vite.config.js                  # lib-mode IIFE; React → window.shinyreact
├── src/
│   ├── App.jsx                     # composes Column → ItemRow with shadcn Card/Button
│   ├── ui.jsx                      # mounts into #root from www/index.html
│   ├── index.css                   # Tailwind v4 + shadcn theme tokens
│   ├── lib/utils.js                # cn() = clsx + tailwind-merge
│   └── components/ui/
│       ├── button.jsx              # actual shadcn Button (cva variants)
│       └── card.jsx                # actual shadcn Card stack
└── www/
    ├── index.html                  # the app's own document (checked in)
    ├── ui.js                       # built by Vite (gitignored)
    └── ui.css                      # built by Vite (gitignored)
```

## The app-owned document

`app.py` is `ReactApp(server)` with no `ui=`. It finds `www/index.html`, so the
page is *your* document — Shiny does not build one. Two things make that work:

- **`<meta name="shiny-dependency-placeholder" content="">`** in `<head>` marks
  where Shiny's and shinyreact's `<script>`/`<link>` tags go. It is an ordinary
  `<meta>` tag, not template syntax, so the file is valid HTML that any tool can
  parse (`shiny.ui.PageDocument.DEPS_PLACEHOLDER` is the same literal).
- **`ReactApp` mounts `www/` at `/`**, so the document's relative `ui.js` /
  `ui.css` are served.

`<script src="ui.js" defer>` needs the `defer`: the shinyreact bundle in
`<head>` is deferred, and deferred scripts run in document order, so without it
`ui.js` would run first and find no `window.shinyreact`.

The tradeoff versus the other examples: `page_react()` / `set_react_page()`
version the bundle by its mtime, so the browser re-fetches after every rebuild.
A hand-written `<script src="ui.js">` is cached by URL — hard-refresh after
rebuilding, or add your own `?v=` / content hash. Own the document when you need
control over the HTML; otherwise don't.

## Build plumbing

Worth understanding because every shadcn-style example in this repo uses the same setup:

- `vite.config.js` is in **lib mode** with `format: "iife"`, output filename `ui.js`, referenced by `www/index.html`. We can't use Vite's regular HTML pipeline because we need a single self-contained bundle that reuses the page's existing React — an ES-module build can't map a bare `react` import to a global.
- `react`, `react-dom`, `react-dom/client` are listed as `external` and mapped via `rollupOptions.output.globals` to `window.shinyreact.React` / `window.shinyreact.ReactDOM`. The IIFE bundle reuses the React instance that owns the shinyreact hooks (mixing two React copies would break the hooks).
- `@tailwindcss/vite` wires Tailwind v4 in directly; the shadcn design tokens live in `src/index.css`.
- `define: { "process.env.NODE_ENV": '"production"' }` is set because lib mode does not auto-replace it (it assumes a downstream bundler will). Without it the bundled React jsx-runtime hits a `process is not defined` error in the browser.
- `lucide-react` is a runtime dependency. It transitively pulls in `react` so `react/jsx-runtime` resolves at build time.

## Run it

```bash
cd examples/03-columns-shadcn
npm install
npm run build       # or `npm run dev` for watch mode

cd ../../..
uv run shiny run examples/03-columns-shadcn/app.py
```

## When to use this pattern

When you want shadcn (or any other JSX-based component library) with the `ui.tsx`-first model. For a richer demo with multiple cards and a server-side plot, see [04-shadcn](../04-shadcn/). For a build-step-free version, see [02-columns](../02-columns/).
