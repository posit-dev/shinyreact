# Features — `shinyreact`

The `shinyreact` package ships two first-class patterns. See [`docs/app-py-vs-ui-tsx.md`](app-py-vs-ui-tsx.md) for a side-by-side comparison and guidance on which to choose.

---

## `app.py` pattern (`page_react` + `reactive_output`)

UI is defined as Python (or R) objects in the app file via `page_react()` / `Spec` / `Element` / `Node`. The server emits JSON specs that the client renders into a React tree using `shinyreact`'s in-house Spec walker (`js/src/renderer.tsx`). Lives at `pkg-py/src/shinyreact/`. Examples in `examples/app-py/`.

### Python public API

| Feature | Status | Notes |
|---------|--------|-------|
| `shinyreact.ui_output()` | Working | Creates output div with HTMLDependency; accepts `extra_deps` |
| `shinyreact.page_react()` | Working | Full-page React app with `#root` + the shinyreact HTMLDependency |
| `shinyreact.page_bare()` | Working | Bare HTML page wrapper |
| `@shinyreact.reactive_output` | Working | Renders `Spec` or passes raw JSON for `useShinyOutputValue` |
| `shinyreact.Spec` / `Element` | Working | Flat-map data model for component trees |
| `shinyreact.Node` | Working | Nested tree API; `.to_spec()` auto-flattens to `Spec` |
| `shinyreact.send_message()` | Working | Server-to-client custom messages |
| Bookmark restoration | Working | `page_react()` and `set_react_page()` emit a head `<script>` carrying restored input values; `useShinyInput` adopts them as initial values. URL and server-stored bookmark modes both supported |

### Examples

| Example | Status | Description |
|---------|--------|-------------|
| [01-hello-world](../examples/app-py/01-hello-world/) | Working | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via Spec |
| [02-inputs](../examples/app-py/02-inputs/) | Working | 10 input types (text, number, checkbox, radio, select, slider, date, button, file, batch form) |
| [03-outputs](../examples/app-py/03-outputs/) | Working | Data table, statistics, matplotlib plot via ImageOutput |
| [04-messages](../examples/app-py/04-messages/) | Working | Server-to-client messaging with send_message, auto-dismissing toasts |
| [05-shadcn](../examples/app-py/05-shadcn/) | Working | Text processing, button events, matplotlib plot; shadcn look via plain CSS |
| [06-dashboard](../examples/app-py/06-dashboard/) | Working | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters |
| [07-chat](../examples/app-py/07-chat/) | Needs API key | AI chat with streaming, themes, image upload; requires OPENAI_API_KEY |
| [08-modules](../examples/app-py/08-modules/) | Working | Three counter widgets using ShinyModuleProvider namespacing |
| [09-blended](../examples/app-py/09-blended/) | Working | Tabbed sidebar layout, matplotlib plot, data table, settings panel |
| [10-columns](../examples/app-py/10-columns/) | Working | Drag-between-columns demo; `render.ui`-driven approach |
| [13-bookmarking](../examples/app-py/13-bookmarking/) | Working | Bookmark restoration: URL query string (or server-stored state) hydrates `useShinyInput` initial values via a head `<script>` emitted by `page_react()` |

### Design decisions

- **Treat element keys as internal/opaque.** When using `Node`, element keys in the flat `elements` map (e.g., `"auto_001"`) are auto-generated internal plumbing. Callers can still manually construct `Spec(elements={...})` with arbitrary keys, so this is guidance rather than a hard API guarantee. These keys have no relationship to DOM IDs or Shiny input/output IDs: Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server needs to know about.
- **HTMLDependency mtime versioning for examples.** Shiny caches static files by `{name}-{version}` in the URL. During development, editing a JS file doesn't bust the cache if the version string is fixed. Examples use `version=str(int(file.stat().st_mtime))` so the version changes whenever the file is saved. Development convenience only — published packages should use fixed versions.
- **Downstream extension.** Downstream packages (e.g. `shinyshadcn`) ship their own IIFE bundle that calls `window.shinyreact.registerComponents(catalog, registry)` at load time, plus a Python render subclass with an overridden `transform()`. The package's `HTMLDependency` is injected on the UI side via `shinyreact.ui_output(id, extra_deps=[...])` (`reactive_output` does not read an `extra_deps` class attribute).

---

## `ui.tsx` pattern (`set_react_page`)

UI is defined in a client-side codebase (`www/index.html` + JS, or built from `src/ui.tsx`). Minimal server-side primitives for apps whose UI lives in the client. Examples in `examples/ui-tsx/`. See `DESIGN.md` for the architectural rationale.

### Python public API

| Feature | Status | Notes |
|---------|--------|-------|
| `set_react_page(path="www/index.html")` | Working | Configures a Shiny Express app to serve a static `index.html`; auto-discovers HTMLDependencies from traditional Shiny renderers and injects the shinyreact dep |
| `@reactive_output` | Working | Renderer for `ui.tsx` outputs — server returns any `Jsonifiable` value, the client picks it up via `useShinyOutputValue()` |
| `send_message(session, id, data)` | Working | Server-to-client custom message helper for `ui.tsx` apps |

### JS bridge hooks (`js/src/shiny-react/`)

Vendored from `@posit/shiny-react`; bundled into `js/dist/shinyreact.js` (IIFE) and re-exported on `window.shinyreact`. Used by both the `ui.tsx` and `app.py` pattern apps.

| Feature | Status | Notes |
|---------|--------|-------|
| `useShinyInput` | Working | Full `[value, setValue]` — stable defaultValue via `useRef`; debounce + priority options; optional `type=` routes values through a Shiny input handler (e.g. `shiny.datetime`) |
| `useShinyInputValue` | Working | Read-only consumer hook — returns just the current value, with mount-order-safe subscription to a producer registered elsewhere |
| `useSetShinyInput` | Working | Write-only producer hook — returns just the setter; same `defaultValue` + options as `useShinyInput`; optional `type=` routes values through a Shiny input handler (e.g. `shiny.datetime`) |
| `useShinyOutputValue` | Working | Subscribes to a Shiny output binding; receives `Jsonifiable` values from `reactive_output`. Returns just the value |
| `useShinyOutputStatus` | Working | Returns the lifecycle status — `"pending" \| "ready" \| "recalculating" \| "error"` — for a Shiny output binding |
| `useShinyMessageHandler` | Working | Stable handler ref; no unnecessary re-registration on inline arrow functions |
| `useShinyInitialized` | Working | Tracks Shiny client initialization state |
| `useShinyBusy` | Working | App-wide busy/idle state hook |
| `ShinyModuleProvider` | Working | Namespace support for module patterns |
| `ImageOutput` | Working | Renders `@render.plot()` outputs; prop is `id` (not `outputId`) |
| `ShinyOutput` | Working | Component that renders a container for traditional Shiny output bindings (`bindAll`/`unbindAll` lifecycle) |

### Examples

| Example | Status | Description |
|---------|--------|-------------|
| [01-hello](../examples/ui-tsx/01-hello/) | Working | Smallest `ui.tsx` app — Python server with reactive logic only, plus a static React client (no JSX, no bundler). Side-by-side comparison of client-only state vs. server-routed state to highlight websocket latency |
| [02-columns](../examples/ui-tsx/02-columns/) | Working | Drag-between-columns demo on the `ui.tsx` pattern, no build step. Server owns data only (one `move_item` event input), client owns UI. ~20 lines of server logic vs. ~80 in the `render.ui` version |
| [03-columns-shadcn](../examples/ui-tsx/03-columns-shadcn/) | Working | Same drag-between-columns demo as 02, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyreact`. Identical Python server to 02 |
| [04-shadcn](../examples/ui-tsx/04-shadcn/) | Working | shadcn/ui + Tailwind v4. Mirrors `wch/shiny-react examples/5-shadcn` and adds a side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@reactive_output`, client renders) comparison; Plotly hover/click/select events round-trip through `useShinyInput` |
| [05-temperature](../examples/ui-tsx/05-temperature/) | Working | Temperature conversion app demonstrating simple reactive data flow |
| [06-data-frame](../examples/ui-tsx/06-data-frame/) | Working | Embeds `@render.data_frame` via `ShinyOutput` and `set_react_page()` |
| [07-plotly](../examples/ui-tsx/07-plotly/) | Working | Embeds `@render_plotly` via `ShinyOutput` and `set_react_page()` |
| [08-input-handler](../examples/ui-tsx/08-input-handler/) | Working | Demonstrates `useShinyInput` with `type="shiny.datetime"` — client sends unix seconds; server `input.when()` is a `datetime.datetime` via Shiny's built-in handler |

### Design decisions

- **Server owns data, client owns UI.** `reactive_output` ships pure data; the React client renders. Eliminates `render.ui`-driven dynamic UI patterns, per-item observer churn, and server-side ID bookkeeping.
- **`set_react_page()` serves static + Shiny side-by-side.** Inside a Shiny Express app, `shinyreact.set_react_page()` reads `www/index.html` and serves it as the page body alongside reactive computation. The Python file contains reactive logic only; the `www/` directory contains `index.html` and (optionally) a bundled JS app.
- **No build step required.** The default path uses `React.createElement` directly from a hand-written `app.js` (see ex. 01/02). Apps that want JSX or a component library opt into Vite (see ex. 03/04).
- **Vite lib-mode IIFE for build path.** Bundled `ui.tsx` apps externalize React to `window.shinyreact` to share the bundled React instance with shinyreact's hooks and avoid duplicate React copies.
