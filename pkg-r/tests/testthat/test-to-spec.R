test_that("to_spec() passes plain lists through unchanged", {
  expect_identical(to_spec(list(a = 1)), list(a = 1))
  expect_identical(to_spec("hi"), "hi")
  expect_identical(to_spec(42L), 42L)
})

test_that("to_spec(node) flattens depth-first with auto keys", {
  n <- node("Card", node("Divider"), node("Text", props = list(value = "x")))
  out <- to_spec(n)
  expect_identical(out$root, "auto_001")
  expect_named(out$elements, c("auto_001", "auto_002", "auto_003"))
  expect_identical(out$elements$auto_001$type, "Card")
  expect_identical(out$elements$auto_001$children, list("auto_002", "auto_003"))
  expect_identical(out$elements$auto_002$type, "Divider")
  expect_identical(out$elements$auto_003$props, list(value = "x"))
})

test_that("to_spec(spec) normalizes to a plain list", {
  s <- spec("a", list(a = element("Card", props = list(title = "Hi"))))
  out <- to_spec(s)
  expect_identical(out$root, "a")
  expect_identical(out$elements$a$type, "Card")
  expect_identical(out$elements$a$props, list(title = "Hi"))
  expect_identical(out$elements$a$children, list())
})

test_that("to_spec(element) wraps a single element into a spec list", {
  out <- to_spec(element("Card"))
  expect_length(out$elements, 1)
  expect_identical(out$elements[[out$root]]$type, "Card")
})

test_that("to_spec(node) leaf has children == list()", {
  out <- to_spec(node("Leaf"))
  expect_identical(out$elements$auto_001$children, list())
})

test_that("to_spec(element) preserves empty children", {
  out <- to_spec(element("Card"))
  expect_identical(out$elements[[out$root]]$children, list())
})

test_that("to_spec(node) handles three levels of nesting", {
  out <- to_spec(node("A", node("B", node("C"))))
  expect_named(out$elements, c("auto_001", "auto_002", "auto_003"))
  expect_identical(out$elements$auto_001$children, list("auto_002"))
  expect_identical(out$elements$auto_002$children, list("auto_003"))
  expect_identical(out$elements$auto_003$type, "C")
  expect_identical(out$elements$auto_003$children, list())
})
