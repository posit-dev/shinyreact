# examples/10-bookmarking — behavior

Bookmark and restore React input state through the URL query string. Three
inputs, a bookmark button, and a server echo.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## App wiring (`app.py`, Core)

- `ReactApp(server, bookmark_store="url")`
  - `ReactApp` discovers `www/ui.js` + `www/ui.css` next to the module and
    builds the UI **per request**, which is what makes restore work with no
    further wiring — a UI object built once could not carry a per-request
    restore payload
- output `greeting` (`reactive_output`) → `text='<txt>' num=<num>
  checked=<yes|no>`
  - `checked` is the string `"yes"` / `"no"`, not a boolean
  - `txt` is `repr`'d, so it is quoted
- `@reactive.effect` + `@reactive.event(input.bookmark_clicks,
  ignore_init=True)` → `await session.bookmark()`, which rewrites the browser
  URL
- `[py]` only — this example has no R server

## Restore path

- `page_react()`'s page entry emits a `<script type="application/json"
  id="shinyreact-config">` tag carrying the protocol version and the restored
  input values
- the bundle seeds `useShinyInput` initial values from that tag; the config tag
  is the only delivery channel (`window.shinyreact._restore` is a write-only
  DevTools sentinel)
- so opening a bookmarked URL renders the restored values on the *first* paint,
  with no flash of the defaults
- restored values appear in the page source — a documented property of the
  mechanism, not a leak to fix here

## Client (`www/ui.js`)

- wrapped in an IIFE and written in ES5 style (`var`, `function`) — the only
  example that is; it is otherwise the same no-build pattern
- does **not** gate on `useShinyInitialized()` — it renders immediately
- inputs, all with default `debounceMs`
  - `useShinyInput("txt", "")` → `<input type="text">` `(test)`
  - `useShinyInput("num", 0)` → `<input type="number">`, sends
    `Number(e.target.value)` `(test)`
  - `useShinyInput("chk", false)` → `<input type="checkbox">`, sends
    `e.target.checked` `(test)`
  - the hook tuples are kept whole (`txt[0]` / `txt[1]`) rather than
    destructured
- bookmark button
  - `useSetShinyInput("bookmark_clicks", 0, {debounceMs: 0, priority:
    "event"})` — write-only, the client never reads the count back
  - the count lives in a `useRef` and is incremented per click, so each click
    is a distinct event value `(test)`
  - carries `data-testid="bookmark-btn"` for the Playwright suite
- the echo card renders `"Server says: <greeting>"`, empty string before the
  first value
- no mount container in the page — the client appends its own `<div>` to
  `<body>`

## Covered elsewhere

- the restore mechanism itself (config-tag shape, escaping, protocol version)
  is claimed in the repo-root `FEATURES.md` and pinned by
  `pkg-py/tests/test_bookmark_restore.py`,
  `pkg-py/tests/playwright/test_bookmark_restore.py`, and the R/JS mirrors
