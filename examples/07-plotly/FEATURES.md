# examples/07-plotly — behavior

A Plotly widget rendered by the *server* (shinywidgets in Python,
`plotly::renderPlotly` in R) and mounted inside a React tree via `ShinyOutput`.
One `www/` client, two servers.

Format rules: `../README.md` § "Example behavior trees". `[py]` / `[r]` /
`[js]` mark a claim that holds only there.

## Server

- output `greeting` (`reactive_output`) → `"Showing N random points"`
  - `[r]` returns `NULL` while `input$num_points` is `NULL`; `req()` is
    deliberately avoided so the silent error does not reach the client console
  - `[py]` `input.num_points()` raises a silent exception before the first
    message
- output `scatter` — a Plotly figure of `N` standard-normal `(x, y)` points,
  seeded 42, title `"Random Scatter (N points)"`, margins l 40 / r 20 / t 40 /
  b 40
  - `[py]` `@render_plotly` from shinywidgets, `px.scatter` over
    `np.random.default_rng(42)`
  - `[r]` `plotly::renderPlotly` with `set.seed(42)` and `rnorm`
  - the two servers draw *different* points — the RNG streams differ — so this
    is not a cross-language parity claim
  - `[r]` uses `req(input$num_points)` here, unlike `greeting`
- there is no `output_widget()` / `plotlyOutput()` placeholder in either server
- the render function's binding JS is discovered and delivered automatically
  - `[py]` `set_react_page()` inlines the dependency into `<head>`
  - `[r]` `page_react()` cannot inline it (the UI is built before `server()`
    runs), so the deps are pushed after the flush as a `shinyreact-deps`
    custom message and the bundle re-runs `bindAll` — see the repo
    `FEATURES.md` § dependency discovery

## Client (`www/ui.js`)

- renders `null` until `useShinyInitialized()` is true
- `useShinyInput("num_points", 50)` — `<input type="range">`, `min` 10, `max`
  500, `id="num-points"`, default 100 ms debounce `(test)`
- `<ShinyOutput id="scatter" .../>` inside a 400px-tall div `(test)`
  - default `tagName` (`div`), so the element is `<div id="scatter">`
  - `className` is
    `"shiny-ipywidget-output plotly html-widget html-widget-output
    shiny-report-size"` — one element carrying both bindings' selectors
    `(test)`
    - `shiny-ipywidget-output` is what Python's shinywidgets binding matches
    - `plotly html-widget html-widget-output` mirrors R's
      `plotly::plotlyOutput()`
    - only the running server's binding JS is loaded, so the other side's
      classes are inert
  - `style` is `width: 100%; height: 100%`
- the greeting paragraph renders the raw `greeting` value
- the slider's current value is echoed next to it as plain text
- no mount container in the page — the client appends its own `<div>` to
  `<body>`
