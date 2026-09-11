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

test_that("reactive_output is namespaced inside a module server", {
  # Mirrors test_module_namespaces_stay_isolated in
  # pkg-py/tests/test_in_memory_server.py, which drives the same app shape
  # through shiny.testserver.test_server(). The browser-level counterpart is
  # pkg-py/tests/playwright/test_module_namespaces.py; R has no e2e suite yet
  # (#194), so this is R's coverage of the claim.
  counter_server <- function(id) {
    moduleServer(id, function(input, output, session) {
      output$serverCount <- reactive_output(
        if (is.null(input$count)) 0L else input$count
      )
    })
  }
  server <- function(input, output, session) {
    counter_server("a")
    counter_server("b")
  }

  shiny::testServer(server, {
    session$setInputs(`a-count` = 3L)
    expect_identical(output$`a-serverCount`, 3L)
    # Namespace isolation: counter "b" is untouched.
    expect_identical(output$`b-serverCount`, 0L)
  })

  # The same ids through a scope, which is how a module's own test reads them.
  shiny::testServer(server, {
    a <- session$makeScope("a")
    a$setInputs(count = 2L)
    expect_identical(output$`a-serverCount`, 2L)
  })
})

test_that("reactive_output surfaces errors and silent errors to the test", {
  # Mirrors test_output_error_statuses in pkg-py/tests/test_in_memory_server.py
  # -- with a deliberate divergence in the *testing* API, not in shinyreact:
  # R's testServer() re-raises, so reading the output is the assertion, while
  # Python's test_server() reports `.status` / `.error` instead. Python also
  # keeps the previous value after a silent error where R does not
  # (posit-dev/py-shiny#2492).
  server <- function(input, output, session) {
    output$answer <- reactive_output({
      n <- input$n
      req(!is.null(n))
      if (n == 0) {
        stop("invalid number of 'breaks'")
      }
      paste0("ok: ", n)
    })
  }

  shiny::testServer(server, {
    # req() fails: a silent error, with no message.
    expect_error(output$answer, class = "shiny.silent.error")

    session$setInputs(n = 1)
    expect_identical(output$answer, "ok: 1")

    session$setInputs(n = 0)
    expect_error(output$answer, "invalid number of 'breaks'")

    # Recovering clears the error.
    session$setInputs(n = 2)
    expect_identical(output$answer, "ok: 2")
  })
})
