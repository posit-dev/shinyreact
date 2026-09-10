# Tap the websocket wire of a shinytest2 app

`wire_tap()` gives tests access to the JSON payloads that actually
crossed the Shiny websocket — the contract between the server and the
React client. Create the
[shinytest2::AppDriver](https://rstudio.github.io/shinytest2/reference/AppDriver.html)
with `options = list(shiny.trace = TRUE)` so shinytest2 records every
websocket frame in `app$get_logs()`; the tap parses those frames into
per-channel views.

## Usage

``` r
wire_tap(app)
```

## Arguments

- app:

  A
  [shinytest2::AppDriver](https://rstudio.github.io/shinytest2/reference/AppDriver.html)
  started with `options = list(shiny.trace = TRUE)` — or any object
  whose `$get_logs()` returns a data frame with `location`, `level`, and
  `message` columns in shinytest2's shape.

## Value

A list of functions:

- `all_output_values(output_id)`:

  Every value the server delivered for `output_id`, in order.

- `all_messages(message_id)`:

  Every
  [`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
  payload of `message_id`, in order.

- `all_input_values(input_id)`:

  Every value the client sent for `input_id`, in order. Matches the bare
  id or any `id:type` wire id (e.g. the implicit `:shinyreact.default`
  suffix), so use the id you wrote in `useShinyInput()`.

- `expect_output_value(output_id, matcher, timeout = 10)`:

  Retrying expectation. A function `matcher` is satisfied by a truthy
  return; any other object is compared with
  [`identical()`](https://rdrr.io/r/base/identical.html). Returns the
  matched value invisibly, or errors at `timeout` (seconds). A matcher
  that errors on a value's shape counts as a non-match.

- `expect_message(message_id, matcher, timeout = 10)`:

  As above, for
  [`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
  payloads.

- `expect_input_value(input_id, matcher, timeout = 10)`:

  As above, for client-sent input values.

## Details

Cross-channel frame order (which output lands first, how outputs batch
into a single `values` frame, busy/progress interleaving) is
reactive-scheduling coincidence, not contract — so the tap deliberately
does not expose a global frame stream. Within one channel (one output
id, one message type, one input id) wire order is guaranteed, and the
`expect_*` methods consume it through a cursor: each expectation scans
the recorded history from just past the previous match, so values that
arrive between checks are never missed — capture is lossless; polling
only decides when to re-scan. Successive expectations on one channel
therefore assert an ordered subsequence.

The Python counterpart is `shinyreact.playwright.WireTap`, with the same
methods and semantics. One small divergence:
[`jsonlite::fromJSON()`](https://jeroen.r-universe.dev/jsonlite/reference/fromJSON.html)
maps a JSON `null` output value to `NULL`, indistinguishable from an
absent key, so early `output: null` frames are dropped where Python sees
`None`.

## Examples

``` r
if (FALSE) {
app <- shinytest2::AppDriver$new(
  "path/to/app",
  options = list(shiny.trace = TRUE)
)
tap <- wire_tap(app)

# The JSON 30 parses to integer; identical() needs the right type.
tap$expect_input_value("bins", 30L)
tap$expect_output_value("dist_data", function(d) {
  d$breaks[[1]] == 43 && sum(unlist(d$counts)) == 272
})
}
```
