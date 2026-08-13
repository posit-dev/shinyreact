# Round-trip the JSON payload embedded by restore_script_tag(), mirroring
# `_extract_restore_payload()` in pkg-py/tests/test_bookmark_restore.py.
#
# The script body is shaped:
#   window.shinyreact._restore = JSON.parse(<js-string-literal>);
# Two unescape layers: the JS string literal (whose escapes are a subset of
# JSON's, so fromJSON reads it), then the inner JSON text.
extract_restore_payload <- function(html) {
  m <- regmatches(
    html,
    regexpr(
      'window\\.shinyreact\\._restore = JSON\\.parse\\(".*"\\);',
      html
    )
  )
  expect_length(m, 1L)
  literal <- sub(
    '^window\\.shinyreact\\._restore = JSON\\.parse\\((".*")\\);$',
    "\\1",
    m
  )
  inner <- jsonlite::fromJSON(literal, simplifyVector = TRUE)
  jsonlite::fromJSON(inner, simplifyVector = FALSE)
}

restore_html <- function(values) {
  testthat::local_mocked_bindings(.restore_input_values = function() values)
  as.character(restore_script_tag())
}

test_that("restore_script_tag escapes U+2028 / U+2029 (#183)", {
  # Legal in a JSON string, but JS line terminators -- and therefore illegal
  # inside a JS string literal. Emitting them raw produces a <script> block the
  # browser cannot parse, killing bookmark restore.
  values <- list(ls = "A\u2028B", ps = "C\u2029D")
  html <- restore_html(values)

  expect_no_match(html, "\u2028", fixed = TRUE)
  expect_no_match(html, "\u2029", fixed = TRUE)
  expect_match(html, "\\\\u2028", fixed = TRUE)
  expect_match(html, "\\\\u2029", fixed = TRUE)
  expect_identical(extract_restore_payload(html), values)
})

test_that("restore_script_tag preserves full numeric precision", {
  # jsonlite::toJSON() defaults to digits = 4, which would silently round
  # bookmarked numeric values. shiny's toJSON() uses 16 significant digits;
  # Python's json.dumps() is exact.
  values <- list(pi_ish = 3.14159265358979, tiny = 1e-12)
  payload <- extract_restore_payload(restore_html(values))
  expect_equal(payload$pi_ish, 3.14159265358979, tolerance = 1e-15)
  expect_equal(payload$tiny, 1e-12, tolerance = 1e-20)
})

test_that("restore_script_tag serializes NULL as null, matching Python", {
  # jsonlite emits a bare NULL element as `{}`; shiny's toJSON() passes
  # null = "null", so it round-trips as NULL like Python's json.dumps(None).
  payload <- extract_restore_payload(restore_html(list(a = NULL, b = 1L)))
  expect_true("a" %in% names(payload))
  expect_null(payload$a)
  expect_identical(payload$b, 1L)
})

test_that("restore_script_tag survives quotes, newlines and tabs", {
  values <- list(q = "it's \"me\"", ctrl = "line1\nline2\twith\ttabs")
  expect_identical(extract_restore_payload(restore_html(values)), values)
})

test_that("restore_script_tag escapes a closing script tag", {
  values <- list(foo = "</script><script>alert(1)</script>")
  html <- restore_html(values)
  # Only the tag we emit may close; the payload's "</" is neutralized to "<\\/".
  expect_identical(
    lengths(regmatches(html, gregexpr("</script>", html, fixed = TRUE))),
    1L
  )
  expect_identical(extract_restore_payload(html), values)
})

test_that("restore_script_tag round-trips __proto__ and constructor keys", {
  values <- list(`__proto__` = "evil", constructor = "x", ok = 1L)
  html <- restore_html(values)
  expect_match(html, "JSON.parse(", fixed = TRUE)
  expect_no_match(html, "window.shinyreact._restore = {", fixed = TRUE)
  expect_identical(
    extract_restore_payload(html),
    list(`__proto__` = "evil", constructor = "x", ok = 1L)
  )
})
