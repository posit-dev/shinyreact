# Fixtures are copies of pkg-py/tests/fixtures/wire_format/ — kept in sync by
# `make r-check-fixtures`. Python is the source of truth; R must reproduce the
# same wire tree (compared semantically; whitespace/format-insignificant).

fixture <- function(name) {
  jsonlite::fromJSON(
    testthat::test_path("fixtures", "wire_format", paste0(name, ".json")),
    simplifyVector = FALSE
  )
}

r_wire <- function(value) {
  parts <- serialize_ui(value)
  jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
}

test_that("react_node matches Python", {
  expect_equal(
    r_wire(node("Card", props = list(title = "Hi"))),
    fixture("react_node")
  )
})

test_that("tag_child matches Python (attr translation)", {
  expect_equal(
    r_wire(node("Card", htmltools::tags$span("hi", class = "x"))),
    fixture("tag_child")
  )
})

test_that("text_child matches Python (number coercion)", {
  expect_equal(
    r_wire(node("Card", "plain text", 42L)),
    fixture("text_child")
  )
})

test_that("html_child matches Python", {
  expect_equal(
    r_wire(node("Card", htmltools::HTML("<b>x</b>"))),
    fixture("html_child")
  )
})

test_that("mixed_tree matches Python", {
  expect_equal(
    r_wire(node(
      "Card",
      node("Divider"),
      htmltools::tags$span("hi", class = "x"),
      "text",
      props = list(title = "Hi")
    )),
    fixture("mixed_tree")
  )
})

test_that("taglist_root matches Python (sibling-list payload)", {
  expect_equal(
    r_wire(htmltools::tagList(
      node("Card"),
      htmltools::tags$div("d", id = "root2")
    )),
    fixture("taglist_root")
  )
})

test_that(".ATTR_MAP matches Python's _ATTR_MAP", {
  # The HTML-attribute -> React-prop map must stay identical across languages.
  # Python commits attr_map.json from its _ATTR_MAP; R asserts its .ATTR_MAP
  # against the same fixture (order-insensitive). Keeps the two from drifting.
  expected <- unlist(jsonlite::fromJSON(
    testthat::test_path("fixtures", "wire_format", "attr_map.json"),
    simplifyVector = FALSE
  ))
  expect_mapequal(shinyreact:::.ATTR_MAP, expected)
})
