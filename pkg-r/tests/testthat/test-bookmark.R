test_that("config_script_tag omits restore with no restore values", {
  # The tag is still emitted (it carries the protocol version), but has no
  # "restore" member. Mirrors Python's
  # test_config_script_tag_no_context_omits_restore.
  testthat::local_mocked_bindings(
    .restore_input_values = function() list()
  )
  html <- as.character(config_script_tag())
  config <- extract_config(html)
  expect_identical(config, list(protocolVersion = .protocol_version))
})

test_that("config_script_tag emits a JSON config tag with restore", {
  testthat::local_mocked_bindings(
    .restore_input_values = function() list(name = "Alice", n = 3L)
  )
  html <- as.character(config_script_tag())
  expect_match(html, 'type="application/json"', fixed = TRUE)
  expect_match(html, 'id="shinyreact-config"', fixed = TRUE)
  config <- extract_config(html)
  expect_identical(config$protocolVersion, .protocol_version)
  expect_identical(config$restore, list(name = "Alice", n = 3L))
})

test_that("config payload survives __proto__ keys", {
  testthat::local_mocked_bindings(
    .restore_input_values = function() stats::setNames(list("x"), "__proto__")
  )
  html <- as.character(config_script_tag())
  expect_match(html, "__proto__")
})

test_that("protocol version matches the JS and Python declarations", {
  # .protocol_version is one contract declared in three languages; this
  # parity test pins all three to the same string. Mirrors Python's
  # test_protocol_version_matches_js_and_r.
  repo_root <- file.path(testthat::test_path(), "..", "..", "..")
  js_src <- file.path(repo_root, "pkg-js", "src", "shiny-react", "config.ts")
  py_src <- file.path(repo_root, "pkg-py", "src", "shinyreact", "_protocol.py")
  skip_if_not(
    file.exists(js_src) && file.exists(py_src),
    "monorepo sources not available (installed-package run)"
  )
  extract_version <- function(path, pattern) {
    src <- paste(readLines(path, warn = FALSE), collapse = "\n")
    m <- regmatches(src, regexec(pattern, src))[[1]]
    expect_length(m, 2L)
    m[[2]]
  }
  expect_identical(
    extract_version(js_src, 'PROTOCOL_VERSION = "([^"]+)"'),
    .protocol_version
  )
  expect_identical(
    extract_version(py_src, 'PROTOCOL_VERSION = "([^"]+)"'),
    .protocol_version
  )
})
