# Runs the example apps' own R tests, which live beside each app in
# examples/<app>/tests/testthat/ -- the layout shiny::runTests() and
# shinytest2::test_app() expect, so a user sitting in the app can run them
# without this file.
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

# The examples that ship an app.R, copied into inst/examples-shiny/ by
# `make update-examples` so the installed package can reach them via
# system.file() (see test-wire-tap.R). This is the drift guard on those copies;
# mirrors test-skills.R's guard on the shipped skills.
shipped_r_examples <- c("01-hello", "07-plotly")

test_that("R example apps are installed at examples-shiny/<name>", {
  for (name in shipped_r_examples) {
    expect_true(nzchar(system.file(
      "examples-shiny",
      name,
      "app.R",
      package = "shinyreact"
    )))
  }
})

test_that("shipped R example apps match examples/", {
  skip_if_not(dir.exists(examples_dir), "not running from the repo")

  tree <- function(root) {
    files <- sort(list.files(root, recursive = TRUE))
    stats::setNames(
      lapply(files, function(f) readLines(file.path(root, f))),
      files
    )
  }

  for (name in shipped_r_examples) {
    # Only app.R + www/ are copied; the example's README/FEATURES/tests and its
    # Python siblings stay in examples/.
    src <- tree(file.path(examples_dir, name))
    src <- src[grepl("^(app\\.R|www/)", names(src))]
    expect_equal(
      tree(system.file("examples-shiny", name, package = "shinyreact")),
      src,
      info = "run `make update-examples`"
    )
  }
})

if (dir.exists(examples_dir)) {
  example_tests <- list.files(
    examples_dir,
    pattern = "^test-.*\\.R$",
    recursive = TRUE,
    full.names = TRUE
  )
  # Only files under examples/<app>/tests/testthat/, the layout
  # shiny::runTests() and shinytest2::test_app() expect.
  example_tests <- example_tests[
    basename(dirname(example_tests)) == "testthat"
  ]
  # Source from the app's own tests/testthat/, as shinytest2::test_app() would,
  # so test_path("../../") -- AppDriver$new()'s default app_dir -- is the app.
  for (file in example_tests) {
    withr::with_dir(dirname(file), source(basename(file), local = TRUE))
  }
}
