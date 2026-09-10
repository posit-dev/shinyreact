# shinyreact

shinyreact lets you write the UI of a [Shiny](https://shiny.posit.co/)
app as a [React](https://react.dev/) client you own, while the R server
contains only reactive computation. It provides the bridge between the
two and ships zero UI components itself. The same [JavaScript
bundle](https://posit-dev.github.io/shinyreact/js/) backs the [Python
package](https://posit-dev.github.io/shinyreact/py/), so one React
client works against an `app.R` or an `app.py` server. The [full
site](https://posit-dev.github.io/shinyreact/) covers all three.

## Installation

shinyreact is not yet on CRAN. Install the development version from
GitHub:

``` r

# install.packages("pak")
pak::pak("posit-dev/shinyreact/pkg-r")
```

## Usage

[`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md)
discovers `www/ui.js` (and `www/ui.css`, if present) and serves them as
the page.
[`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
publishes any JSON-serializable value to the client’s
`useShinyOutputValue()` hook:

``` r

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

ReactDOM.createRoot(document.body.appendChild(document.createElement("div"))).render(h(App));
```

Try a complete app without cloning:

``` r

shiny::runGitHub("posit-dev/shinyreact", subdir = "examples/01-hello")
```

## Learn more

- [`vignette("shinyreact")`](https://posit-dev.github.io/shinyreact/r/articles/shinyreact.md)
  walks through the `ui.tsx` pattern: inputs, outputs, messages, and
  embedding traditional Shiny renderers.
- [TSX files and JavaScript build
  tools](https://posit-dev.github.io/shinyreact/articles/tsx-and-build-tools.html)
  explains `.tsx`, JSX, TypeScript, and what `npm run build` does.
- [Testing wire
  payloads](https://posit-dev.github.io/shinyreact/r/articles/testing.html)
  covers
  [`wire_tap()`](https://posit-dev.github.io/shinyreact/r/reference/wire_tap.md)
  for shinytest2 tests.
- [Agent
  Skills](https://posit-dev.github.io/shinyreact/r/articles/agent-skills.html)
  explains the skills that ship with the package for coding agents.
- The [examples
  catalog](https://github.com/posit-dev/shinyreact/blob/main/examples/README.md)
  lists runnable apps from no-build to Vite + HMR.
