test_that("as.tags.shinyreact_node emits a static mount with inline JSON", {
  tagobj <- htmltools::as.tags(node("Card", props = list(title = "Hi")))
  html <- as.character(tagobj)
  expect_match(html, 'class="shinyreact-static"')
  expect_match(html, 'type="application/json"')
  expect_match(html, "Card")
  deps <- htmltools::findDependencies(tagobj)
  expect_true(any(vapply(deps, function(d) d$name == "shinyreact", logical(1))))
})

test_that("static mount escapes < to prevent </script> breakout", {
  tagobj <- htmltools::as.tags(node(
    "Card",
    htmltools::HTML("</script><b>x</b>")
  ))
  html <- as.character(tagobj)
  expect_match(html, "u003c", fixed = TRUE)
})

test_that("static mount surfaces harvested dependencies", {
  dep <- htmltools::htmlDependency("extra", "1.0.0", src = c(href = "x"))
  tagobj <- htmltools::as.tags(node("Card", htmltools::tags$div("a"), dep))
  deps <- htmltools::findDependencies(tagobj)
  names <- vapply(deps, function(d) d$name, character(1))
  expect_true(all(c("shinyreact", "extra") %in% names))
})
