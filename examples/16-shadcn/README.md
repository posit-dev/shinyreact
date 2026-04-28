# Example 16 — shadcn/ui + plotly.js (SPA-first)

A SPA-first Shiny app whose UI is a React app styled with [shadcn/ui](https://ui.shadcn.com/) components and Tailwind v4. Mirrors the layout from
[wch/shiny-react examples/5-shadcn](https://github.com/wch/shiny-react/tree/main/examples/5-shadcn) and adds a side-by-side comparison of a server-rendered matplotlib plot vs. a client-rendered Plotly chart over the same data.

## What it shows

| Card | Demonstrates |
|------|--------------|
| **TextInputCard** | shadcn `Input` + `Card` + `Badge`. `useShinyInput("user_text", "")` round-trips text through the server, which sends back the reversed/uppercased string and a length count via `@render_json`. |
| **ButtonEventCard** | shadcn `Button` + `Card`. `useShinyInput("button_trigger", 0, { priority: "event" })` is a Shiny-style action button — increments on every click; the server's `@render_json @reactive.event(input.button_trigger)` returns a fresh timestamp string. |
| **PlotCard** | shadcn `Card` wrapping `<ImageOutput id="plot1"/>`. The server uses Shiny's standard `@render.plot` to draw a matplotlib scatter + linear trend line; the SPA's `ImageOutput` binding picks up the rendered PNG. |
| **PlotlyCard** | shadcn `Card` with a `plotly.js-basic-dist-min` chart. The server only ships the raw data via `@render_json scatter_data`; the client receives `{age: [...], score: [...]}`, computes the trend-line slope/intercept locally, and calls `Plotly.react`. Pan/zoom/hover are pure client interactions — zero roundtrips after the initial fetch. |

The two plots draw the same data so you can see the trade-off directly:

| Path | Wire payload | Where rendering runs | Interactive zoom |
|------|--------------|----------------------|------------------|
| matplotlib + `ImageOutput` | ~50 kB PNG | server (Python) | requires server roundtrip (re-render at new size) |
| plotly.js + `useShinyOutput` | ~120 B JSON | browser | instant, no server involvement |

## Layout

```
examples/16-shadcn/
├── app.py                          # SpaApp + 4 outputs (3 render_json + 1 render.plot)
├── package.json
├── vite.config.js                  # lib-mode IIFE; React externalized to window.shinyjson
├── README.md
├── src/
│   ├── App.jsx                     # composes the four cards
│   ├── main.jsx                    # mounts via window.shinyjson.React/ReactDOM
│   ├── index.css                   # Tailwind v4 + shadcn theme tokens
│   ├── lib/utils.js                # cn() = clsx + tailwind-merge
│   └── components/
│       ├── TextInputCard.jsx
│       ├── ButtonEventCard.jsx
│       ├── PlotCard.jsx            # server-rendered matplotlib plot
│       ├── PlotlyCard.jsx          # client-rendered plotly.js chart
│       └── ui/                     # actual shadcn component files (cva + Tailwind)
│           ├── badge.jsx
│           ├── button.jsx
│           ├── card.jsx
│           ├── input.jsx
│           └── separator.jsx
└── www/
    ├── index.html                  # 3 lines, committed
    ├── app.js                      # built by Vite (gitignored)
    └── style.css                   # built by Vite (gitignored)
```

## Build plumbing

The non-obvious bit is how the bundle stays compatible with the page-level `window.shinyjson` runtime:

- `vite.config.js` is in **lib mode** with format `iife`, output filename `app.js`.
- `react`, `react-dom`, and `react-dom/client` are listed as `external` and mapped via `rollupOptions.output.globals` to `window.shinyjson.React` / `window.shinyjson.ReactDOM`. The IIFE bundle reuses the React instance that owns the shinyjson hooks (mixing two React copies would break `useShinyInput`/`useShinyOutput`).
- `react`/`react-dom` are still listed as `devDependencies` so `react/jsx-runtime` resolves at build time when Vite's automatic JSX transform inlines it.
- Tailwind v4 is wired in through `@tailwindcss/vite`; the shadcn design tokens live in `src/index.css`.
- `define: { "process.env.NODE_ENV": '"production"' }` is set in the Vite config because lib mode does not auto-replace it (it assumes a downstream bundler will). Without it, the bundled React jsx-runtime hits a `process is not defined` error in the browser.

## Run it

```bash
# from the repo root
cd examples/16-shadcn
npm install
npm run build       # or `npm run dev` for watch mode

cd ../..
uv run shiny run examples/16-shadcn/app.py
```

Open the URL printed by Shiny. Type in the text box, click "Send Event", and compare the two plots — try drag-zoom on the Plotly chart to see how the client-rendered version reacts instantly.
