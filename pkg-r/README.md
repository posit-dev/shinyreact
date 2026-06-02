# shinyreact (R)

<!-- badges: start -->
[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![check-r](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml)
[![check-js](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml)
<!-- badges: end -->

JSON-driven React rendering infrastructure for [Shiny](https://shiny.posit.co/). shinyreact is pure plumbing: it lets downstream packages deliver React component trees from R, and ships zero UI components of its own. The same JSON wire format and JavaScript bundle back both the R and [Python](https://github.com/posit-dev/shinyreact/tree/main/pkg-py) packages.

## Overview

shinyreact gives R Shiny two ways to drive a React front end:

- **`app.R` pattern** — describe the UI as R objects with `node()` and render them with `render_react()`. The server owns the UI.
- **`ui.tsx` pattern** — write the UI in a client React codebase and bootstrap it from R with `page_react_html()`. The server owns only reactive computation.

Either way, downstream packages register the React components, and shinyreact handles the wire format, the output binding, and server-to-client messaging.

## Installation

shinyreact is pre-release and not yet on CRAN. Install the development version from GitHub (the package lives in the `pkg-r/` subdirectory of the monorepo):

```r
# install.packages("pak")
pak::pak("posit-dev/shinyreact/pkg-r")
```

## Usage

A minimal `app.R` (the `app.R` pattern). The thin component helpers wrap `node()` to mirror the React components registered in `hello_world.js`:

```r
library(shiny)
library(shinyreact)

card <- function(title, ...) node("Card", ..., props = list(title = title))

ui <- page_react(
  # ... your htmlDependency for the registered React components ...
  ui_output_react("hello")
)

server <- function(input, output, session) {
  output$hello <- render_react({
    card(
      "Hello Shiny React!",
      htmltools::tags$small("A shinyreact x htmltools demo")
    )
  })
}

shinyApp(ui, server)
```

`render_react()` walks a `node()` tree (which may interleave htmltools tags, `HTML()`, and strings) into the JSON wire tree. Any other JSON-serializable value passes through unchanged for `useShinyOutputValue()` hooks on the React side. Push data to the client with `send_message()`.

See [`examples/app-r/01-hello-world/`](https://github.com/posit-dev/shinyreact/tree/main/examples/app-r/01-hello-world) for the complete runnable app, including the registered components.

## Get started

- **Function reference:** <https://posit-dev.github.io/shinyreact/r>
- **Examples:** [`examples/app-r/`](https://github.com/posit-dev/shinyreact/tree/main/examples/app-r) (the `app.R` pattern) and [`examples/ui-tsx-r/`](https://github.com/posit-dev/shinyreact/tree/main/examples/ui-tsx-r) (the `ui.tsx` pattern)
- **Feature inventory:** [`docs/features.md`](https://github.com/posit-dev/shinyreact/blob/main/docs/features.md)
- **Which pattern?** [`docs/app-py-vs-ui-tsx.md`](https://github.com/posit-dev/shinyreact/blob/main/docs/app-py-vs-ui-tsx.md)
