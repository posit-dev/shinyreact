# Example 16 — shadcn/ui + plotly.js (SPA-first)

A SPA-first Shiny app whose UI is a React app styled with [shadcn/ui](https://ui.shadcn.com/) components and Tailwind v4. Mirrors the layout from
[wch/shiny-react examples/5-shadcn](https://github.com/wch/shiny-react/tree/main/examples/5-shadcn) and adds a side-by-side comparison of a server-rendered matplotlib plot vs. a client-rendered Plotly chart over the same data.

## What it shows

| Card | Demonstrates |
|------|--------------|
| **TextInputCard** | shadcn `Input` + `Card` + `Badge`. `useShinyInput("user_text", "")` round-trips text through the server, which sends back the reversed/uppercased string and a length count via `@reactive_output`. |
| **ButtonEventCard** | shadcn `Button` + `Card`. `useShinyInput("button_trigger", 0, { priority: "event" })` is a Shiny-style action button — increments on every click; the server's `@reactive_output @reactive.event(input.button_trigger)` returns a fresh timestamp string. |
| **PlotCard** | shadcn `Card` wrapping `<ImageOutput id="plot1"/>`. The server uses Shiny's standard `@render.plot` to draw a matplotlib scatter + linear trend line; the SPA's `ImageOutput` binding picks up the rendered PNG. |
| **PlotlyCard** | shadcn `Card` with a `plotly.js-basic-dist-min` chart. The server only ships the raw data via `@reactive_output scatter_data`; the client receives `{age: [...], score: [...]}`, computes the trend-line slope/intercept locally, and calls `Plotly.react`. Continuous hover (anywhere in the plot, not just on markers), click anywhere, drag-to-select-and-zoom, double-click or Esc to reset the view. All interactions push the cursor's data coords into Shiny inputs (`plotly_hover`, `plotly_click`, `plotly_dblclick`, `plotly_selection`, `plotly_xy_ranges`). |
| **PlotlyInfoCard** | A read-only card that re-subscribes to those same input ids via `useShinyInput`. The displayed values are React's local state (no roundtrip), demonstrating that "set a Shiny input from a client interaction" and "display a value the client already has" are the same hook. The values also travel to the server, so `input.plotly_hover()` etc. work in the Python reactive graph if you want them. |

The two plots draw the same data so you can see the trade-off directly:

| Path | Wire payload | Where rendering runs | Interactive zoom |
|------|--------------|----------------------|------------------|
| matplotlib + `ImageOutput` | ~50 kB PNG | server (Python) | requires server roundtrip (re-render at new size) |
| plotly.js + `useShinyOutput` | ~120 B JSON | browser | instant, no server involvement |

## Layout

```
examples/16-shadcn/
├── app.py                          # set_react_page() + outputs (4 reactive_output + 1 render.plot)
├── package.json
├── vite.config.js                  # lib-mode IIFE; React externalized to window.shinyreact
├── README.md
├── src/
│   ├── App.jsx                     # composes the cards
│   ├── main.jsx                    # mounts via window.shinyreact.React/ReactDOM
│   ├── index.css                   # Tailwind v4 + shadcn theme tokens
│   ├── lib/utils.js                # cn() = clsx + tailwind-merge
│   └── components/
│       ├── TextInputCard.jsx
│       ├── ButtonEventCard.jsx
│       ├── PlotCard.jsx            # server-rendered matplotlib plot
│       ├── PlotlyCard.jsx          # client-rendered plotly.js chart
│       ├── PlotlyInfoCard.jsx      # reads back hover/click/etc. via useShinyInput
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

The non-obvious bit is how the bundle stays compatible with the page-level `window.shinyreact` runtime:

- `vite.config.js` is in **lib mode** with format `iife`, output filename `app.js`.
- `react`, `react-dom`, and `react-dom/client` are listed as `external` and mapped via `rollupOptions.output.globals` to `window.shinyreact.React` / `window.shinyreact.ReactDOM`. The IIFE bundle reuses the React instance that owns the shinyreact hooks (mixing two React copies would break `useShinyInput`/`useShinyOutput`).
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

Open the URL printed by Shiny. Type in the text box, click "Send Event", and compare the two plots. On the Plotly chart, try:

- Move the cursor anywhere — the **Hover** row in the info card updates continuously.
- Click anywhere — the **Click** row updates with the cursor's data coords.
- Drag a box — the **Selection** row populates as you drag, and on release the chart zooms to that region.
- Double-click anywhere, or hover the chart and press **Esc** — view resets to autorange and the selection clears.

> **Note on double-click:** Plotly's drag layer uses `setPointerCapture`, which swallows the `mouseup` events the browser needs to detect a native `dblclick`. The example falls back to a manual click counter (two clicks within 300 ms) — see `PlotlyCard.jsx`.
