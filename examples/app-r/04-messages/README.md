# app-r/04-messages

R port of `examples/app-py/04-messages`. Demonstrates server-to-client custom
messages: `shinyreact::send_message()` pushes `logEvent` messages every 2
seconds from an `observe()`/`invalidateLater()` loop, which the React
`useShinyMessageHandler("logEvent", ...)` hook consumes to display animated
toast notifications.
