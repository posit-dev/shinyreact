test_that("default_input_handler preserves arrays of objects as a list of records", {
  records <- list(
    list(name = "a", size = 1L),
    list(name = "b", size = 2L)
  )
  expect_identical(default_input_handler(records), records)
  # A mixed array keeps its structure too -- Python would hand back
  # [{"a": 1}, 5], so flattening here would diverge.
  expect_identical(
    default_input_handler(list(list(a = 1L), 5L)),
    list(list(a = 1L), 5L)
  )
})

test_that("default_input_handler flattens scalar arrays to atomic vectors", {
  expect_equal(default_input_handler(list(0, 100)), c(0, 100))
  expect_equal(default_input_handler(list("a", "b")), c("a", "b"))
})

test_that("default_input_handler leaves scalars and single objects unchanged", {
  expect_identical(default_input_handler(5L), 5L)
  expect_identical(default_input_handler(list(a = 1L)), list(a = 1L))
})

test_that("default_input_handler keeps an empty array empty (not NULL)", {
  # Python's handler hands back []; shiny's default no-type coercion would
  # unlist() this to NULL, conflating "empty array" with "absent input" (#184).
  expect_identical(default_input_handler(list()), list())
})

test_that("default_input_handler preserves nested arrays", {
  # Shiny's default flattens [[1, 2], [3, 4]] to c(1, 2, 3, 4), destroying the
  # shape the React component sent; Python keeps the nesting (#184).
  expect_identical(
    default_input_handler(list(list(1, 2), list(3, 4))),
    list(list(1, 2), list(3, 4))
  )
})

test_that("asis_input_handler returns the value completely untouched", {
  expect_null(asis_input_handler(NULL))
  expect_identical(asis_input_handler(list(0, 100)), list(0, 100))
  records <- list(list(name = "a"), list(name = "b"))
  expect_identical(asis_input_handler(records), records)
})

test_that("both handlers are registered and dispatch through shiny", {
  # shiny:::applyInputHandler(name, val, session) splits the ":type" suffix,
  # looks up the registered handler, and calls it — i.e. the real runtime path.
  # It throws "No handler registered for type" if the handler is missing.
  expect_identical(
    shiny:::applyInputHandler(
      "x:shinyreact.default",
      list(list(a = 1L), list(b = 2L)),
      NULL
    ),
    list(list(a = 1L), list(b = 2L))
  )
  expect_identical(
    shiny:::applyInputHandler("y:shinyreact.asis", list(0, 100), NULL),
    list(0, 100)
  )
})
