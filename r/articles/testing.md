# Testing

In a shinyreact app the contract between server and client is the JSON
that crosses the Shiny websocket: the values
[`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
delivers, the payloads
[`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
pushes, and the values `useShinyInput()` sends back. Both halves of this
article assert that JSON — the first with no browser at all, the second
inside a real one.

## Testing the server with `testServer()`

A `ui.tsx` server contains only reactive computation, so “this input
produces that output value” *is* the server.
[`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
is an ordinary render function, so
[`shiny::testServer()`](https://rdrr.io/pkg/shiny/man/testServer.html)
drives it with no browser and no client, and `output$id` is the JSON
value itself — no spec wrapper, no coercion:

``` r

test_that("dist_data bins the waiting column", {
  shiny::testServer(app_dir, {
    session$setInputs(bins = 9)

    expect_named(output$dist_data, c("breaks", "counts"))
    expect_equal(
      unclass(output$dist_data$counts),
      c(16L, 37L, 30L, 16L, 14L, 57L, 67L, 29L, 6L)
    )
    expect_equal(output$dist_caption, "272 eruptions in 9 bins")
  })
})
```

[`unclass()`](https://rdrr.io/r/base/class.html) is there because the
app wraps its vectors in [`I()`](https://rdrr.io/r/base/AsIs.html) so a
one-bin result serializes as `[272]` rather than `272` — the `AsIs`
class rides along on the value the test sees.

Pass a directory containing the app, or the `server` function itself.
Module ids are namespaced as the session sees them
(`` output$`counter-label` ``), or reachable through
`session$makeScope("counter")`; a module server can also be driven on
its own:

``` r

shiny::testServer(card_server, args = list(id = "left"), {
  session$setInputs(n = 7)
  expect_equal(output$label, "n=7")
})
```

[`testServer()`](https://rdrr.io/pkg/shiny/man/testServer.html)
**raises** rather than reporting a status. Reading an output whose
render function failed [`req()`](https://rdrr.io/pkg/shiny/man/req.html)
throws a silent error, which is how you assert that an output produced
nothing:

``` r

expect_error(output$answer, class = "shiny.silent.error")
```

`examples/01-hello` and `examples/07-plotly` both carry a
`tests/testthat/test-outputs.R` written this way, runnable from the app
directory with
[`shiny::runTests()`](https://rdrr.io/pkg/shiny/man/runTests.html).

The Python counterpart is `shiny.testserver.test_server()`, which
reports `.status` (`"ok"`, `"error"`, `"silent"`) instead of raising.

## Testing wire payloads with `wire_tap()`

[`wire_tap()`](https://posit-dev.github.io/shinyreact/r/reference/wire_tap.md)
records the payloads crossing the websocket in a
[shinytest2](https://rstudio.github.io/shinytest2/) test so you can
assert on them directly, without inspecting the rendered DOM. Reserve it
for what [`testServer()`](https://rdrr.io/pkg/shiny/man/testServer.html)
structurally cannot see: the values the *client* chooses to send, real
bindings, and real rendering.

### Setup

[`wire_tap()`](https://posit-dev.github.io/shinyreact/r/reference/wire_tap.md)
needs the shinytest2 package. Start the `AppDriver` with
`shiny.trace = TRUE` so every websocket frame is recorded in the app’s
logs:

``` r

test_that("dist_data bins the waiting column", {
  app <- shinytest2::AppDriver$new(
    app_dir,
    options = list(shiny.trace = TRUE)
  )
  withr::defer(app$stop())

  tap <- shinyreact::wire_tap(app)
  tap$expect_input_value("bins", 30L)
  tap$expect_output_value("dist_data", function(d) d$breaks[[1]] == 43)
})
```

### Matchers

Each `expect_*` function takes a matcher and retries until it matches or
a timeout (10 seconds by default) elapses:

- A **function** is satisfied by a truthy return value. A function that
  errors on a payload’s shape counts as a non-match, not a test failure.
- Any **other object** is compared with
  [`identical()`](https://rdrr.io/r/base/identical.html). JSON numbers
  parse to integer when they have no fraction, so compare against `30L`,
  not `30`.

There is one `expect_*` per channel:

| Function | Channel |
|----|----|
| `expect_output_value(id, matcher)` | values delivered for `output$id` |
| `expect_message(id, matcher)` | `send_message(session, id, ...)` payloads |
| `expect_input_value(id, matcher)` | values the client sent for `input$id` |

Successive expectations on one channel assert an ordered subsequence:
each scans from just past the previous match, so a value that arrives
between two checks is never missed.

### Full histories

To inspect everything that crossed a channel, use the `all_*` functions:

``` r

tap$all_output_values("dist_data")
tap$all_messages("notify")
tap$all_input_values("bins")
```

Input ids match the bare id or any `id:type` wire id, so use the id you
wrote in `useShinyInput()`.

### Python counterpart

`shinyreact.playwright.WireTap` in the Python package has the same
methods and semantics for Playwright tests. One divergence:
[`jsonlite::fromJSON()`](https://jeroen.r-universe.dev/jsonlite/reference/fromJSON.html)
maps a JSON `null` output value to `NULL`, indistinguishable from an
absent key, so early `null` frames are dropped in R where Python records
`None`.
