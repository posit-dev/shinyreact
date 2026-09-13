# shinyreact 0.1.0

* Initial CRAN release.

* Server-side plumbing for the `ui.tsx` pattern: the UI is a React client you
  own, and the Shiny server contains only reactive computation.
  `reactive_output()` sends JSON to `useShinyOutputValue()` hooks,
  `send_message()` reaches `useShinyMessageHandler()`, and `page_react()` /
  `page_react_html()` / `page_bare()` / `page_react_dep()` bootstrap the
  client.

* Automatic renderer-dependency discovery: dependencies of traditional Shiny
  outputs hosted inside a React tree are pushed to the client after each
  flush, so `ShinyOutput` works with zero configuration.

* Bookmark restore is delivered through the `#shinyreact-config` script tag,
  and the client asserts the wire-protocol major version at boot.

* `shinyreact.default` and `shinyreact.asis` input handlers give R and Python
  the same view of the JSON a hook sends.
