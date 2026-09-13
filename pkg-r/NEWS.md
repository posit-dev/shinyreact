# shinyreact 0.1.0

* Initial CRAN release. shinyreact is the server-side plumbing for the
  `ui.tsx` pattern: the UI is a React client you own, and the Shiny server
  contains only reactive computation. It ships no UI components.

* Dependencies of traditional Shiny outputs hosted inside a React tree are
  discovered automatically and pushed to the client after each flush, so the
  `ShinyOutput` component works with zero configuration.

* Bookmark restore values reach the client through the `#shinyreact-config`
  script tag, and the client asserts the wire-protocol major version at boot.

* `page_react()` serves `www/ui.js` (and `www/ui.css`, if present) as the
  whole page, with no HTML file required. `page_react_html()` serves a
  complete `index.html` that you own, `page_bare()` builds a page with no
  Bootstrap, and `page_react_dep()` wraps an app's own bundle as an
  `htmlDependency()` versioned by its mtime.

* `reactive_output()` publishes any JSON-serializable value to the client's
  `useShinyOutputValue()` hook, with no UI placeholder.

* `send_message()` sends a custom message to the client's
  `useShinyMessageHandler()` hook, namespaced to the current module.

* `shinyreact.default` and `shinyreact.asis` input handlers give R and Python
  the same view of the JSON a `useShinyInput()` hook sends: records stay
  lists, `[]` stays `list()`, and nested arrays keep their shape.

* `wire_tap()` reads the websocket payloads a shinytest2 `AppDriver` recorded,
  so tests can assert the exact inputs, outputs, and messages that crossed the
  wire.
