# Features — `shinyjson` (SPA-first)

The new SPA-first package at `pkg-py/src/shinyjson/`. Provides minimal server-side primitives for apps whose UI lives in a static (or built) React client. See `DESIGN.md` for the architectural rationale and `features-shinyjson-old.md` for the legacy JSON-spec package.

## Python public API (`pkg-py/src/shinyjson/`)

| Feature | Status | Notes |
|---------|--------|-------|
| `SpaApp` | Working | App wrapper that serves a static `www/` directory (typically containing `index.html` + bundled JS) and runs a Shiny server alongside it |
| `@render_json` | Working | Renderer for SPA outputs — server returns any `Jsonifiable` value, the client picks it up via `useShinyOutput()` |
| `send_json(session, id, data)` | Working | Server-to-client custom message helper for SPA apps |

## JS bridge hooks (`js/src/shiny-react/`)

Vendored from `@posit/shiny-react`; bundled into `js/dist/shinyjson.js` (IIFE) and re-exported on `window.shinyjson`. Used by both the SPA-first apps and the legacy JSON-spec package.

| Feature | Status | Notes |
|---------|--------|-------|
| `useShinyInput` | Working | Stable defaultValue via `useRef`; debounce + priority options |
| `useShinyOutput` | Working | Subscribes to a Shiny output binding; receives `Jsonifiable` values from `render_json` |
| `useShinyMessageHandler` | Working | Stable handler ref; no unnecessary re-registration on inline arrow functions |
| `useShinyInitialized` | Working | Tracks Shiny client initialization state |
| `useShinyBusy` | Working | App-wide busy/idle state hook |
| `ShinyModuleProvider` | Working | Namespace support for module patterns |
| `ImageOutput` | Working | Renders `@render.plot()` outputs; prop is `id` (not `outputId`) |

## Examples

| Example | Status | Description |
|---------|--------|-------------|
| 13-spa-hello | Working | Smallest SPA-first app — Python server with reactive logic only, plus a static React client (no JSX, no bundler). Side-by-side comparison of client-only state vs. server-routed state to highlight websocket latency |
| 14-columns-new-spa | Working | Drag-between-columns demo on the new `shinyjson` package, no build step. Demonstrates the canonical SPA-first pattern: server owns data only (one `move_item` event input), client owns UI. ~20 lines of server logic vs. ~80 in the traditional `render.ui` version |
| 15-columns-shadcn | Working | Same drag-between-columns demo as 14, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyjson`. Identical Python server to 14 |
| 16-shadcn | Working | shadcn/ui + Tailwind v4 SPA. Mirrors `wch/shiny-react examples/5-shadcn` and adds a side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@render_json`, client renders) comparison; Plotly hover/click/select events round-trip through `useShinyInput` |

## Design decisions

- **Server owns data, client owns UI.** `render_json` ships pure data; the React client renders. Eliminates `render.ui`-driven dynamic UI patterns, per-item observer churn, and server-side ID bookkeeping.
- **SpaApp serves static + Shiny side-by-side.** The Python file contains reactive logic only; the `www/` directory contains `index.html` and (optionally) a bundled JS app.
- **No build step required.** The default path uses `React.createElement` directly from a hand-written `app.js` (see ex. 13/14). Apps that want JSX or a component library opt into Vite (see ex. 15/16).
- **Vite lib-mode IIFE for build path.** Bundled SPA apps externalize React to `window.shinyjson` to share the bundled React instance with shinyjson's hooks and avoid duplicate React copies.
