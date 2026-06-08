# Parse a single-node walker result to JSON-structure for assertions.
wire1 <- function(x) {
  parts <- serialize_ui(x)
  jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
}

test_that("a plain string becomes a text node", {
  expect_identical(wire1("hello"), list(type = "text", value = "hello"))
})

test_that("a number becomes a stringified text node", {
  expect_identical(wire1(42L), list(type = "text", value = "42"))
  expect_identical(wire1(3.5), list(type = "text", value = "3.5"))
})

test_that("HTML() becomes an html node", {
  expect_identical(
    wire1(htmltools::HTML("<b>x</b>")),
    list(type = "html", html = "<b>x</b>")
  )
})

test_that("a shiny.tag becomes a tag node with translated attrs", {
  out <- wire1(htmltools::tags$span("hi", class = "x", `for` = "y"))
  expect_identical(out$type, "tag")
  expect_identical(out$name, "span")
  expect_identical(out$props$className, "x")
  expect_identical(out$props$htmlFor, "y")
  expect_identical(out$children, list(list(type = "text", value = "hi")))
})

test_that("a tagList of siblings yields an array payload", {
  parts <- serialize_ui(htmltools::tagList(
    htmltools::tags$div("a"),
    htmltools::tags$div("b")
  ))
  parsed <- jsonlite::fromJSON(
    jsonlite::toJSON(parts$payload, auto_unbox = FALSE),
    simplifyVector = FALSE
  )
  expect_length(parsed, 2)
  expect_identical(parsed[[1]]$name, "div")
})

test_that("html dependencies are harvested, not emitted as nodes", {
  dep <- htmltools::htmlDependency("d", "1.0.0", src = c(href = "x"))
  parts <- serialize_ui(htmltools::tagList(htmltools::tags$div("a"), dep))
  expect_length(parts$deps, 1)
  expect_identical(parts$deps[[1]]$name, "d")
  expect_identical(parts$payload$name, jsonlite::unbox("div"))
})

test_that("NULL and empty content yield an empty payload", {
  expect_identical(serialize_ui(NULL)$payload, list())
  expect_identical(serialize_ui(htmltools::tagList())$payload, list())
})

test_that("empty tag props serialize as an object, children as an array", {
  parts <- serialize_ui(htmltools::tags$hr())
  txt <- jsonlite::toJSON(parts$payload, auto_unbox = FALSE)
  expect_match(txt, '"props":\\{\\}')
  expect_match(txt, '"children":\\[\\]')
})

test_that("an unknown object with no as.tags method errors", {
  obj <- structure(list(), class = "nomethod_xyz")
  expect_error(serialize_ui(obj))
})
