test_that("restore_script_tag returns NULL with no restore values", {
  testthat::local_mocked_bindings(
    .restore_input_values = function() list()
  )
  expect_null(restore_script_tag())
})

test_that("restore_script_tag emits a JSON.parse restore script", {
  testthat::local_mocked_bindings(
    .restore_input_values = function() list(name = "Alice", n = 3L)
  )
  tagobj <- restore_script_tag()
  html <- as.character(tagobj)
  expect_match(html, "window\\.shinyreact\\._restore = JSON\\.parse\\(")
  expect_match(html, "Alice")
})

test_that("restore script payload survives __proto__ keys", {
  testthat::local_mocked_bindings(
    .restore_input_values = function() stats::setNames(list("x"), "__proto__")
  )
  html <- as.character(restore_script_tag())
  expect_match(html, "__proto__")
})
