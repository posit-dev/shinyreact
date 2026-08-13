test_that("reactive_output returns a shiny render function", {
  r <- reactive_output(list(a = 1, b = 2))
  expect_s3_class(r, "shiny.render.function")
})
