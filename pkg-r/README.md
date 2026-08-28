# shinyreact (R)

<!-- badges: start -->
[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![check-r](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml)
[![check-js](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-js.yaml)
<!-- badges: end -->

React UI infrastructure for [Shiny](https://shiny.posit.co/). The Shiny server contains only reactive computation; the UI is a React client you own. shinyreact provides the bridge — it ships zero UI components itself. The same JavaScript bundle backs both the R and [Python](https://github.com/posit-dev/shinyreact/tree/main/pkg-py) packages.

## Overview

shinyreact implements the **`ui.tsx` pattern**: write the UI in a client React codebase and bootstrap it from R with `page_react_html()`. The server publishes data with `reactive_output()`, pushes messages with `send_message()`, and reads inputs sent by the client's `useShinyInput` hooks.

## Installation

shinyreact is pre-release and not yet on CRAN. Install the development version from GitHub (the package lives in the `pkg-r/` subdirectory of the monorepo):

```r
# install.packages("pak")
pak::pak("posit-dev/shinyreact/pkg-r")
```

## Usage

A minimal `app.R`. The UI lives in `www/` (`ui.js`, plus `ui.css` if you want styles — discovered automatically); the server owns only reactive computation:

```r
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

`reactive_output()` sends any JSON-serializable value through unchanged; the client reads it with `useShinyOutputValue("greeting")`. Push data to the client with `send_message()`.

Traditional Shiny renderers (e.g. `plotly::renderPlotly()`) work too, rendered client-side with the `ShinyOutput` React component — their binding JS/CSS is discovered from the render function and delivered to the client automatically, no `*Output()` placeholder needed.

See [`examples/01-hello/`](https://github.com/posit-dev/shinyreact/tree/main/examples/01-hello) for the complete runnable app (`app.R` alongside the equivalent `app.py`, sharing one `www/` client).

## Get started

- **Function reference:** <https://posit-dev.github.io/shinyreact/r>
- **Examples:** the [examples catalog](https://github.com/posit-dev/shinyreact/blob/main/examples/README.md)

## Agent Skills

The package ships two Agent Skills, so a coding agent can build a shinyreact
app without you pasting this README into it:

- **`shinyreact-build-app`** — build a `ui.tsx`-pattern app from scratch
- **`shinyreact-convert-app`** — port an existing Shiny app to the pattern

Agents using [btw](https://posit-dev.github.io/btw/) discover them automatically
once shinyreact is attached. To copy them into a project for Claude Code and
other skill-aware tools:

```r
btw::btw_skill_install_package("shinyreact")
```
