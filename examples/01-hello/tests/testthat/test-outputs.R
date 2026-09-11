# Pins app.R's outputs as the client sees them, using shiny::testServer() --
# inputs in, output values out, with no browser and no client.
#
# test-histogram.R next door pins the *math* by reimplementing app.R's two
# lines, because that logic lives inside server(). This file drives server()
# itself, so it pins what the app actually answers with. The Python
# counterpart is test_outputs.py beside them, which does the same thing with
# shiny.testserver.test_server().
#
# Run it from the app directory, the way a user of the app would:
#
#   Rscript -e 'shiny::runTests()'
#   Rscript -e 'testthat::test_dir("tests/testthat")'
#
# The shinyreact package's own suite also runs it, via
# pkg-r/tests/testthat/test-examples.R.
#
# app_dir is "../../" from tests/testthat/, the same default AppDriver uses.
app_dir <- testthat::test_path("..", "..")

test_that("dist_data is the {breaks, counts} the client draws", {
  shiny::testServer(app_dir, {
    session$setInputs(bins = 9)

    expect_named(output$dist_data, c("breaks", "counts"))
    # Mirrors COUNTS_9 in test_faithful.py and test-histogram.R.
    expect_equal(
      unclass(output$dist_data$counts),
      c(16L, 37L, 30L, 16L, 14L, 57L, 67L, 29L, 6L)
    )
    expect_equal(unclass(output$dist_data$breaks)[[1]], 43)
    expect_equal(unclass(output$dist_data$breaks)[[10]], 96)
  })
})

test_that("dist_caption pluralizes on the bin count", {
  shiny::testServer(app_dir, {
    session$setInputs(bins = 9)
    expect_equal(output$dist_caption, "272 eruptions in 9 bins")

    session$setInputs(bins = 1)
    expect_equal(output$dist_caption, "272 eruptions in 1 bin")
    expect_equal(unclass(output$dist_data$counts), 272L)
    expect_equal(unclass(output$dist_data$breaks), c(43, 96))
  })
})

test_that("the vectors carry I(), so a one-bin result is a JSON array", {
  # The class is the behavior: without it toJSON() emits `272` where the
  # client expects `[272]`. test-histogram.R pins the serialization; this
  # pins that app.R really applies it.
  shiny::testServer(app_dir, {
    session$setInputs(bins = 1)
    expect_s3_class(output$dist_data$counts, "AsIs")
    expect_s3_class(output$dist_data$breaks, "AsIs")
  })
})

test_that("both outputs are NULL before the client's first bins message", {
  # app.R returns NULL explicitly rather than using req(), so there is no
  # silent error to reach the client console.
  shiny::testServer(app_dir, {
    expect_null(output$dist_data)
    expect_null(output$dist_caption)
  })
})
