# extract_config() / extract_restore_payload() live in helper-config.R (they
# are shared with test-bookmark.R and test-bookmark-restore-context.R).

config_html <- function(values) {
  testthat::local_mocked_bindings(.restore_input_values = function() values)
  as.character(config_script_tag())
}

test_that("config_script_tag round-trips U+2028 / U+2029 (#183)", {
  # These were a hazard when the payload was a JS string literal (issue
  # #183). In the JSON script tag they are inert; this pins the round-trip.
  # Mirrors Python's test_config_script_tag_line_separators_round_trip.
  values <- list(ls = "A\u2028B", ps = "C\u2029D")
  html <- config_html(values)
  expect_identical(extract_restore_payload(html), values)
})

test_that("config_script_tag preserves full numeric precision", {
  # jsonlite::toJSON() defaults to digits = 4, which would silently round
  # bookmarked numeric values. shiny's toJSON() uses 16 significant digits;
  # Python's json.dumps() is exact.
  values <- list(pi_ish = 3.14159265358979, tiny = 1e-12)
  payload <- extract_restore_payload(config_html(values))
  expect_equal(payload$pi_ish, 3.14159265358979, tolerance = 1e-15)
  expect_equal(payload$tiny, 1e-12, tolerance = 1e-20)
})

test_that("config_script_tag serializes NULL as null, matching Python", {
  # jsonlite emits a bare NULL element as `{}`; shiny's toJSON() passes
  # null = "null", so it round-trips as NULL like Python's json.dumps(None).
  payload <- extract_restore_payload(config_html(list(a = NULL, b = 1L)))
  expect_true("a" %in% names(payload))
  expect_null(payload$a)
  expect_identical(payload$b, 1L)
})

test_that("config_script_tag survives quotes, newlines and tabs", {
  values <- list(q = "it's \"me\"", ctrl = "line1\nline2\twith\ttabs")
  expect_identical(extract_restore_payload(config_html(values)), values)
})

test_that("config_script_tag escapes a closing script tag", {
  # Every "<" in the payload is emitted as the JSON escape \\u003c, so the
  # only actual </script> is the one closing our injected tag, and no
  # <script> can be smuggled in. Mirrors Python's
  # test_config_script_tag_escapes_closing_script_tag.
  values <- list(foo = "</script><script>alert(1)</script>")
  html <- config_html(values)
  expect_identical(
    lengths(regmatches(html, gregexpr("</script>", html, fixed = TRUE))),
    1L
  )
  expect_no_match(html, "<script>alert(1)", fixed = TRUE)
  expect_identical(extract_restore_payload(html), values)
})

test_that("config_script_tag round-trips __proto__ and constructor keys", {
  # The client reads the tag with JSON.parse, which treats "__proto__" and
  # "constructor" as ordinary own properties (unlike a bare JS object
  # literal, where "__proto__" is the prototype setter).
  values <- list(`__proto__` = "evil", constructor = "x", ok = 1L)
  html <- config_html(values)
  expect_no_match(html, "window.shinyreact._restore", fixed = TRUE)
  expect_identical(
    extract_restore_payload(html),
    list(`__proto__` = "evil", constructor = "x", ok = 1L)
  )
})

test_that("protocol fixture round-trips through the config tag", {
  # protocol/fixtures/config-restore.json is the shared wire-contract fixture
  # (see protocol/README.md); the Python and JS suites round-trip the same
  # file. Mirrors Python's test_protocol_fixture_round_trips.
  fixture <- file.path(
    testthat::test_path(),
    "..", "..", "..",
    "protocol", "fixtures", "config-restore.json"
  )
  skip_if_not(
    file.exists(fixture),
    "monorepo sources not available (installed-package run)"
  )
  expected <- jsonlite::fromJSON(brio::read_file(fixture), simplifyVector = FALSE)
  expect_identical(expected$protocolVersion, .protocol_version)
  html <- config_html(expected$restore)
  expect_equal(extract_config(html), expected, tolerance = 1e-12)
})
