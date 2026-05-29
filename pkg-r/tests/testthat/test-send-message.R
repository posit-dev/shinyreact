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
  expect_identical(sent$message$type, "mod-notify")
  expect_identical(sent$message$data, list(text = "hi"))
})

test_that("send_message tolerates a session without ns()", {
  sent <- NULL
  fake_session <- list(
    sendCustomMessage = function(type, message) {
      sent <<- message
    }
  )
  send_message(fake_session, "notify", list(n = 1L))
  expect_identical(sent$type, "notify")
})
