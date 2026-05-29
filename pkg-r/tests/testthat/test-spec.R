test_that("element() builds an Element with defaults", {
  el <- element("TextInput")
  expect_s3_class(el, "shinyreact::Element")
  expect_identical(el@type, "TextInput")
  expect_identical(el@props, list())
  expect_identical(el@children, list())
})

test_that("element() rejects a non-scalar or empty type", {
  expect_error(element(""), "non-empty")
  expect_error(element(c("a", "b")), "single")
})

test_that("element() rejects unnamed props", {
  expect_error(element("X", props = list(1, 2)), "named")
})

test_that("element() children must be length-1 character keys", {
  expect_error(element("X", children = list(1)), "character")
  ok <- element("X", children = list("k1", "k2"))
  expect_identical(ok@children, list("k1", "k2"))
})

test_that("spec() requires root to be present in elements", {
  els <- list(a = element("Card"))
  s <- spec("a", els)
  expect_s3_class(s, "shinyreact::Spec")
  expect_error(spec("missing", els), "root")
})

test_that("node() collects children via ...", {
  n <- node("Card", node("Divider"), props = list(title = "Hi"))
  expect_s3_class(n, "shinyreact::Node")
  expect_identical(n@type, "Card")
  expect_identical(n@props, list(title = "Hi"))
  expect_length(n@children, 1)
  expect_s3_class(n@children[[1]], "shinyreact::Node")
})

test_that("node() children must be Node objects", {
  expect_error(node("Card", "text"), "Node")
  expect_error(node("Card", 42), "Node")
})
