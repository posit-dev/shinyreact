test_that("leaf helpers build mui nodes with the right type and props", {
  b <- mui_button("go", "Go")
  expect_s3_class(b, "shinyreact_node")
  expect_equal(b$type, "mui:Button")
  expect_equal(b$props$input_id, "go")
  expect_equal(b$props$label, "Go")
})

test_that("class passes through as className", {
  expect_equal(mui_alert("Hi", class = "mt-2")$props$className, "mt-2")
})

test_that("leaf helpers reject stray positional args", {
  expect_error(mui_switch("id", "oops"))
})

test_that("container helpers carry child nodes", {
  card <- mui_card(mui_button("go", "Go"), title = "Demo")
  expect_equal(card$type, "mui:Card")
  expect_equal(card$props$title, "Demo")
  expect_length(card$children, 1)
})
