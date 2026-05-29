test_that(".wire_json unboxes scalars and emits arrays for children", {
  s <- to_spec(node("Card", node("Divider")))
  txt <- shinyreact:::.wire_json(s)
  parsed <- jsonlite::fromJSON(txt, simplifyVector = FALSE)
  expect_identical(parsed$root, "auto_001")
  expect_identical(parsed$elements$auto_001$type, "Card")
  expect_identical(parsed$elements$auto_001$children, list("auto_002"))
  expect_identical(parsed$elements$auto_002$children, list())
})

test_that(".wire_json emits empty props as a JSON object, not array", {
  s <- to_spec(element("Divider"))
  txt <- shinyreact:::.wire_json(s)
  expect_match(txt, '"props":\\{\\}')
})

test_that(".wire_json round-trips a string value unchanged", {
  txt <- shinyreact:::.wire_json("HELLO")
  expect_identical(jsonlite::fromJSON(txt), "HELLO")
})
