# shinyreact examples

Runnable example apps for both `shinyreact` patterns, in both languages. See
[`docs/app-py-vs-ui-tsx.md`](../docs/app-py-vs-ui-tsx.md) for how the `app.py`/`app.R`
and `ui.tsx` patterns differ and which to choose.

## Python

### `app.py` pattern — UI defined as Python objects ([`app-py/`](app-py/))

| Example | Description |
|---------|-------------|
| [01-hello-world](app-py/01-hello-world/) | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via `Node` |
| [02-inputs](app-py/02-inputs/) | 10 input types (text, number, checkbox, radio, select, slider, date, button, file, batch form) |
| [03-outputs](app-py/03-outputs/) | Data table, statistics, matplotlib plot via `ImageOutput` |
| [04-messages](app-py/04-messages/) | Server-to-client messaging with `send_message`, auto-dismissing toasts |
| [05-shadcn](app-py/05-shadcn/) | Text processing, button events, matplotlib plot; shadcn look via plain CSS |
| [06-dashboard](app-py/06-dashboard/) | Sidebar nav with tab switching, metrics cards, CSS bar charts, data table, filters |
| [07-chat](app-py/07-chat/) | AI chat with streaming, themes, image upload. **Requires `OPENAI_API_KEY`** |
| [08-modules](app-py/08-modules/) | Three counter widgets using `ShinyModuleProvider` namespacing |
| [09-blended](app-py/09-blended/) | Tabbed sidebar layout, matplotlib plot, data table, settings panel |
| [10-columns](app-py/10-columns/) | Drag-between-columns demo; `render.ui`-driven approach |
| [12-express-demo](app-py/12-express-demo/) | Shiny **Express** mode: traditional Express UI (`ui.input_text`, `ui.input_slider`, `ui.layout_sidebar`) mixed with one custom `shinyreact` output rendering a Card of Badges + Button via a `render_react` subclass |
| [13-bookmarking](app-py/13-bookmarking/) | Bookmark restoration: URL query string (or server-stored state) hydrates `useShinyInput` initial values via a head `<script>` emitted by `page_react()` |
| [14-nesting](app-py/14-nesting/) | htmltools `tags.*` and `Node`s interleaved at arbitrary depth; static React component in page chrome + reactive `Node` with mixed htmltools/React children |
| [14-unified-ui-prototype](app-py/14-unified-ui-prototype/) | **`shinyui` prototype** (sibling package, not `shinyreact` core). Shiny **Core** demo of the class-per-component UI hierarchy (#69): each component is a class owning its handler, serializer, deps, `update()`, and server-side read accessors (`slider.value()`, `card.value_full_screen()`, `acc.open_panels()`) |
| [15-shinyui-with-blocks](app-py/15-shinyui-with-blocks/) | **`shinyui` prototype** (sibling package). Same component set as 14, in Shiny **Express** `with`-block form |

### `ui.tsx` pattern — UI defined in a React client ([`ui-tsx/`](ui-tsx/))

| Example | Description |
|---------|-------------|
| [01-hello](ui-tsx/01-hello/) | Smallest `ui.tsx` app — Python server with reactive logic only, plus a static React client (no JSX, no bundler). Side-by-side comparison of client-only state vs. server-routed state to highlight websocket latency |
| [02-columns](ui-tsx/02-columns/) | Drag-between-columns demo, no build step. Server owns data only (one `move_item` event input), client owns UI. ~20 lines of server logic vs. ~80 in the `render.ui` version |
| [03-columns-shadcn](ui-tsx/03-columns-shadcn/) | Same drag-between-columns demo as 02, rendered with real shadcn/ui `Card` + `Button` and lucide-react icons. Vite lib-mode IIFE build with React externalized to `window.shinyreact` |
| [04-shadcn](ui-tsx/04-shadcn/) | shadcn/ui + Tailwind v4. Side-by-side matplotlib (`@render.plot` + `ImageOutput`) vs. Plotly (data-only via `@reactive_output`, client renders); Plotly hover/click/select events round-trip through `useShinyInput` |
| [05-temperature](ui-tsx/05-temperature/) | Temperature conversion app demonstrating simple reactive data flow |
| [06-data-frame](ui-tsx/06-data-frame/) | Embeds `@render.data_frame` via `ShinyOutput` and `set_react_page()` |
| [07-plotly](ui-tsx/07-plotly/) | Embeds `@render_plotly` via `ShinyOutput` and `set_react_page()` |
| [08-input-handler](ui-tsx/08-input-handler/) | `useShinyInput` with `type="shiny.datetime"` — client sends unix seconds; server `input.when()` is a `datetime.datetime` via Shiny's built-in handler |
| [09-hmr](ui-tsx/09-hmr/) | React Fast Refresh in dev (Vite dev server alongside Shiny); the `app.py` and no-build `www/app.js` paths reload too |

## R

### `app.R` pattern — UI defined as R objects ([`app-r/`](app-r/))

| Example | Description |
|---------|-------------|
| [01-hello-world](app-r/01-hello-world/) | Card + TextInput + OutputDisplay composed via `node()`; direct port of `app-py/01-hello-world` |
| [02-inputs](app-r/02-inputs/) | ~10 input widget types; bookmark demo (URL bookmark restores inputs on reload) |
| [04-messages](app-r/04-messages/) | `send_message()` end-to-end; auto-dismissing toasts |

### `ui.tsx` pattern — UI defined in a React client ([`ui-tsx-r/`](ui-tsx-r/))

| Example | Description |
|---------|-------------|
| [01-hello](ui-tsx-r/01-hello/) | `page_react_html()` + `reactive_output()` data returns; direct port of `ui-tsx/01-hello` |
