# Features — `shinyreact`

The `shinyreact` package ships two first-class patterns. See [`docs/spa-vs-traditional.md`](spa-vs-traditional.md) for a side-by-side comparison and guidance on which to choose.

---

## Traditional pattern (`page_react` + `reactive_output`)

Server emits JSON specs that the client renders into a React tree using `shinyreact`'s in-house Spec walker (`js/src/renderer.tsx`). Lives at `pkg-py/src/shinyreact/`. Examples in `examples/traditional/`.

### Python public API

| Feature | Status | Notes |
|---------|--------|-------|
| `shinyreact.ui_output()` | Working | Creates output div with HTMLDependency; accepts `extra_deps` |
| `shinyreact.page_react()` | Working | Full-page React app with `#root` + the shinyreact HTMLDependency |
| `shinyreact.page_bare()` | Working | Bare HTML page wrapper |
| `@shinyreact.reactive_output` | Working | Renders `Spec` or passes raw JSON for `useShinyOutput` |
| `shinyreact.Spec` / `Element` | Working | Flat-map data model for component trees |
| `shinyreact.Node` | Working | Nested tree API; `.to_spec()` auto-flattens to `Spec` |
| `shinyreact.send_message()` | Working | Server-to-client custom messages |

### Examples

| Example | Status | Description |
|---------|--------|-------------|
| [01-hello-world](../examples/traditional/01-hello-world/) | Working | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via Spec |
| [02-inputs](../examples/traditional/02-inputs/) | Working | 10 input types (text, number, checkbox, radio, select, slider, date, button, file, batch form) |
| [03-outputs](../examples/traditional/03-outputs/) | Working | Data table, statistics, matplotlib plot via ImageOutput |
| [04-messages](../examples/traditional/04-messages/) | Working | Server-to-client messaging with send_message, auto-dismissing toasts |
| [05-shadcn](../examples/traditional/05-shadcn/) | Working | Text processing, button events, matplotlib plot; shadcn look via plain CSS |
| [06-dashboard](../examples/traditional/06-dashboard/) | Working | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters |
| [07-chat](../examples/traditional/07-chat/) | Needs API key | AI chat with streaming, themes, image upload; requires OPENAI_API_KEY |
| [08-modules](../examples/traditional/08-modules/) | Working | Three counter widgets using ShinyModuleProvider namespacing |
| [09-blended](../examples/traditional/09-blended/) | Working | Tabbed sidebar layout, matplotlib plot, data table, settings panel |
| [10-columns](../examples/traditional/10-columns/) | Working | Drag-between-columns demo; traditional `render.ui`-driven approach |

### Design decisions

- **Treat element keys as internal/opaque.** When using `Node`, element keys in the flat `elements` map (e.g., `"auto_001"`) are auto-generated internal plumbing. Callers can still manually construct `Spec(elements={...})` with arbitrary keys, so this is guidance rather than a hard API guarantee. These keys have no relationship to DOM IDs or Shiny input/output IDs: Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server needs to know about.
- **HTMLDependency mtime versioning for examples.** Shiny caches static files by `{name}-{version}` in the URL. During development, editing a JS file doesn't bust the cache if the version string is fixed. Examples use `version=str(int(file.stat().st_mtime))` so the version changes whenever the file is saved. Development convenience only — published packages should use fixed versions.
- **Downstream extension.** Downstream packages (e.g. `shinyshadcn`) ship their own IIFE bundle that calls `window.shinyreact.registerComponents(catalog, registry)` at load time, plus a Python render subclass with an overridden `transform()`. The package's `HTMLDependency` is injected on the UI side via `shinyreact.ui_output(id, extra_deps=[...])` (`reactive_output` does not read an `extra_deps` class attribute).

---

## SPA pattern (`ReactApp`)

Minimal server-side primitives for apps whose UI lives in a static (or built) React client. Examples in `examples/spa/`. See `DESIGN.md` for the architectural rationale.

### Python public API

| Feature | Status | Notes |
|---------|--------|-------|
| `ReactApp` | Working | App wrapper that serves a static `www/` directory (typically containing `index.html` + bundled JS) and runs a Shiny server alongside it |
| `@reactive_output` | Working | Renderer for SPA outputs — server returns any `Jsonifiable` value, the client picks it up via `useShinyOutput()` |
| `send_message(session, id, data)` | Working | Server-to-client custom message helper for SPA apps |

### JS bridge hooks (`js/src/shiny-react/`)

Vendored from `@posit/shiny-react`; bundled into `js/dist/shinyreact.js` (IIFE) and re-exported on `window.shinyreact`. Used by both the SPA and traditional pattern apps.

| Feature | Status | Notes |
|---------|--------|-------|
| `useShinyInput` | Working | Stable defaultValue via `useRef`; debounce + priority options |
| `useShinyOutput` | Working | Subscribes to a Shiny output binding; receives `Jsonifiable` values from `reactive_output` |
| `useShinyMessageHandler` | Working | Stable handler ref; no unnecessary re-registration on inline arrow functions |
| `useShinyInitialized` | Working | Tracks Shiny client initialization state |
| `useShinyBusy` | Working | App-wide busy/idle state hook |
| `ShinyModuleProvider` | Working | Namespace support for module patterns |
| `ImageOutput` | Working | Renders `@render.plot()` outputs; prop is `id` (not `outputId`) |

### Examples

| Example | Status | Description |
|---------|--------|-------------|
| [01-hello](../examples/spa/01-hello/) | Working | Smallest SPA app — Python server with reactive logic only, plus a static React client (no JSX, no bundler). Side-by-side comparison of client-only state vs. server-routed state to highlight websocket latency |
| [02-columns](../examples/spa/02-columns/) | Working | Drag-between-columns demo on the SPA pattern, no build step. Demonstrates the canonical SPA pattern: server owns data only (one `move_item` event input), client owns UI. ~20 lines of server logic vs. ~80 in the traditional `render.ui` version |
| [03-columns-shadcn](../examples/spa/03-columns-shadcn/) | Working | Same drag-between-columns demo as 02, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyreact`. Identical Python server to 02 |
| [04-shadcn](../examples/spa/04-shadcn/) | Working | shadcn/ui + Tailwind v4 SPA. Mirrors `wch/shiny-react examples/5-shadcn` and adds a side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@reactive_output`, client renders) comparison; Plotly hover/click/select events round-trip through `useShinyInput` |
| [05-temperature](../examples/spa/05-temperature/) | Working | Temperature conversion SPA demonstrating simple reactive data flow |

### Design decisions

- **Server owns data, client owns UI.** `reactive_output` ships pure data; the React client renders. Eliminates `render.ui`-driven dynamic UI patterns, per-item observer churn, and server-side ID bookkeeping.
- **ReactApp serves static + Shiny side-by-side.** The Python file contains reactive logic only; the `www/` directory contains `index.html` and (optionally) a bundled JS app.
- **No build step required.** The default path uses `React.createElement` directly from a hand-written `app.js` (see ex. 01/02). Apps that want JSX or a component library opt into Vite (see ex. 03/04).
- **Vite lib-mode IIFE for build path.** Bundled SPA apps externalize React to `window.shinyreact` to share the bundled React instance with shinyreact's hooks and avoid duplicate React copies.
