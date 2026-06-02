test_that(".render_transform walks a node to a react wire tree", {
  val <- shinyreact:::.render_transform(node(
    "Card",
    props = list(title = "Hi")
  ))
  p <- jsonlite::fromJSON(
    jsonlite::toJSON(val, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_identical(p$type, "react")
  expect_identical(p$name, "Card")
  expect_identical(p$props$title, "Hi")
})

test_that(".render_transform walks a bare htmltools tag", {
  val <- shinyreact:::.render_transform(htmltools::tags$div("hi"))
  p <- jsonlite::fromJSON(
    jsonlite::toJSON(val, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_identical(p$type, "tag")
  expect_identical(p$name, "div")
})

test_that(".render_transform passes a raw list through unchanged", {
  expect_identical(
    shinyreact:::.render_transform(list(key = "value", count = 42L)),
    list(key = "value", count = 42L)
  )
})

test_that(".render_transform passes a bare string through unchanged", {
  expect_identical(
    shinyreact:::.render_transform("raw json string"),
    "raw json string"
  )
})

test_that(".render_transform returns NULL for NULL", {
  expect_null(shinyreact:::.render_transform(NULL))
})

test_that("should_walk dispatches correctly across types", {
  expect_true(shinyreact:::should_walk(node("Card")))
  expect_true(shinyreact:::should_walk(htmltools::tags$div()))
  expect_true(shinyreact:::should_walk(htmltools::tagList(htmltools::tags$div())))
  expect_false(shinyreact:::should_walk("a string"))
  expect_false(shinyreact:::should_walk(htmltools::HTML("<b>x</b>")))
  expect_false(shinyreact:::should_walk(list(rows = 1, cols = 2)))
  expect_false(shinyreact:::should_walk(42L))
})

test_that(".render_transform warns when a walked tree carries dependencies", {
  dep <- htmltools::htmlDependency("d", "1.0.0", src = c(href = "x"))
  expect_warning(
    shinyreact:::.render_transform(node("Card", htmltools::tags$div("a"), dep)),
    "HTMLDependency"
  )
})

test_that("render_reactive returns a shiny render function", {
  r <- render_reactive(node("Card"))
  expect_s3_class(r, "shiny.render.function")
})
