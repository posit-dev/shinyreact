test_that("send_message sends a namespaced shinyReactMessage", {
  sent <- NULL
  fake_session <- list(
    ns = function(x) paste0("mod-", x),
    sendCustomMessage = function(type, message) {
      sent <<- list(type = type, message = message)
    }
  )
  send_message(fake_session, "notify", list(text = "hi"))
  expect_identical(sent$type, "shinyReactMessage")
  expect_identical(sent$message$id, "mod-notify")
  expect_identical(sent$message$data, list(text = "hi"))
})

test_that("send_message errors on a session without ns()", {
  # Previously fell back to sending an un-namespaced id, which no
  # module-scoped handler would match -- silent misdelivery (#184).
  fake_session <- list(sendCustomMessage = function(type, message) NULL)
  expect_error(
    send_message(fake_session, "notify", list(n = 1L)),
    "must be a Shiny session"
  )
})

test_that("send_message uses the top-level session namespace unchanged", {
  # A real top-level ShinySession's ns() is NS(NULL, id), i.e. identity.
  sent <- NULL
  fake_session <- list(
    ns = function(x) shiny::NS(NULL, x),
    sendCustomMessage = function(type, message) sent <<- message
  )
  send_message(fake_session, "notify", list(n = 1L))
  expect_identical(sent$id, "notify")
})
