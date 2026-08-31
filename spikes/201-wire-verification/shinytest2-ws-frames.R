# Prototype for #201: assert websocket wire payloads from R via shinytest2.
#
# `AppDriver$new(options = list(shiny.trace = TRUE))` makes shinytest2
# subscribe to chromote's Network.webSocketFrameSent/Received and record every
# frame in `app$get_logs()` (location == "chromote", level == "websocket",
# message prefixed "send "/"recv "). This is the R counterpart of
# pkg-py/tests/playwright/test_wire_frames.py — same tap, same methods.
# wire_tap() is exported from the shinyreact package; unit tests for it live
# in pkg-r/tests/testthat/test-wire-tap.R.
#
# `wire_tap()` exposes per-channel views only. Cross-channel frame order
# (which output lands first, how outputs batch into `values` frames,
# busy/progress interleaving) is reactive-scheduling coincidence, not
# contract — so it is not exposed. Within one channel wire order is real,
# and the `expect_*` methods consume it through a cursor: each expectation
# scans the recorded history from just past the previous match, so values
# that arrive between checks are never missed — capture is lossless, polling
# only decides when to re-scan.
#
# Run (from repo root): NOT_CRAN=true Rscript spikes/201-wire-verification/shinytest2-ws-frames.R
# Requires: shinytest2, chromote-discoverable Chrome, shinyreact installed.

library(shinytest2)
library(shinyreact) # exports wire_tap()

# Run from the repo root.
app <- AppDriver$new(
  "examples/01-hello",
  options = list(shiny.trace = TRUE)
)
withr::defer(app$stop())
app$wait_for_idle()

tap <- wire_tap(app)

# client -> server: the untyped input rides the shinyreact.default handler
# and the first delivered value is the hook's defaultValue (30). identical()
# needs the right storage type: the JSON 30 parses to integer.
tap$expect_input_value("bins", 30L)

# server -> client: dist_data binned the *waiting* column (~43-96 min), not
# `eruptions` (~1.6-5.1 min); breaks[[1]] alone distinguishes them. Every one
# of the 272 observations lands in a bin.
tap$expect_output_value("dist_data", function(d) {
  d$breaks[[1]] == 43 && sum(unlist(d$counts)) == 272
})

# 01-hello uses no send_message(); the channel history is simply empty.
stopifnot(length(tap$all_messages("notify")) == 0)

cat("wire_tap assertions passed:\n")
cat("  expect_input_value('bins', 30L)\n")
cat("  expect_output_value('dist_data', breaks[1]==43 & sum(counts)==272)\n")

# ponytail: driving the React slider needs run_js with React's native value
# setter (set_inputs() only knows shiny input bindings); add when the helper
# graduates from spike to shipped test API.
