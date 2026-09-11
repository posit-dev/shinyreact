# shinyreact <a href="https://posit-dev.github.io/shinyreact/r/"><img src="man/figures/logo.svg" align="right" height="139" alt="shinyreact hex logo" /></a>

<!-- badges: start -->
[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![check-r](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-r.yaml)
<!-- badges: end -->

shinyreact lets you write the UI of a [Shiny](https://shiny.posit.co/) app as a [React](https://react.dev/) client you own, while the R server contains only reactive computation. It provides the bridge between the two and ships zero UI components itself. The same [JavaScript bundle](https://posit-dev.github.io/shinyreact/js/) backs the [Python package](https://posit-dev.github.io/shinyreact/py/), so one React client works against an `app.R` or an `app.py` server. The [full site](https://posit-dev.github.io/shinyreact/) covers all three.

## Installation

shinyreact is not yet on CRAN. Install the development version from GitHub:

```r
# install.packages("pak")
pak::pak("posit-dev/shinyreact/pkg-r")
```

## Usage

`page_react()` discovers `www/ui.js` (and `www/ui.css`, if present) and serves them as the page. `reactive_output()` publishes any JSON-serializable value to the client's `useShinyOutputValue()` hook:

```r
library(shiny)
library(shinyreact)

server <- function(input, output, session) {
  output$greeting <- reactive_output({
    paste0("Hello, ", input$name, "!")
  })
}

shinyApp(page_react(), server)
```

The matching `www/ui.js`:

```js
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

ReactDOM.createRoot(document.body.appendChild(document.createElement("div"))).render(h(App));
```

Try a complete app without cloning:

```r
shiny::runGitHub("posit-dev/shinyreact", subdir = "examples/01-hello")
```

## Learn more

- `vignette("shinyreact")` walks through the `ui.tsx` pattern: inputs, outputs, messages, and embedding traditional Shiny renderers.
- [TSX files and JavaScript build tools](https://posit-dev.github.io/shinyreact/articles/tsx-and-build-tools.html) explains `.tsx`, JSX, TypeScript, and what `npm run build` does.
- [Testing](https://posit-dev.github.io/shinyreact/r/articles/testing.html) covers `shiny::testServer()` for driving a server with no browser, and `wire_tap()` for wire payloads in shinytest2 tests.
- [Agent Skills](https://posit-dev.github.io/shinyreact/r/articles/agent-skills.html) explains the skills that ship with the package for coding agents.
- The [examples catalog](https://github.com/posit-dev/shinyreact/blob/main/examples/README.md) lists runnable apps from no-build to Vite + HMR.
