# Package index

## Pages

Bootstrap a React client from the app file. Start with
[`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md);
reach for the others only when your app owns its own HTML document or
you are assembling a page by hand.

- [`page_react()`](https://posit-dev.github.io/shinyreact/r/reference/page_react.md)
  : Create a React page from conventional assets — no HTML file required

- [`page_react_html()`](https://posit-dev.github.io/shinyreact/r/reference/page_react_html.md)
  :

  Serve a React `index.html` document (the `ui.tsx` pattern)

- [`page_bare()`](https://posit-dev.github.io/shinyreact/r/reference/page_bare.md)
  : Bare HTML page with Shiny dependencies

- [`page_react_dep()`](https://posit-dev.github.io/shinyreact/r/reference/page_react_dep.md)
  : HTML dependency for a downstream package's own JS/CSS bundle

## Outputs

Publish JSON to `useShinyOutputValue()` hooks.

- [`reactive_output()`](https://posit-dev.github.io/shinyreact/r/reference/reactive_output.md)
  :

  Publish a reactive value to a shinyreact client (the `ui.tsx` pattern)

## Messaging

Push messages to `useShinyMessageHandler()` hooks.

- [`send_message()`](https://posit-dev.github.io/shinyreact/r/reference/send_message.md)
  : Send a custom message to client React components

## Testing

Record the wire payloads a browser test observes.

- [`wire_tap()`](https://posit-dev.github.io/shinyreact/r/reference/wire_tap.md)
  : Tap the websocket wire of a shinytest2 app

## Package

- [`shinyreact`](https://posit-dev.github.io/shinyreact/r/reference/shinyreact-package.md)
  [`shinyreact-package`](https://posit-dev.github.io/shinyreact/r/reference/shinyreact-package.md)
  : shinyreact: Shiny UI Infrastructure for Client-Side React Rendering
