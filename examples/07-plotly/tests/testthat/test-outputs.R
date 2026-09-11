# Pins app.R's outputs with shiny::testServer() -- no browser, no client.
#
# The Python counterpart is test_scatter.py beside it, which does the same
# thing with shiny.testserver.test_server(). Both exist to pin this example's
# central claim from the server side: a widget renderer produces its value
# with no *Output() placeholder anywhere.
#
# Run it from the app directory, the way a user of the app would:
#
#   Rscript -e 'shiny::runTests()'
#
# The shinyreact package's own suite also runs it, via
# pkg-r/tests/testthat/test-examples.R.
app_dir <- testthat::test_path("..", "..")

# app.R calls plotly::renderPlotly() inside server(), so every testServer()
# call here -- not just the scatter test -- needs plotly installed.
testthat::skip_if_not_installed("plotly")

test_that("greeting counts the points", {
  shiny::testServer(app_dir, {
    session$setInputs(num_points = 50)
    expect_equal(output$greeting, "Showing 50 random points")

    # No singular special case.
    session$setInputs(num_points = 1)
    expect_equal(output$greeting, "Showing 1 random points")
  })
})

test_that("greeting is NULL before the client's first message", {
  # app.R returns NULL explicitly rather than using req(), so no silent error
  # reaches the client console -- unlike `scatter`, which does use req().
  shiny::testServer(app_dir, {
    expect_null(output$greeting)
  })
})

test_that("scatter renders a plotly widget with no plotlyOutput() anywhere", {
  shiny::testServer(app_dir, {
    session$setInputs(num_points = 50)

    # renderPlotly() hands the client a JSON string carrying the figure, with
    # the widget's HTML dependencies attached as an attribute -- the React
    # side's ShinyOutput is what mounts it, and page_react() pushes those deps
    # after the flush.
    expect_s3_class(output$scatter, "json")
    expect_match(output$scatter, '"type":"scatter"', fixed = TRUE)
    dep_names <- vapply(
      attr(output$scatter, "deps"),
      `[[`,
      character(1),
      "name"
    )
    expect_true("plotly-main" %in% dep_names)
    # The *binding* JS is not in here: page_react() discovers it from the
    # render function and pushes it as a shinyreact-deps message instead,
    # which is what pkg-r/tests/testthat/test-dep-discovery.R covers.
    expect_false("plotly-binding" %in% dep_names)
  })
})
