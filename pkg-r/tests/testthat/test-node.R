test_that("node() builds an S3 shinyreact_node", {
  n <- node("Card", props = list(title = "Hi"))
  expect_s3_class(n, "shinyreact_node")
  expect_identical(n$type, "Card")
  expect_identical(n$props, list(title = "Hi"))
  expect_identical(n$children, list())
})

test_that("node() collects mixed children via ...", {
  n <- node("Card", node("Divider"), htmltools::tags$span("x"), "text", 42)
  expect_length(n$children, 4)
  expect_s3_class(n$children[[1]], "shinyreact_node")
  expect_s3_class(n$children[[2]], "shiny.tag")
  expect_identical(n$children[[3]], "text")
})

test_that("node() rejects an empty or non-scalar type", {
  expect_error(node(""), "non-empty")
  expect_error(node(c("a", "b")), "single")
})

test_that("node() rejects an NA type", {
  expect_error(node(NA_character_), "non-empty")
})

test_that("node() rejects unnamed props", {
  expect_error(node("X", props = list(1, 2)), "named")
})

test_that("a node walks to a react wire node", {
  parts <- serialize_ui(node(
    "Card",
    props = list(title = "Hi"),
    node("Divider")
  ))
  p <- jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_identical(p$type, "react")
  expect_identical(p$name, "Card")
  expect_identical(p$props$title, "Hi")
  expect_identical(p$children[[1]]$type, "react")
  expect_identical(p$children[[1]]$name, "Divider")
})
