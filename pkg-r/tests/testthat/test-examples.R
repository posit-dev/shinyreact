# Runs the example apps' own R tests, which live beside each app in
# examples/<app>/tests/test-*.R.
#
# They are the examples' tests, not the package's -- but a package change that
# breaks an example should fail here rather than be discovered later, which is
# the same reason pkg-js's vitest config includes examples/*/tests and pytest's
# testpaths includes examples/.
#
# Skipped when examples/ is not reachable, which is the case for R CMD check
# against an installed package.

examples_dir <- normalizePath(
  file.path(testthat::test_path(), "..", "..", "..", "examples"),
  mustWork = FALSE
)

test_that("the example apps' own tests are reachable", {
  skip_if_not(
    dir.exists(examples_dir),
    "examples/ not present (installed package)"
  )
  expect_true(dir.exists(examples_dir))
})

if (dir.exists(examples_dir)) {
  example_tests <- list.files(
    examples_dir,
    pattern = "^test-.*\\.R$",
    recursive = TRUE,
    full.names = TRUE
  )
  # Only files under examples/<app>/tests/.
  example_tests <- example_tests[
    basename(dirname(example_tests)) == "tests"
  ]
  for (file in example_tests) {
    source(file, local = TRUE)
  }
}
