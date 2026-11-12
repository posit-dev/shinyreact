# Changelog

## Unreleased

* `useShinyOutputValue()` and its sibling hooks no longer leak a Shiny output
  binding each time a component unmounts. Before, every mount/unmount cycle
  (e.g. switching tabs) added a stale binding, so Shiny's "Duplicate output
  IDs were found" warning grew and the console logged `Output <id> not found`
  (#330).

* Bookmarking on a `page_react()` page needs an app-registered callback such as
  `session.bookmark.on_bookmarked(session.bookmark.update_query_string)`. Without one, Shiny shows the bookmark URL in a Bootstrap modal, which
  a page with no Bootstrap cannot open, so `session.bookmark()` failed with
  `$(...).modal is not a function`. The browser console now logs a
  `[shinyreact]` error naming the fix instead (#326).

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
