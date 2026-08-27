# Automatic output dependency discovery (#146/#203). Python's Express-mode
# counterpart (inline harvest at page-generation time) is asserted in
# pkg-py/tests/test_page_dep_harvest.py; R must push post-flush instead, since
# the UI renders before server() runs.

fake_dep <- function(name, version = "1.0.0") {
  htmltools::htmlDependency(
    name = name,
    version = version,
    src = c(href = name),
    script = paste0(name, ".js")
  )
}

# A render function whose outputFunc attaches `dep`, standing in for e.g.
# plotly::renderPlotly() without the test dependency.
fake_render_fn <- function(dep) {
  shiny::createRenderFunction(
    function() "value",
    transform = function(value, session, name, ...) value,
    outputFunc = function(id) {
      htmltools::attachDependencies(htmltools::div(id = id), dep)
    }
  )
}

# Minimal stand-in for the slice of ShinySession that install_dep_discovery()
# touches: userData, onFlushed, getOutput, sendCustomMessage, and the private
# `.outputs` list.
fake_session <- function() {
  private <- new.env()
  private$.outputs <- list()
  flush_callbacks <- list()
  messages <- list()
  session <- new.env()
  session$userData <- new.env()
  session$.__enclos_env__ <- list(private = private)
  session$onFlushed <- function(callback, once = FALSE) {
    flush_callbacks[[length(flush_callbacks) + 1]] <<- callback
  }
  session$getOutput <- function(name) {
    attr(private$.outputs[[name]], "renderFunc", exact = TRUE)
  }
  session$sendCustomMessage <- function(type, message) {
    messages[[length(messages) + 1]] <<- list(type = type, message = message)
  }
  session$define_output <- function(name, render_fn) {
    obs <- structure(list(), renderFunc = render_fn)
    private$.outputs[[name]] <- obs
  }
  session$flush <- function() {
    for (callback in flush_callbacks) {
      callback()
    }
  }
  session$messages <- function() messages
  session
}

sent_dep_names <- function(msg) {
  vapply(msg$message, function(dep) dep$name, character(1))
}

test_that("discovery pushes new outputs' deps once per flush cycle", {
  session <- fake_session()
  expect_true(install_dep_discovery(session))

  session$define_output("plot1", fake_render_fn(fake_dep("fake-binding")))
  session$flush()
  msgs <- session$messages()
  expect_length(msgs, 1)
  expect_identical(msgs[[1]]$type, "shinyreact-deps")
  expect_identical(sent_dep_names(msgs[[1]]), "fake-binding")

  # No new outputs => no message on later flushes.
  session$flush()
  expect_length(session$messages(), 1)
})

test_that("discovery covers outputs registered after startup, without resends", {
  session <- fake_session()
  install_dep_discovery(session)

  session$define_output("a", fake_render_fn(fake_dep("binding-a")))
  session$flush()

  # A late-mounted output (e.g. module server inside an observer): its new
  # dep is pushed, the already-sent one is not.
  session$define_output("b", fake_render_fn(fake_dep("binding-a")))
  session$define_output("c", fake_render_fn(fake_dep("binding-c")))
  session$flush()

  msgs <- session$messages()
  expect_length(msgs, 2)
  expect_identical(sent_dep_names(msgs[[2]]), "binding-c")
})

test_that("dep-less outputs (renderText, reactive_output) push nothing", {
  session <- fake_session()
  install_dep_discovery(session)
  session$define_output("txt", shiny::renderText("hi"))
  session$define_output("react", reactive_output(42))
  session$flush()
  expect_length(session$messages(), 0)
})

test_that("install_dep_discovery() is idempotent per session", {
  session <- fake_session()
  expect_true(install_dep_discovery(session))
  expect_false(install_dep_discovery(session))
  session$define_output("a", fake_render_fn(fake_dep("binding-a")))
  session$flush()
  expect_length(session$messages(), 1)
})

test_that("install_dep_discovery() no-ops without a real session", {
  expect_false(install_dep_discovery(NULL))
  expect_false(install_dep_discovery(list(userData = list())))
})

test_that("input handlers install discovery", {
  session <- fake_session()
  default_input_handler(list(), session = session)
  expect_true(session$userData[[".shinyreact_dep_discovery"]])

  session2 <- fake_session()
  asis_input_handler(1, session = session2)
  expect_true(session2$userData[[".shinyreact_dep_discovery"]])
})
