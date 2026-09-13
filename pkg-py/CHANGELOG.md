# Changelog

## 0.1.0

* Initial PyPI release.

* Server-side plumbing for the `ui.tsx` pattern: the UI is a React client you
  own, and the Shiny server contains only reactive computation.
  `@reactive_output` sends JSON to `useShinyOutputValue()` hooks,
  `send_message()` reaches `useShinyMessageHandler()`, and `set_react_page()`
  (Express), `ReactApp` (Core), `page_react()`, `page_react_html()`,
  `page_bare()`, and `page_react_dep()` bootstrap the client.

* Renderer dependencies of traditional Shiny outputs hosted inside a React tree
  are discovered automatically, so `ShinyOutput` works with zero configuration.

* Bookmark restore is delivered through the `#shinyreact-config` script tag,
  and the client asserts the wire-protocol major version at boot.

* `shinyreact.default` and `shinyreact.asis` input handlers give Python and R
  the same view of the JSON a hook sends.

* `shinyreact.playwright.WireTap` records the Shiny websocket for end-to-end
  tests.
