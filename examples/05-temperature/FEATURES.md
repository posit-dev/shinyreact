# examples/05-temperature — behavior

Two linked thermometer sliders (°C and °F) with a server echo. The smallest
example of a client that computes locally *and* keeps the server in the loop.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Server (`app.py`, Express)

- one output, `display` → `{celsius, fahrenheit, zone}` `(test)`
- `fahrenheit` is `round(c * 9 / 5 + 32, 1)` — one decimal, so 20 °C → 68.0
  `(test)`
  - the client rounds to whole degrees, so the two disagree by design: 37 °C is
    `98.6` from the server and `99` on the client `(test)`
- `zone` thresholds, all inclusive upper bounds `(test)`
  - `c <= 0` → `"Freezing"`
  - `c <= 15` → `"Cold"`
  - `c <= 30` → `"Comfortable"`
  - otherwise → `"Hot"`
- before the client's first message, `input.celsius()` raises a silent
  exception, so `display` never renders — the `c is None` guard in `app.py` is
  unreachable from a real client `(test)`
- `[py]` only — this example has no R server
- the logic lives inside `app.py` next to `set_react_page()`, so it is not
  importable — `tests/test_display.py` drives the app itself with
  `shiny.testserver.test_server()` instead

## Client (`www/ui.js`)

- `useShinyInput("celsius", 20, {debounceMs: 0})` — the single source of truth;
  Fahrenheit is derived, never stored `(test)`
- renders `null` until `useShinyInitialized()` is true
- conversions are integer-rounded on the client `(test)`
  - `cToF(c) = round(c * 9/5 + 32)`
  - `fToC(f) = round((f - 32) * 5/9)`
  - so the client's headline reads whole degrees while the server echo shows
    one decimal — 37 °C is `99°F` on the client and `98.6°F` from the server
  - `fToC` is not a right inverse of `cToF`: the °F slider has more positions
    than the °C range can represent, so dragging it to 69 °F stores 21 °C and
    the display snaps back to 70 °F `(test)`
- zone label and color are computed **twice** — client-side in
  `zoneLabel`/`zoneColor` and server-side in `display` — using the same
  thresholds; only the client half is pinned by a test `(test)`
  - client colors: `#0dcaf0` Freezing, `#0d6efd` Cold, `#198754` Comfortable,
    `#dc3545` Hot
  - a threshold change on one side without the other is a visible divergence
- headline reads `"<c>°C = <f>°F"` with a colored `.temp-badge` next to it
- server echo line `"Server: <c>°C → <f>°F (<zone>)"` renders only once the
  `display` value has arrived `(test)`
- two `Thermometer` sliders, vertical stack of label / value / range input
  - Celsius: `min` -40, `max` 60
  - Fahrenheit: `min` -40, `max` 140 — the exact `cToF` image of the Celsius
    range, so neither slider can be dragged out of the other's range
  - both use `onInput` (not `onChange`), so the value updates while dragging
  - the max tick is rendered *above* the slider and the min tick below
- the Fahrenheit slider writes through `fToC` back into the same `celsius`
  input `(test)`
- no mount container in the page — the client appends its own `<div>` to
  `<body>`
