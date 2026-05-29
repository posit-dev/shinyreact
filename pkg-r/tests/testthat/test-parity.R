# Fixtures are copies of pkg-py/tests/fixtures/wire_format/ — keep in sync.
# (A make target verifies the copy matches the Python source.)

fixture <- function(name) {
  jsonlite::fromJSON(
    testthat::test_path("fixtures", "wire_format", paste0(name, ".json")),
    simplifyVector = FALSE
  )
}

# Parse R's serialized wire output back into a list structure.
r_wire <- function(value) {
  jsonlite::fromJSON(
    shinyreact:::.wire_json(to_spec(value)),
    simplifyVector = FALSE
  )
}

# Normalize a parsed wire structure so element-map key ORDER does not matter
# (JSON object order is insignificant; R sorts root-first, Python post-order).
# `children` arrays inside elements are left untouched (their order matters).
normalize <- function(x) {
  if (is.list(x) && !is.null(x$elements)) {
    x$elements <- x$elements[order(names(x$elements))]
  }
  x
}

expect_parity <- function(value, fixture_name) {
  expect_equal(normalize(r_wire(value)), normalize(fixture(fixture_name)))
}

test_that("single_element matches Python", {
  expect_parity(node("Card", props = list(title = "Hello")), "single_element")
})

test_that("nested_tree matches Python", {
  expect_parity(
    node(
      "Card",
      node("Divider"),
      node("Text", props = list(value = "x")),
      props = list(title = "Hi")
    ),
    "nested_tree"
  )
})

test_that("empty_children matches Python", {
  expect_parity(node("Divider"), "empty_children")
})

test_that("multi_props matches Python", {
  expect_parity(
    node(
      "TextInput",
      props = list(
        input_id = "name",
        label = "Name",
        placeholder = "..."
      )
    ),
    "multi_props"
  )
})

test_that("raw_value passes through unchanged", {
  expect_equal(
    jsonlite::fromJSON(
      shinyreact:::.wire_json(list(key = "value", count = 42L)),
      simplifyVector = FALSE
    ),
    fixture("raw_value")
  )
})
