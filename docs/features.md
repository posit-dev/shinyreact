# Features — `shinyreact`

The `shinyreact` package ships two first-class patterns. See [`docs/app-py-vs-ui-tsx.md`](app-py-vs-ui-tsx.md) for a side-by-side comparison and guidance on which to choose.

---

## `app.py` pattern (`page_react` + `reactive_output`)

UI is defined as Python (or R) objects in the app file via `page_react()` / `Node`. The server emits a JSON wire tree that the client renders into a React tree using `shinyreact`'s in-house walker (`js/src/renderer.tsx`). Lives at `pkg-py/src/shinyreact/`. Examples in `examples/app-py/`.

### Python public API

| Feature | Status | Notes |
|---------|--------|-------|
| `shinyreact.ui_output()` | Working | Creates output div with HTMLDependency; accepts `extra_deps` |
| `shinyreact.page_react()` | Working | Full-page React app with `#root` + the shinyreact HTMLDependency |
| `shinyreact.page_bare()` | Working | Bare HTML page wrapper |
| `@shinyreact.reactive_output` | Working | Walks `Node`/htmltools content into the JSON wire tree, or passes raw JSON for `useShinyOutputValue` |
| `shinyreact.Node` | Working | Recursive component tree; `.to_dict()` serializes to the JSON wire tree |
| **Interleaved htmltools + React content** | Working | `Node` is a `Tagifiable`; htmltools `tags.*`/`HTML`/strings and `Node`s nest at arbitrary depth in one tree. Serialized to a discriminated-union wire format (`react` \| `tag` \| `text` \| `html`); HTML dependencies are harvested in the same traversal. Static `Node`s in page chrome are delivered via an inline `<script type="application/json">` inside a `.shinyreact-static` mount. See `examples/app-py/14-nesting` |
| `shinyreact.send_message()` | Working | Server-to-client custom messages |
| Bookmark restoration | Working | `page_react()` and `set_react_page()` emit a head `<script>` carrying restored input values; `useShinyInput` adopts them as initial values. URL and server-stored bookmark modes both supported |

### Examples

| Example | Status | Description |
|---------|--------|-------------|
| [01-hello-world](../examples/app-py/01-hello-world/) | Working | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via `Node` |
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
| [14-nesting](../examples/app-py/14-nesting/) | Working | htmltools `tags.*` and `Node`s interleaved at arbitrary depth; static React component in page chrome + reactive `Node` with mixed htmltools/React children |

### Design decisions

- **React keys are positional by default.** The wire tree is a recursive structure with no synthetic element-key map; React reconciles children positionally. For lists or reorderable content, pass an explicit `key` in a node's props (React reads it natively and it is not emitted as a DOM attribute). Component identity has no relationship to DOM IDs or Shiny input/output IDs — Shiny IDs are passed as component props (`input_id`, `output_id`) and are the only IDs the server needs to know about.
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

---

## R package (`pkg-r/`)

Mirrors the Python package API for R Shiny users. Pure plumbing — no UI components. Lives at `pkg-r/`. Install with `pak::local_install("pkg-r")`.

### `app.R` pattern (`page_react` + `render_reactive`)

UI is defined as R objects (`node()`, `spec()`, `element()`) in the app file via `page_react()`; the server returns trees from `render_reactive()`. Equivalent to the Python `app.py` pattern. Examples in `examples/app-r/`.

| Feature | Status | Notes |
|---------|--------|-------|
| `page_react(...)` | Working | Full-page React app with `#root` + page-level dep (bundle + bookmark restore script) |
| `page_bare(...)` | Working | Minimal HTML scaffold without `#root` |
| `ui_output(id, extra_deps = list())` | Working | Output div with `shinyreact-output` class and per-output dep; `extra_deps` merged via `attachDependencies()` |
| `render_reactive(expr)` | Working | Shiny renderer; calls `to_spec()` on the value and returns the plain list for Shiny to serialize. `NULL` passes through. |
| `node(type, ..., props = list())` | Working | Nested tree API; `to_spec(node())` auto-flattens to a `Spec` with generated keys |
| `spec(root, elements)` | Working | S7 `Spec` class; `root` must be in `names(elements)` |
| `element(type, props, children)` | Working | S7 `Element` class with validated children (list of length-1 character keys) |
| `to_spec(x)` | Working | S7 generic; identity for plain lists; error on unregistered S7 classes |
| `send_message(session, type, data)` | Working | Server-to-client custom message (`shinyReactMessage`) |
| Bookmark restoration | Working | `page_react()` and `page_react_html()` emit a head `<script>` carrying restored input values; `useShinyInput` adopts them as initial values. URL and server-stored bookmark modes both supported |

### `ui.tsx` pattern (`page_react_html`)

UI lives in `www/index.html` + JS; bootstrapped from R via `page_react_html()`. Server contains only reactive computation. Equivalent to the Python `ui.tsx` pattern. Examples in `examples/ui-tsx-r/`.

| Feature | Status | Notes |
|---------|--------|-------|
| `page_react_html(path = "www/index.html")` | Working | Reads a static HTML file and attaches the page-level dep (bundle + bookmark restore script). Pass as `ui` to `shinyApp()` |
| `page_react_dep()` | Working | `htmlDependency` for a downstream package's own JS/CSS bundle; mtime-versioned |
| `render_reactive(expr)` | Working | Returns any `Jsonifiable` value for `useShinyOutputValue()` hooks; raw lists pass through |
| `send_message(session, type, data)` | Working | Same as `app.R` pattern |

### JS bridge hooks

The shared JS bundle (`window.shinyreact`) is identical for R and Python apps. All hooks listed in the [JS bridge hooks table above](#js-bridge-hooks-jssrc-shiny-react) are accessible from R apps the same way — the client-side API is language-agnostic.

### Examples

| Example | Pattern | Status | Description |
|---------|---------|--------|-------------|
| [app-r/01-hello-world](../examples/app-r/01-hello-world/) | `app.R` | Working | Card + TextInput + OutputDisplay composed via `node()`; direct port of `app-py/01-hello-world` |
| [app-r/02-inputs](../examples/app-r/02-inputs/) | `app.R` | Working | ~10 input widget types; bookmark demo (URL bookmark restores inputs on reload) |
| [app-r/04-messages](../examples/app-r/04-messages/) | `app.R` | Working | `send_message()` end-to-end; auto-dismissing toasts |
| [ui-tsx-r/01-hello](../examples/ui-tsx-r/01-hello/) | `ui.tsx` | Working | `page_react_html()` + raw-JSON renderer return; direct port of `ui-tsx/01-hello` |

### Design decisions

- **`render_reactive()` returns a plain list.** `to_spec()` produces a plain R list; Shiny serializes it via its standard `jsonlite` call. `toJSON` / `.wire_json()` helpers are used for the bookmark payload and cross-language parity tests only — they are not on the output critical path.
- **Parity with Python is semantic.** Cross-language wire-format parity is verified by parsing both outputs and comparing structures; element-map key order is insignificant. Python `json.dumps` and R `jsonlite` differ in whitespace by design.
- **`shiny:::` for bookmark restore context.** R Shiny does not expose a public API for reading the restore context non-destructively. `bookmark.R` uses `shiny:::` internals, isolated in one thin wrapper, with a pinned `shiny` version floor in `DESCRIPTION`.
- **Downstream extension.** Downstream R packages supply S7 classes with `to_spec` methods and an `htmlDependency` injected via `ui_output(id, extra_deps = list(...))`. `render_reactive()` is the single rendering entry point — downstream packages register `to_spec` methods, not render wrappers.
