# Pins the wire-level `(test)` leaves in this example's FEATURES.md for app.R:
# the JSON that actually crosses the websocket, read with shinyreact::wire_tap().
#
# test-histogram.R pins the *math* by reimplementing app.R's two lines. This
# file pins the *contract*: which input id the client sends, what the server
# answers with, and that moving the slider produces fresh payloads. The
# Python real-browser counterpart is pkg-py/tests/playwright/test_wire_frames.py.
#
# Run it from this directory, the way a user of the app would:
#
#   Rscript -e 'shinytest2::test_app()'
#
# The shinyreact package's own suite also runs it, via
# pkg-r/tests/testthat/test-examples.R, which sources it from this directory so
# AppDriver's default app_dir (test_path("../../")) resolves to the app either
# way.

# Drive the React-owned <input type="range">. shinytest2's set_inputs() needs a
# Shiny input binding, and useShinyInput() registers none, so set the value
# through the native setter and fire the `input` event React listens for.
# (A raw `change` event, or assigning `el.value`, is ignored by React.)
set_bins <- function(app, n) {
  app$get_js(sprintf(
    "
    const el = document.getElementById('bins');
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
      .set.call(el, '%d');
    el.dispatchEvent(new Event('input', { bubbles: true }));
    ",
    n
  ))
}

test_that("the wire carries the histogram contract", {
  skip_if_not_installed("shinytest2")
  skip_if_not_installed("chromote")
  skip_on_cran()

  app <- shinytest2::AppDriver$new(
    options = list(shiny.trace = TRUE)
  )
  withr::defer(app$stop())
  app$wait_for_idle()

  tap <- shinyreact::wire_tap(app)

  # client -> server: the hook's defaultValue (30) is the first value sent.
  tap$expect_input_value("bins", 30L)

  # server -> client: dist_data bins the *waiting* column (43-96 min). Mirrors
  # COUNTS_30 in test_faithful.py and test-histogram.R, count for count.
  dist <- tap$expect_output_value("dist_data", function(d) {
    length(d$counts) == 30
  })
  expect_equal(dist$breaks[[1]], 43)
  expect_equal(dist$breaks[[31]], 96)
  # fmt: skip
  expect_equal(
    unlist(dist$counts),
    c(
      1L, 8L, 7L, 10L, 6L, 12L, 15L, 7L, 4L, 13L,
      4L, 7L, 3L, 3L, 3L, 9L, 8L, 6L, 17L, 27L,
      18L, 13L, 26L, 16L, 8L, 6L, 9L, 2L, 3L, 1L
    )
  )
  tap$expect_output_value("dist_caption", "272 eruptions in 30 bins")

  # reactivity: moving the slider re-sends the input and produces a fresh
  # payload. The cursor guarantees these are strictly later values.
  set_bins(app, 1)
  tap$expect_input_value("bins", 1L)
  one <- tap$expect_output_value("dist_data", function(d) {
    length(d$counts) == 1
  })
  # I() in app.R keeps the one-bin vectors as JSON arrays; simplifyVector =
  # FALSE in wire_tap means a scalar would arrive as a bare number, not a list.
  expect_type(one$counts, "list")
  expect_equal(one$counts[[1]], 272L)
  expect_equal(unlist(one$breaks), c(43, 96))
  tap$expect_output_value("dist_caption", "272 eruptions in 1 bin")

  # 01-hello uses no send_message(); the channel history is simply empty.
  expect_length(tap$all_messages("notify"), 0L)
})
