# Mirrors pkg-py/tests/test_wire_tap.py — the two taps present the same
# methods and semantics, so their unit suites assert the same behaviors on the
# same frames. The real-browser walkthrough is
# spikes/201-wire-verification/shinytest2-ws-frames.R; Python's is
# pkg-py/tests/playwright/test_wire_frames.py.

# A stand-in for shinytest2::AppDriver: $get_logs() returning websocket rows
# in shinytest2's shape (send/recv-prefixed JSON in `message`).
fake_app <- function(messages) {
  list(
    get_logs = function() {
      data.frame(
        location = rep("chromote", length(messages)),
        level = rep("websocket", length(messages)),
        message = messages,
        stringsAsFactors = FALSE
      )
    }
  )
}

frame <- function(direction, x) {
  paste0(direction, " ", jsonlite::toJSON(x, auto_unbox = TRUE))
}

test_that("wire_tap validates its app argument", {
  skip_if_not_installed("shinytest2")
  expect_error(wire_tap(list()), "get_logs")
  expect_error(
    wire_tap(list(get_logs = function() data.frame(location = "x"))),
    "level"
  )
})

test_that("all_output_values returns per-output values in order", {
  skip_if_not_installed("shinytest2")
  tap <- wire_tap(fake_app(c(
    frame("recv", list(values = list(a = 1, b = "x"))),
    frame("recv", list(values = list(a = 2))),
    frame("send", list(data = list(a = 99))) # wrong direction: ignored
  )))
  expect_identical(tap$all_output_values("a"), list(1L, 2L))
  expect_identical(tap$all_output_values("b"), list("x"))
  expect_identical(tap$all_output_values("missing"), list())
})

test_that("all_input_values matches bare and typed wire ids", {
  skip_if_not_installed("shinytest2")
  tap <- wire_tap(fake_app(c(
    frame("send", list(data = list("bins:shinyreact.default" = 30))),
    frame("send", list(data = list(bins = 5))),
    frame("send", list(data = list(binsight = 1))), # not a match
    frame("recv", list(values = list(bins = 7))) # wrong direction: ignored
  )))
  expect_identical(tap$all_input_values("bins"), list(30L, 5L))
})

test_that("all_messages filters by type", {
  skip_if_not_installed("shinytest2")
  tap <- wire_tap(fake_app(c(
    frame(
      "recv",
      list(custom = list(shinyReactMessage = list(id = "notify", data = 1)))
    ),
    frame(
      "recv",
      list(custom = list(shinyReactMessage = list(id = "other", data = 2)))
    ),
    frame(
      "recv",
      list(custom = list(shinyReactMessage = list(id = "notify", data = 3)))
    )
  )))
  expect_identical(tap$all_messages("notify"), list(1L, 3L))
  expect_identical(tap$all_messages("nope"), list())
})

test_that("expect_* matches an object with identical() and a fn by truthiness", {
  skip_if_not_installed("shinytest2")
  tap <- wire_tap(fake_app(c(
    frame("recv", list(values = list(a = list(n = 1)))),
    frame("recv", list(values = list(a = list(n = 2))))
  )))
  expect_identical(
    tap$expect_output_value("a", list(n = 1L), timeout = 0),
    list(n = 1L)
  )
  expect_identical(
    tap$expect_output_value("a", function(v) v$n == 2, timeout = 0),
    list(n = 2L)
  )
})

test_that("expect_* cursor consumes an ordered subsequence", {
  skip_if_not_installed("shinytest2")
  tap <- wire_tap(fake_app(c(
    frame("send", list(data = list(bins = 30))),
    frame("send", list(data = list(bins = 5))),
    frame("send", list(data = list(bins = 30)))
  )))
  tap$expect_input_value("bins", 30L, timeout = 0)
  tap$expect_input_value("bins", 5L, timeout = 0)
  # The second 30 is strictly later than the 5 the cursor sits on.
  tap$expect_input_value("bins", 30L, timeout = 0)
  # Nothing is left past the cursor.
  expect_error(
    tap$expect_input_value("bins", 30L, timeout = 0),
    "no matching value"
  )
})

test_that("a matcher error is a non-match and is reported on timeout", {
  skip_if_not_installed("shinytest2")
  # A shape-blind matcher errors on the first value and must still reach the
  # second. (Unlike Python, an early JSON `null` output value is dropped by
  # fromJSON — see ?wire_tap — so the error here comes from a wrong shape.)
  tap <- wire_tap(fake_app(c(
    frame("recv", list(values = list(a = "oops"))),
    frame("recv", list(values = list(a = list(n = 1))))
  )))
  expect_identical(
    tap$expect_output_value("a", function(v) v$n == 1, timeout = 0),
    list(n = 1L)
  )

  tap2 <- wire_tap(fake_app(
    frame("recv", list(values = list(a = "oops")))
  ))
  expect_error(
    tap2$expect_output_value("a", function(v) stop("boom"), timeout = 0),
    "Last matcher error"
  )
})

test_that("non-JSON payloads are ignored", {
  skip_if_not_installed("shinytest2")
  tap <- wire_tap(fake_app(c("recv not json", "recv [1, 2, 3]")))
  expect_identical(tap$all_output_values("a"), list())
})

test_that("wire_tap works end-to-end against the 01-hello example", {
  # The one real-browser test: inst/examples-shiny/01-hello is a copy of
  # examples/01-hello (app.R + www/) so it ships with the installed package.
  # Python's real-browser counterpart is
  # pkg-py/tests/playwright/test_wire_frames.py.
  skip_if_not_installed("shinytest2")
  skip_if_not_installed("chromote")
  skip_on_cran()

  app_dir <- system.file("examples-shiny", "01-hello", package = "shinyreact")
  skip_if(!nzchar(app_dir), "examples-shiny/01-hello not installed")

  app <- shinytest2::AppDriver$new(
    app_dir,
    options = list(shiny.trace = TRUE)
  )
  withr::defer(app$stop())
  app$wait_for_idle()

  tap <- wire_tap(app)

  # client -> server: the untyped input rides the shinyreact.default handler
  # and the first delivered value is the hook's defaultValue (30).
  tap$expect_input_value("bins", 30L)

  # server -> client: dist_data binned the *waiting* column (~43-96 min), not
  # `eruptions` (~1.6-5.1 min); breaks[[1]] alone distinguishes them. Every
  # one of the 272 observations lands in a bin.
  dist <- tap$expect_output_value("dist_data", function(d) {
    d$breaks[[1]] == 43 && sum(unlist(d$counts)) == 272
  })
  expect_length(dist$counts, 30L)

  # 01-hello uses no send_message(); the channel history is simply empty.
  expect_length(tap$all_messages("notify"), 0L)
})
