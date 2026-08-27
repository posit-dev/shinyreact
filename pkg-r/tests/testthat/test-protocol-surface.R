# Guards the client/server boundary surface against silent growth.
#
# protocol/surface.json lists every name that crosses the boundary, next to the
# protocol version that describes it. This asserts the R side matches: the input
# handlers shinyreact registers with shiny, the custom message types it sends,
# and the version constant.
#
# It exists because the surface already grew unnoticed -- #221 added
# `shinyreact.init` and `shinyreact-deps` while all three protocol constants
# still documented "exactly three" boundary shapes (issue #232). Mirrors
# pkg-py/tests/test_protocol_surface.py and
# pkg-js/src/__tests__/protocol-surface.test.ts.

surface <- function() {
  path <- testthat::test_path("..", "..", "..", "protocol", "surface.json")
  skip_if_not(file.exists(path), "protocol/surface.json not found")
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

pkg_r_sources <- function() {
  dir <- testthat::test_path("..", "..", "R")
  vapply(
    list.files(dir, pattern = "[.]R$", full.names = TRUE),
    brio::read_file,
    character(1)
  )
}

test_that("registered input handlers match the manifest", {
  # Read from shiny's registry rather than a list in this file, so a new
  # registerInputHandler() call in .onLoad() shows up here whether or not
  # anyone remembered this test.
  registry <- shiny:::inputHandlers
  registered <- sort(grep("^shinyreact[.]", registry$keys(), value = TRUE))

  expect_identical(
    registered,
    sort(names(surface()$inputHandlers)),
    info = paste(
      "shinyreact's registered input handlers no longer match",
      "protocol/surface.json. Add the new name there and decide whether the",
      "protocol version must change (#232)."
    )
  )
})

test_that("custom message types match the manifest", {
  # Source scan: the type is a literal at the send site.
  sources <- pkg_r_sources()
  found <- unlist(regmatches(
    sources,
    gregexpr('sendCustomMessage\\(\\s*"[^"]+"', sources, perl = TRUE)
  ))
  found <- unique(sub('.*"([^"]+)"$', "\\1", found))

  expect_length(setdiff(found, names(surface()$customMessages)), 0L)
})

test_that("the config tag id matches the manifest", {
  sources <- pkg_r_sources()
  found <- unlist(regmatches(
    sources,
    gregexpr('id = "shinyreact[^"]*"', sources, perl = TRUE)
  ))
  found <- unique(sub('.*"([^"]+)"$', "\\1", found))

  expect_gt(length(found), 0L)
  expect_length(setdiff(found, names(surface()$domIds)), 0L)
})

test_that("the protocol version matches the manifest", {
  expect_identical(.protocol_version, surface()$protocolVersion)
})
