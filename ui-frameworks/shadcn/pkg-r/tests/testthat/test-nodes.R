test_that("leaf helpers build shadcn nodes with the right type and props", {
  b <- shadcn_button("go", "Go")
  expect_s3_class(b, "shinyreact_node")
  expect_equal(b$type, "shadcn:Button")
  expect_equal(b$props$input_id, "go")
  expect_equal(b$props$label, "Go")
})

test_that("class passes through as className", {
  expect_equal(shadcn_badge("Hi", class = "mt-2")$props$className, "mt-2")
})

test_that("leaf helpers reject stray positional args via check_dots_empty", {
  expect_error(shadcn_badge("Hi", "oops"))
})

test_that("container helpers carry child nodes", {
  card <- shadcn_card(shadcn_button("go", "Go"), title = "Demo")
  expect_equal(card$type, "shadcn:Card")
  expect_equal(card$props$title, "Demo")
  expect_length(card$children, 1)
})

test_that("builder helpers return plain list specs, not nodes", {
  it <- shadcn_menu_item("save", "Save")
  expect_type(it, "list")
  expect_false(inherits(it, "shinyreact_node"))
})
