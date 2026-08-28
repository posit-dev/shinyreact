# Runner for this example app's own tests, in the layout `shiny::runTests()`
# and `shinytest2::test_app()` expect. From the app directory:
#
#   Rscript -e 'shiny::runTests()'
#
# The Python and JS tests for this app live beside testthat/ and are run with
# pytest and vitest; see this example's README.
library(testthat)

test_dir("testthat")
