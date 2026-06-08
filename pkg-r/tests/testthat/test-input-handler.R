test_that("default_input_handler preserves arrays of objects as a list of records", {
  records <- list(
    list(name = "a", size = 1L),
    list(name = "b", size = 2L)
  )
  expect_identical(default_input_handler(records), records)
  # A partially-named child is not a proper record array -> falls through to unlist.
  expect_equal(
    default_input_handler(list(list(a = 1L, 2L))),
    c(a = 1L, 2L)
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

test_that("default_input_handler returns NULL for an empty array and flattens nested arrays", {
  expect_null(default_input_handler(list()))
  expect_equal(
    default_input_handler(list(list(1, 2), list(3, 4))),
    c(1, 2, 3, 4)
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
