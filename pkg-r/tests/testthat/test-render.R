test_that("reactive_output returns a shiny render function", {
  r <- reactive_output(list(a = 1, b = 2))
  expect_s3_class(r, "shiny.render.function")
})

test_that("reactive_output passes every JSON shape through unchanged", {
  # Mirrors Python's pass-through coverage in pkg-py/tests/test_reactive_output.py:
  # the value reaches the client exactly as the expression produced it, with no
  # spec wrapping and no coercion.
  server <- function(input, output, session) {
    output$obj <- reactive_output(list(a = 1, b = list(2, 3)))
    output$num <- reactive_output(42L)
    output$str <- reactive_output("hello")
    output$arr <- reactive_output(list(1, 2, 3))
    output$nul <- reactive_output(NULL)
  }
  shiny::testServer(server, {
    expect_identical(output$obj, list(a = 1, b = list(2, 3)))
    expect_identical(output$num, 42L)
    # A top-level string is JSON pass-through, not a wrapped text node.
    expect_identical(output$str, "hello")
    expect_identical(output$arr, list(1, 2, 3))
    expect_null(output$nul)
  })
})

test_that("reactive_output recomputes when its inputs change", {
  server <- function(input, output, session) {
    output$doubled <- reactive_output(list(value = input$n * 2))
  }
  shiny::testServer(server, {
    session$setInputs(n = 3)
    expect_identical(output$doubled, list(value = 6))
    session$setInputs(n = 10)
    expect_identical(output$doubled, list(value = 20))
  })
})

test_that("reactive_output attaches no UI placeholder or dependency", {
  # The client owns all UI. Python asserts `auto_output_ui() is None` and that
  # no `extra_deps` attribute exists; the R equivalents are that no output
  # element is registered (shiny's "no UI function provided" default stands in)
  # and that the render function smuggles in no html dependency.
  r <- reactive_output(list(a = 1))
  expect_length(htmltools::findDependencies(r), 0L)

  placeholder <- htmltools::renderTags(attr(r, "outputFunc")("my_id"))
  expect_match(placeholder$html, "No UI/output function provided")
  expect_no_match(placeholder$html, "my_id", fixed = TRUE)
  expect_length(placeholder$dependencies, 0L)
})
