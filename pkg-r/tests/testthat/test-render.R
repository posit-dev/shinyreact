test_that(".render_transform turns a Node into the wire list", {
  val <- shinyreact:::.render_transform(node(
    "Card",
    props = list(title = "Hi")
  ))
  expect_identical(val$root, "auto_001")
  expect_identical(val$elements$auto_001$type, "Card")
  expect_identical(val$elements$auto_001$props, list(title = "Hi"))
})

test_that(".render_transform passes a raw list through", {
  expect_identical(
    shinyreact:::.render_transform(list(key = "value", count = 42L)),
    list(key = "value", count = 42L)
  )
})

test_that(".render_transform returns NULL for NULL", {
  expect_null(shinyreact:::.render_transform(NULL))
})

test_that("render_reactive returns a shiny render function", {
  r <- render_reactive(node("Card", props = list(title = "Hi")))
  expect_type(r, "closure")
  # createRenderFunction marks the closure; just confirm it's callable shape.
  expect_true(is.function(r))
})
