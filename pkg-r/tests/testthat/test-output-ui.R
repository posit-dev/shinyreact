# output_ui() is the R counterpart of the Python renderer's auto_output_ui()
# (exercised in pkg-py/tests/test_page_dep_harvest.py). The extraction itself
# is R-only (#203): Python renderers carry auto_output_ui() natively.

test_that("output_ui() builds the matching *Output() UI", {
  ui <- output_ui(shiny::renderText("hi"), "my_text")
  expect_s3_class(ui, "shiny.tag")
  expect_identical(as.character(ui), as.character(shiny::textOutput("my_text")))
})

test_that("output_ui() never evaluates the render expression", {
  ui <- output_ui(shiny::renderText(stop("boom")), "x")
  expect_s3_class(ui, "shiny.tag")
})

test_that("output_ui() works for renderImage (construction-only, no expr)", {
  # renderImage's render *call* needs a real file; extraction must not care.
  ui <- suppressWarnings(output_ui(shiny::renderImage({}), "img"))
  expect_match(as.character(ui), 'class="shiny-image-output"', fixed = TRUE)
  expect_match(as.character(ui), 'id="img"', fixed = TRUE)
})

test_that("output_ui() forwards outputArgs to the output function", {
  render_fn <- shiny::renderText("hi", outputArgs = list(inline = TRUE))
  expect_identical(
    as.character(output_ui(render_fn, "x")),
    as.character(shiny::textOutput("x", inline = TRUE))
  )
})

test_that("output_ui() surfaces htmlDependencies via findDependencies", {
  dep <- htmltools::htmlDependency(
    name = "fake-binding",
    version = "1.0.0",
    src = c(href = "fake"),
    script = "fake.js"
  )
  render_fn <- shiny::createRenderFunction(
    function() "value",
    transform = function(value, session, name, ...) value,
    outputFunc = function(id) {
      htmltools::attachDependencies(htmltools::div(id = id), dep)
    }
  )
  deps <- htmltools::findDependencies(output_ui(render_fn, "x"))
  expect_identical(deps[[1]]$name, "fake-binding")
})

test_that("output_ui() rejects non-render functions", {
  expect_error(output_ui(identity, "x"), "render function")
})

test_that("output_ui() aborts for a render function built outside createRenderFunction", {
  # The only way to reach the no-outputFunc branch (#234): createRenderFunction()
  # always substitutes a placeholder, so the attribute is absent only for render
  # functions hand-classed like this one.
  render_fn <- structure(
    function(...) "value",
    class = "shiny.render.function"
  )
  expect_error(output_ui(render_fn, "x"), "outputFunc")
  expect_null(output_ui_or_null(render_fn, "x"))
})

test_that("output_ui() on reactive_output yields shiny's dep-less placeholder", {
  # shiny substitutes a placeholder outputFunc ("No UI/output function
  # provided...") when a render function declares none, so reactive_output
  # yields that <pre> notice — with no dependencies, which is all the
  # dep-discovery harvest cares about.
  ui <- output_ui(reactive_output(42), "x")
  expect_match(as.character(ui), "No UI/output function provided")
  expect_length(htmltools::findDependencies(ui), 0)
})
