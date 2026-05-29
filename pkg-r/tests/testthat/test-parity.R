# Fixtures are copies of pkg-py/tests/fixtures/wire_format/ — keep in sync.
# (A make target verifies the copy matches the Python source.)
# NOTE: This test file is rewritten in RW Task 5 to use the new node() +
# serialize_ui() model. All tests below are skipped until then.

fixture <- function(name) {
  jsonlite::fromJSON(
    testthat::test_path("fixtures", "wire_format", paste0(name, ".json")),
    simplifyVector = FALSE
  )
}

test_that("single_element matches Python", {
  skip("rewritten in RW Task 5")
})

test_that("nested_tree matches Python", {
  skip("rewritten in RW Task 5")
})

test_that("empty_children matches Python", {
  skip("rewritten in RW Task 5")
})

test_that("multi_props matches Python", {
  skip("rewritten in RW Task 5")
})

test_that("raw_value passes through unchanged", {
  skip("rewritten in RW Task 5")
})
