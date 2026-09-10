# Get started with shinyreact

shinyreact implements the **`ui.tsx` pattern**: the UI lives in a
client-side React codebase, and the Shiny server contains only reactive
computation. The server never renders HTML. It publishes data, and the
client decides how to show it.

The pieces:

1.  [`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md)
    bootstraps the page. It discovers `www/ui.js` (and `www/ui.css`)
    next to `app.R` and serves them along with `shinyreact.js`, which
    installs React and the hooks at `window.shinyreact`.
2.  [`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
    publishes a JSON-serializable value under an output id.
3.  [`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
    pushes a one-off message to the client.
4.  On the client, `useShinyInput()` sends values to the server,
    `useShinyOutputValue()` reads what
    [`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
    published, and `useShinyMessageHandler()` receives
    [`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
    pushes.

## A minimal app

The app directory holds `app.R` and a `www/` folder:

    my-app/
    ├── app.R
    └── www/
        ├── ui.js
        └── ui.css   # optional

`app.R`:

``` r

library(shiny)
library(shinyreact)

ui <- page_react() # discovers www/ui.js + www/ui.css

server <- function(input, output, session) {
  output$greeting <- reactive_output({
    paste0("Hello, ", input$name, "!")
  })
}

shinyApp(ui, server)
```

`www/ui.js`, written without a build step. The bundle exposes `React`
and `ReactDOM`, so the client uses `React.createElement` instead of JSX:

``` js
const { React, ReactDOM, useShinyInput, useShinyOutputValue } = window.shinyreact;
const h = React.createElement;

function App() {
  const [name, setName] = useShinyInput("name", "world");
  const greeting = useShinyOutputValue("greeting");
  return h(
    "div",
    null,
    h("input", { value: name, onChange: (e) => setName(e.target.value) }),
    h("p", null, greeting)
  );
}

// The page has no mount div; create one and append it to <body>.
const root = ReactDOM.createRoot(
  document.body.appendChild(document.createElement("div"))
);
root.render(h(App));
```

Run it with `shiny::runApp("my-app")`. Typing in the box sends
`input$name` to the server; `output$greeting` recomputes and the
paragraph updates.

Apps that want JSX, TypeScript, or npm packages compile `src/ui.tsx` to
`www/ui.js` with a bundler such as Vite.
[`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md)
does not care how the file was produced. The [examples
catalog](https://github.com/posit-dev/shinyreact/blob/main/examples/README.md)
shows each tier, from no-build to Vite + HMR.

## Inputs

`useShinyInput(id, default)` registers a Shiny input and returns
`[value, setValue]`, like `React.useState`. Every `setValue` call is
sent to the server, where it arrives as `input$id`.

Until the client’s first value arrives, `input$id` is `NULL`. Guard for
that (or use [`req()`](https://rdrr.io/pkg/shiny/man/req.html)) in
outputs that depend on it:

``` r

output$dist <- reactive_output({
  n <- input$bins
  if (is.null(n)) {
    return(NULL)
  }
  hist(faithful$waiting, breaks = n, plot = FALSE)$counts
})
```

Values arrive as the JSON the client sent, with two conveniences: arrays
of scalars become atomic vectors (`c(0, 100)`), and `[]` stays
[`list()`](https://rdrr.io/r/base/list.html) rather than becoming
`NULL`. Pass `{ type: "shinyreact.asis" }` to `useShinyInput()` to
receive the parsed JSON untouched, or any other Shiny input-handler name
(such as `"shiny.datetime"`) to route the value through that handler.

For action buttons, start at `0` and increment on click, with the
debounce disabled so no click is coalesced:

``` js
const [n, setN] = useShinyInput("go", 0, { debounceMs: 0, priority: "event" });
```

## Outputs

[`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
is assigned to `output$id`. Whatever the expression returns is
serialized with jsonlite and delivered to `useShinyOutputValue("id")` on
the client, unchanged. Return lists for structured data. Use
[`I()`](https://rdrr.io/r/base/AsIs.html) to keep a length-one vector as
a JSON array:

``` r

output$dist_data <- reactive_output({
  h <- hist(faithful$waiting, breaks = input$bins, plot = FALSE)
  list(breaks = I(h$breaks), counts = I(h$counts))
})
```

The client can also observe an output’s lifecycle with
`useShinyOutputStatus("id")`, which is `"pending"` before the first
value, `"recalculating"` while the server recomputes, and `"ready"`
otherwise. Keep the previous value mounted while recalculating; only
show a placeholder when no value has ever arrived.

## Messages

[`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
pushes a payload the client handles once, outside the reactive output
graph:

``` r

observeEvent(input$save, {
  send_message(session, "notify", list(text = "Saved", level = "info"))
})
```

``` js
useShinyMessageHandler("notify", (msg) => toast(msg.text));
```

## Traditional Shiny renderers

Render functions from other packages still work. Assign them to
`output$id` as usual and render them on the client with the
`ShinyOutput` component, which binds the output element inside your
React tree:

``` r

output$plot <- plotly::renderPlotly({
  plotly::plot_ly(x = ~ faithful$waiting, type = "histogram")
})
```

``` js
const { ShinyOutput } = window.shinyreact;
h(ShinyOutput, { id: "plot", className: "plotly html-widget html-widget-output" });
```

No `plotlyOutput()` placeholder is needed. shinyreact discovers the
renderer’s JavaScript and CSS dependencies from the render function and
delivers them to the client automatically.

## Bookmarking

Pass `enableBookmarking = "url"` (or `"server"`) to
[`shinyApp()`](https://rdrr.io/pkg/shiny/man/shinyApp.html) as usual.
Restored input values are embedded in the page, and `useShinyInput()`
uses them as initial values instead of its default.

## Next steps

- [TSX files and JavaScript build
  tools](https://posit-dev.github.io/shinyreact/articles/tsx-and-build-tools.html)
  explains `.tsx`, JSX, TypeScript, and what `npm run build` does, for
  readers new to JavaScript tooling.
- [Testing wire
  payloads](https://posit-dev.github.io/shinyreact/r/articles/testing.html)
  shows how to assert the JSON that crosses the websocket with
  [`wire_tap()`](https://posit-dev.github.io/shinyreact/r/reference/wire_tap.md).
- The [JS reference](https://posit-dev.github.io/shinyreact/js/)
  documents every hook and component at `window.shinyreact`.
- [`DESIGN.md`](https://github.com/posit-dev/shinyreact/blob/main/DESIGN.md)
  explains why the pattern looks the way it does.
