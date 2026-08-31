#' Tap the websocket wire of a shinytest2 app
#'
#' `wire_tap()` gives tests access to the JSON payloads that actually crossed
#' the Shiny websocket — the contract between the server and the React client.
#' Create the [shinytest2::AppDriver] with `options = list(shiny.trace = TRUE)`
#' so shinytest2 records every websocket frame in `app$get_logs()`; the tap
#' parses those frames into per-channel views.
#'
#' Cross-channel frame order (which output lands first, how outputs batch into
#' a single `values` frame, busy/progress interleaving) is reactive-scheduling
#' coincidence, not contract — so the tap deliberately does not expose a global
#' frame stream. Within one channel (one output id, one message type, one
#' input id) wire order is guaranteed, and the `expect_*` methods consume it
#' through a cursor: each expectation scans the recorded history from just
#' past the previous match, so values that arrive between checks are never
#' missed — capture is lossless; polling only decides when to re-scan.
#' Successive expectations on one channel therefore assert an ordered
#' subsequence.
#'
#' The Python counterpart is `shinyreact.playwright.WireTap`, with the same
#' methods and semantics. One small divergence: [jsonlite::fromJSON()] maps a
#' JSON `null` output value to `NULL`, indistinguishable from an absent key,
#' so early `output: null` frames are dropped where Python sees `None`.
#'
#' @param app A [shinytest2::AppDriver] started with
#'   `options = list(shiny.trace = TRUE)` — or any object whose `$get_logs()`
#'   returns a data frame with `location`, `level`, and `message` columns in
#'   shinytest2's shape.
#' @return A list of functions:
#' \describe{
#'   \item{`all_output_values(output_id)`}{Every value the server delivered
#'     for `output_id`, in order.}
#'   \item{`all_messages(message_id)`}{Every [send_message()] payload of
#'     `message_id`, in order.}
#'   \item{`all_input_values(input_id)`}{Every value the client sent for
#'     `input_id`, in order. Matches the bare id or any `id:type` wire id
#'     (e.g. the implicit `:shinyreact.default` suffix), so use the id you
#'     wrote in `useShinyInput()`.}
#'   \item{`expect_output_value(output_id, matcher, timeout = 10)`}{Retrying
#'     expectation. A function `matcher` is satisfied by a truthy return; any
#'     other object is compared with [identical()]. Returns the matched value
#'     invisibly, or errors at `timeout` (seconds). A matcher that errors on a
#'     value's shape counts as a non-match.}
#'   \item{`expect_message(message_id, matcher, timeout = 10)`}{As above,
#'     for [send_message()] payloads.}
#'   \item{`expect_input_value(input_id, matcher, timeout = 10)`}{As above,
#'     for client-sent input values.}
#' }
#' @examplesIf FALSE
#' app <- shinytest2::AppDriver$new(
#'   "path/to/app",
#'   options = list(shiny.trace = TRUE)
#' )
#' tap <- wire_tap(app)
#'
#' # The JSON 30 parses to integer; identical() needs the right type.
#' tap$expect_input_value("bins", 30L)
#' tap$expect_output_value("dist_data", function(d) {
#'   d$breaks[[1]] == 43 && sum(unlist(d$counts)) == 272
#' })
#' @export
wire_tap <- function(app) {
  if (!requireNamespace("shinytest2", quietly = TRUE)) {
    cli::cli_abort(c(
      "{.fun wire_tap} requires the {.pkg shinytest2} package.",
      "i" = "Install it with {.code install.packages(\"shinytest2\")}."
    ))
  }
  if (!is.function(app$get_logs)) {
    cli::cli_abort(
      "{.arg app} must have a {.fun $get_logs} method
       (a {.cls shinytest2::AppDriver})."
    )
  }
  probe <- app$get_logs()
  missing_cols <- setdiff(c("location", "level", "message"), names(probe))
  if (!is.data.frame(probe) || length(missing_cols) > 0) {
    cli::cli_abort(c(
      "{.code app$get_logs()} must return a data frame with
       {.field location}, {.field level}, and {.field message} columns.",
      "i" = "Did you create the {.cls AppDriver} with
             {.code options = list(shiny.trace = TRUE)}?"
    ))
  }

  cursors <- new.env(parent = emptyenv())

  # Raw (direction, frame) stream. Cross-channel order in here is NOT a
  # contract; the per-channel views below are the public surface.
  frames <- function() {
    logs <- app$get_logs()
    ws <- logs[logs$location == "chromote" & logs$level == "websocket", ]
    lapply(seq_len(nrow(ws)), function(i) {
      msg <- ws$message[[i]]
      frame <- tryCatch(
        jsonlite::fromJSON(
          sub("^(send|recv) ", "", msg),
          simplifyVector = FALSE
        ),
        error = function(e) NULL
      )
      list(direction = sub("^(send|recv) .*$", "\\1", msg), frame = frame)
    })
  }

  all_output_values <- function(output_id) {
    vals <- lapply(frames(), function(x) {
      if (identical(x$direction, "recv")) x$frame$values[[output_id]]
    })
    Filter(Negate(is.null), vals)
  }

  all_messages <- function(message_id) {
    vals <- lapply(frames(), function(x) {
      if (!identical(x$direction, "recv")) {
        return(NULL)
      }
      # Payload shape {id, data} per protocol/surface.json.
      msg <- x$frame$custom$shinyReactMessage
      if (!is.null(msg) && identical(msg$id, message_id)) {
        msg["data"] # keep NULL data distinguishable from "no match"
      }
    })
    lapply(Filter(Negate(is.null), vals), `[[`, "data")
  }

  all_input_values <- function(input_id) {
    out <- list()
    for (x in frames()) {
      if (!identical(x$direction, "send")) {
        next
      }
      data <- x$frame$data
      if (!is.list(data)) {
        next
      }
      hits <- names(data) == input_id |
        startsWith(names(data), paste0(input_id, ":"))
      out <- c(out, unname(data[hits]))
    }
    out
  }

  expect_channel <- function(key, values_fn, matcher, timeout) {
    matches <- if (is.function(matcher)) {
      matcher
    } else {
      function(v) identical(v, matcher)
    }
    deadline <- Sys.time() + timeout
    last_error <- NULL
    repeat {
      vals <- values_fn()
      start_val <- cursors[[key]]
      start <- if (is.null(start_val)) 1L else start_val + 1L
      i <- start
      while (i <= length(vals)) {
        # A matcher that errors on a value's shape (e.g. an early NULL-ish
        # payload) is a non-match, not a test error; the timeout message
        # reports the last error.
        matched <- tryCatch(isTRUE(matches(vals[[i]])), error = function(e) {
          last_error <<- conditionMessage(e)
          FALSE
        })
        if (matched) {
          # Consume through the match: the next expectation on this channel
          # scans strictly-later values (ordered subsequence semantics).
          # Non-matching values stay visible via the all_* views.
          cursors[[key]] <- i
          return(invisible(vals[[i]]))
        }
        i <- i + 1L
      }
      if (Sys.time() >= deadline) {
        cli::cli_abort(c(
          "{.field {key}}: no matching value within {timeout}s.",
          "i" = "Scanned {length(vals) - start + 1L} value{?s} past the cursor.",
          if (!is.null(last_error)) {
            c("x" = "Last matcher error: {last_error}")
          }
        ))
      }
      Sys.sleep(0.25)
    }
  }

  list(
    all_output_values = all_output_values,
    all_messages = all_messages,
    all_input_values = all_input_values,
    expect_output_value = function(output_id, matcher, timeout = 10) {
      expect_channel(
        paste0("output/", output_id),
        function() all_output_values(output_id),
        matcher,
        timeout
      )
    },
    expect_message = function(message_id, matcher, timeout = 10) {
      expect_channel(
        paste0("message/", message_id),
        function() all_messages(message_id),
        matcher,
        timeout
      )
    },
    expect_input_value = function(input_id, matcher, timeout = 10) {
      expect_channel(
        paste0("input/", input_id),
        function() all_input_values(input_id),
        matcher,
        timeout
      )
    }
  )
}
