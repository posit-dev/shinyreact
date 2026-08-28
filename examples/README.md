# shinyreact examples

Runnable example apps for the `ui.tsx` pattern: the server contains only
reactive computation, and the UI is defined in a client-side React codebase
whose entry is conventionally `ui.tsx` (simpler variants like `www/ui.js`
for no-build or `src/ui.jsx` for Vite + JSX fill the same role).

Examples are Python unless noted; [01-hello](01-hello/) also ships an `app.R`
showing the same app on the R package.

| Example | Description |
|---------|-------------|
| [01-hello](01-hello/) | Shiny's `01_hello` Old Faithful app rebuilt `ui.tsx`-first (no JSX, no bundler). The server returns histogram `{breaks, counts}` as JSON; the client draws the bars as SVG. Includes `app.py`, `app-core.py`, and `app.R` servers over the same `www/` client |
| [02-columns](02-columns/) | Drag-between-columns demo, no build step. Server owns data only (one `move_item` event input), client owns UI (~20 lines of server logic) |
| [03-columns-shadcn](03-columns-shadcn/) | Same drag-between-columns demo as 02, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyreact`. The only example that owns its own `www/index.html` — `ReactApp(server)` serves it as-is, inserting the tags at `<meta name="shiny-dependency-placeholder">` |
| [04-shadcn](04-shadcn/) | shadcn/ui + Tailwind v4. Side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@reactive_output`, client renders); Plotly hover/click/select events round-trip through `useShinyInput` |
| [05-temperature](05-temperature/) | Temperature conversion app demonstrating simple reactive data flow |
| [06-data-frame](06-data-frame/) | Embeds `@render.data_frame` via `ShinyOutput` and `set_react_page()` |
| [07-plotly](07-plotly/) | Embeds `@render_plotly` via `ShinyOutput` and `set_react_page()`. Also ships an `app.R` using `plotly::renderPlotly()` over the same `www/` client — its binding JS is discovered from the render function and pushed automatically |
| [08-input-handler](08-input-handler/) | `useShinyInput` with `type="shiny.datetime"` — client sends unix seconds; server `input.when()` is a `datetime.datetime` via Shiny's built-in handler |
| [09-hmr](09-hmr/) | React Fast Refresh in dev (Vite dev server alongside Shiny); the `app.py` and no-build `www/ui.js` paths reload too |
| [10-bookmarking](10-bookmarking/) | Bookmark restoration: URL query string (or server-stored state) hydrates `useShinyInput` initial values via the `#shinyreact-config` tag emitted by `page_react()` |
