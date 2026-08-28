# Pins the server-side `(test)` leaves in this example's FEATURES.md for app.R.
#
# This example ships three interchangeable servers over one www/ client, so the
# histogram they produce has to be the same one. app.R computes it with base
# R's hist(); test_faithful.py next door computes it with a hand-written binner
# in faithful.py. The golden counts below are asserted verbatim in both, and in
# ui.test.ts, which draws them.
#
# Run it from this directory, the way a user of the app would:
#
#   Rscript -e 'shiny::runTests()'
#   Rscript -e 'shinytest2::test_app()'
#   Rscript -e 'testthat::test_dir("tests/testthat")'
#
# The shinyreact package's own suite also runs it, via
# pkg-r/tests/testthat/test-examples.R, so a package change that breaks this
# example fails there too.
#
# It reimplements app.R's two lines rather than sourcing the app, because the
# logic lives inside server() where no test can reach it.

hist_counts <- function(values, n) {
  breaks <- seq(min(values), max(values), length.out = n + 1)
  hist(values, breaks = breaks, plot = FALSE)$counts
}

test_that("the Old Faithful waiting times are the shape the example claims", {
  # app.R uses base R's faithful; the Python servers read faithful.csv, which
  # is this same data exported.
  expect_equal(length(faithful$waiting), 272)
  expect_equal(min(faithful$waiting), 43)
  expect_equal(max(faithful$waiting), 96)
})

test_that("binning matches the Python binner, count for count", {
  # Mirrors COUNTS_9 / COUNTS_30 in test_faithful.py.
  expect_equal(
    hist_counts(faithful$waiting, 9),
    c(16L, 37L, 30L, 16L, 14L, 57L, 67L, 29L, 6L)
  )
  # fmt: skip
  expect_equal(
    hist_counts(faithful$waiting, 30),
    c(
      1L, 8L, 7L, 10L, 6L, 12L, 15L, 7L, 4L, 13L,
      4L, 7L, 3L, 3L, 3L, 9L, 8L, 6L, 17L, 27L,
      18L, 13L, 26L, 16L, 8L, 6L, 9L, 2L, 3L, 1L
    )
  )
})

test_that("every observation lands in exactly one bin", {
  for (n in c(1, 2, 9, 30, 50)) {
    counts <- hist_counts(faithful$waiting, n)
    expect_equal(length(counts), n)
    expect_equal(sum(counts), 272)
  }
})

test_that("one bin holds everything", {
  expect_equal(hist_counts(faithful$waiting, 1), 272L)
})

test_that("a value on an interior break belongs to the bin below it", {
  # (lo, hi], first bin inclusive. Mirrors
  # test_bins_are_half_open_with_an_inclusive_first_bin in test_faithful.py --
  # the Python binner used to truncate instead, which disagreed here.
  expect_equal(hist_counts(c(0, 5, 10), 2), c(2L, 1L))
})

test_that("a one-bin result serializes as a JSON array, not a scalar", {
  # app.R wraps the vectors in I() for exactly this reason: without it,
  # toJSON() would emit `43` where the client expects `[43]` and the SVG would
  # have nothing to draw.
  breaks <- seq(43, 96, length.out = 2)
  h <- hist(faithful$waiting, breaks = breaks, plot = FALSE)

  expect_equal(
    as.character(jsonlite::toJSON(
      list(counts = I(h$counts)),
      auto_unbox = TRUE
    )),
    '{"counts":[272]}'
  )
  expect_equal(
    as.character(jsonlite::toJSON(list(counts = h$counts), auto_unbox = TRUE)),
    '{"counts":272}'
  )
})
