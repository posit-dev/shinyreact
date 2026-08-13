# shinyreact examples

Runnable example apps for the `ui.tsx` pattern: the server contains only
reactive computation, and the UI is defined in a client-side React codebase
whose entry is conventionally `ui.tsx` (simpler variants like `www/app.js`
for no-build or `src/App.jsx` for Vite + JSX fill the same role).

## Python ([`ui-tsx/`](ui-tsx/))

| Example | Description |
|---------|-------------|
| [01-hello](ui-tsx/01-hello/) | Smallest `ui.tsx` app — Python server with reactive logic only, plus a static React client (no JSX, no bundler). Side-by-side comparison of client-only state vs. server-routed state to highlight websocket latency |
| [02-columns](ui-tsx/02-columns/) | Drag-between-columns demo, no build step. Server owns data only (one `move_item` event input), client owns UI (~20 lines of server logic) |
| [03-columns-shadcn](ui-tsx/03-columns-shadcn/) | Same drag-between-columns demo as 02, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyreact` |
| [04-shadcn](ui-tsx/04-shadcn/) | shadcn/ui + Tailwind v4. Side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@reactive_output`, client renders); Plotly hover/click/select events round-trip through `useShinyInput` |
| [05-temperature](ui-tsx/05-temperature/) | Temperature conversion app demonstrating simple reactive data flow |
| [06-data-frame](ui-tsx/06-data-frame/) | Embeds `@render.data_frame` via `ShinyOutput` and `set_react_page()` |
| [07-plotly](ui-tsx/07-plotly/) | Embeds `@render_plotly` via `ShinyOutput` and `set_react_page()` |
| [08-input-handler](ui-tsx/08-input-handler/) | `useShinyInput` with `type="shiny.datetime"` — client sends unix seconds; server `input.when()` is a `datetime.datetime` via Shiny's built-in handler |
| [09-hmr](ui-tsx/09-hmr/) | React Fast Refresh in dev (Vite dev server alongside Shiny); the `app.py` and no-build `www/app.js` paths reload too |
| [10-bookmarking](ui-tsx/10-bookmarking/) | Bookmark restoration: URL query string (or server-stored state) hydrates `useShinyInput` initial values via a head `<script>` emitted by `page_react_html()` |

## R ([`ui-tsx-r/`](ui-tsx-r/))

| Example | Description |
|---------|-------------|
| [01-hello](ui-tsx-r/01-hello/) | `page_react_html()` + `reactive_output()` data returns; direct port of `ui-tsx/01-hello` |
