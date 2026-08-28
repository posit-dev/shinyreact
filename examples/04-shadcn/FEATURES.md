# examples/04-shadcn — behavior

A six-card dashboard on shadcn/ui + Tailwind v4 that puts every output style
side by side: server-rendered matplotlib, data-only Plotly drawn on the client,
a plain `@render.text`, an event button, and a text round-trip.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Data

- `sample_data`: 8 rows, columns `id` 1–8, `age` `[25, 30, 35, 28, 32, 27, 29,
  33]`, `score` `[85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6]`
- a module-level constant — no input filters it, every card sees all 8 rows

## Server (`app.py`, Express)

- `matplotlib.use("Agg")` is set before `set_react_page()`, so plotting works
  headless
- output `scatter_data` (`reactive_output`) → `{"age": [...], "score": [...]}`,
  column-oriented, `id` dropped
  - not reactive on any input — it recomputes only on session start
- output `processed_text` (`reactive_output`) → `input.user_text()` uppercased
  then reversed
  - empty or missing input → `""`, not `None`
- output `text_length` (`reactive_output`) → `len(input.user_text() or "")`
- output `render_text_demo` (`@render.text`, *not* `reactive_output`) →
  `render.text says: '<text>' (<n> chars)`; `""` when the input is empty
  - proves a traditional renderer's value is readable from
    `useShinyOutputValue` with no placeholder element
- output `button_response` (`reactive_output` + `@reactive.event(input
  .button_trigger, ignore_init=True)`) → `"Event received at: YYYY-MM-DD
  HH:MM:SS.mmm"`
  - millisecond field is zero-padded to 3 digits
  - `ignore_init=True`, so the hook's initial `0` does not fire it
- output `plot1` (`@render.plot`) → a matplotlib figure: scatter of age vs.
  score plus a red dashed degree-1 `np.polyfit` trend line over 100 points,
  axis labels `"Age"` / `"Score"`, title `"Age vs Score"`, grid at alpha 0.3
- the Plotly input ids (`plotly_hover`, `plotly_click`, `plotly_dblclick`,
  `plotly_xy_ranges`, `plotly_selection`) are written by the client but **no
  server output reads them** — they are observable via `input.*()` and nothing
  more
- `[py]` only — this example has no R server

## Build

- Vite IIFE lib mode, entry `src/ui.jsx`, out `www/ui.js` + `www/ui.css`
  (gitignored), `assetFileNames: "ui.[ext]"`, `cssCodeSplit: false`,
  `emptyOutDir: false`
- React externalized to `window.shinyreact.React` / `.ReactDOM`
- the lib `name` is `"ColumnsShadcn"`, copied from example 03 — cosmetic (IIFE
  globals are not read here), but it is not this example's name
- Tailwind v4 via `@tailwindcss/vite`; `src/index.css` declares the shadcn
  color tokens in an `@theme` block rather than pulling in a shadcn config
- Plotly comes from `plotly.js-basic-dist-min`, bundled into `ui.js` — it is
  not the shinywidgets/htmlwidgets binding used by example 07

## Client layout (`src/App.jsx`)

- renders `null` until `useShinyInitialized()` is true
- header, a `Separator`, then: `TextInputCard` + `ButtonEventCard` (2-up),
  `RenderTextCard` (full width), `PlotCard` + `PlotlyCard` (2-up),
  `PlotlyInfoCard` (full width)
- `md:grid-cols-2` — the paired rows stack on narrow screens

## Cards

- `TextInputCard`
  - `useShinyInput("user_text", "")` — default 100 ms debounce
  - shows `processed_text`, or `"No text entered yet"` when empty
  - shows `text_length` in a `Badge` as `"Length: N"`
- `ButtonEventCard`
  - `useShinyInput("button_trigger", 0, {debounceMs: 0, priority: "event"})`,
    incremented on click — the Shiny action-button idiom
  - shows `button_response`, or `"Click button to see response"` when empty
- `RenderTextCard`
  - reads the `@render.text` output through `useShinyOutputValue`
  - status `"recalculating"` → shows `"…"`; empty value → `"(empty — type in
    the box above)"`
- `PlotCard`
  - `<ImageOutput id="plot1">` — the server-rendered PNG, min height 300px
- `PlotlyCard` — client-side Plotly, `Plotly.react` in an effect keyed on the
  data
  - two traces: `"Observations"` markers (size 10, opacity 0.7) and a `"Trend"`
    red dashed line, whose slope/intercept are a least-squares fit computed in
    the browser, drawn between `min(age)` and `max(age)`
  - `showlegend: false`, `dragmode: "select"`, mode bar on, responsive
  - after the first render it publishes the figure's own axis ranges to
    `plotly_xy_ranges`
  - hover: a raw `mousemove` listener converts pixel → data coords with
    plotly's `_fullLayout` axis helpers, so `plotly_hover` updates continuously
    and not only over a point; positions outside the plot area are ignored
  - click: a DOM `click` listener publishes `plotly_click`
  - double-click is detected by hand — two clicks inside 300 ms — because
    plotly's drag layer captures the pointer and swallows the native
    `dblclick`; it publishes `plotly_dblclick` and resets the view
  - box-select publishes `plotly_selection` as `[{age, score}, ...]` on both
    `plotly_selecting` and `plotly_selected`
    - a `plotly_selected` with no points keeps the previous selection rather
      than clearing it
    - a `plotly_selected` carrying a range zooms to that box and then clears
      the selection state and the dashed rectangle
  - `Escape` resets the axes to autorange, but only while the cursor is inside
    the plot — a document-level key listener guarded by `mouseenter` /
    `mouseleave`
  - `plotly_relayout` republishes `plotly_xy_ranges`, reading explicit
    `xaxis.range[0]`-style keys when present and falling back to
    `_fullLayout` otherwise
  - the effect cleanup removes every listener, clears the pending click timer,
    and calls `Plotly.purge`
- `PlotlyInfoCard`
  - a pure reader: `useShinyInputValue` (no setter) on all five plotly ids
  - the values it shows come from client-side input state, not a server
    round-trip
  - hover/click/double-click render as `age=NN.N, score=NN.NN`; missing → `—`
  - range renders as `x=[a, b], y=[c, d]` to one decimal; missing → `—`
  - selection renders one `Badge` per point, or the prompt `"Drag to
    box-select points on the chart"`

## Not covered by tests

- the built bundle is gitignored and Plotly interaction is pointer-driven, so
  no unit test mounts this client
