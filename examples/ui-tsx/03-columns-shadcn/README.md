# Example 15 — drag-between-columns with shadcn/ui

Same drag-between-columns demo as [example 14](../14-columns-new-spa/), but rendered with real [shadcn/ui](https://ui.shadcn.com/) `Card` and `Button` components plus [lucide-react](https://lucide.dev/) arrow icons, styled with Tailwind v4. The Python server is identical — only the client changes.

The point: once you want a component library, you have to bring a build step. This example shows the canonical setup for `ui.tsx`-first apps that want shadcn — Vite in lib-mode IIFE, with React externalized to `window.shinyreact`.

## What it shows

- Three columns rendered as shadcn `Card`s, each with a `CardHeader` / `CardTitle` / `CardContent`.
- Items rendered as bordered rows with shadcn `Button`s (`variant="outline" size="icon"`) wrapping `ArrowLeft` / `ArrowRight` icons from lucide.
- Click an arrow → `useShinyInput("move_item", ...)` ships a `{item, from, to}` event → server's `@reactive.event(input.move_item)` mutates a `reactive.value` → `@reactive_output` ships the new `{A:[...], B:[...], C:[...]}` dict → React re-renders.

## Layout

```
examples/15-columns-shadcn/
├── app.py                          # identical server to ex 14
├── package.json
├── vite.config.js                  # lib-mode IIFE; React → window.shinyreact
├── src/
│   ├── App.jsx                     # composes Column → ItemRow with shadcn Card/Button
│   ├── main.jsx                    # mounts via window.shinyreact.React/ReactDOM
│   ├── index.css                   # Tailwind v4 + shadcn theme tokens
│   ├── lib/utils.js                # cn() = clsx + tailwind-merge
│   └── components/ui/
│       ├── button.jsx              # actual shadcn Button (cva variants)
│       └── card.jsx                # actual shadcn Card stack
└── www/
    ├── index.html                  # 3 lines, committed
    ├── app.js                      # built by Vite (gitignored)
    └── style.css                   # built by Vite (gitignored)
```

## Build plumbing

Worth understanding because every shadcn-style example in this repo uses the same setup:

- `vite.config.js` is in **lib mode** with `format: "iife"`, output filename `app.js`. We can't use Vite's regular HTML pipeline because we need a single self-contained bundle that reuses the page's existing React.
- `react`, `react-dom`, `react-dom/client` are listed as `external` and mapped via `rollupOptions.output.globals` to `window.shinyreact.React` / `window.shinyreact.ReactDOM`. The IIFE bundle reuses the React instance that owns the shinyreact hooks (mixing two React copies would break `useShinyInput`/`useShinyOutput`).
- `@tailwindcss/vite` wires Tailwind v4 in directly; the shadcn design tokens live in `src/index.css`.
- `define: { "process.env.NODE_ENV": '"production"' }` is set because lib mode does not auto-replace it (it assumes a downstream bundler will). Without it the bundled React jsx-runtime hits a `process is not defined` error in the browser.
- `lucide-react` is a runtime dependency. It transitively pulls in `react` so `react/jsx-runtime` resolves at build time.

## Run it

```bash
cd examples/15-columns-shadcn
npm install
npm run build       # or `npm run dev` for watch mode

cd ../..
uv run shiny run examples/15-columns-shadcn/app.py
```

## When to use this pattern

When you want shadcn (or any other JSX-based component library) with the `ui.tsx`-first model. For a richer demo with multiple cards and a server-side plot, see [example 16](../16-shadcn/). For a build-step-free version, see [example 14](../14-columns-new-spa/).
