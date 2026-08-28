# examples/08-input-handler — behavior

`useShinyInput(..., {type: "shiny.datetime"})`: the client sends a number, the
server reads a `datetime`. The smallest demonstration of routing an input
through a Shiny input handler.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Wire

- the hook's `type` appends `:shiny.datetime` to the wire id, so the value
  arrives as `when:shiny.datetime` and Shiny's built-in handler coerces it
  before `input.when()` resolves
- opting into a `type` bypasses shinyreact's own `shinyreact.default` handler —
  the value is handled by Shiny's registry, not by shinyreact
- the id/type pairing is a per-id contract: a second mount of `"when"` without
  `type` (or with a different one) throws at hook mount

## Server (`app.py`, Express)

- one output, `when_info` → `"<type name> → <repr>"`, e.g.
  `"datetime → datetime.datetime(2026, 8, 28, 12, 0, tzinfo=...)"`
- `input.when()` is `None` before the first client message → returns `"—"`
  (em dash)
- the example asserts nothing about the timezone the handler attaches
- `[py]` only — this example has no R server; R's handler registry has no
  `shiny.datetime` equivalent, so the client is not portable as written

## Client (`www/ui.js`)

- renders `null` until `useShinyInitialized()` is true
- `useShinyInput("when", Math.floor(Date.now() / 1000), {type:
  "shiny.datetime", debounceMs: 0})` `(test)`
  - the default is unix **seconds**, not milliseconds — captured once at first
    mount
  - `debounceMs: 0`, so each keystroke in the number field is sent immediately
- a `<input type="number">` bound to that value; `onChange` sends
  `Number(e.target.value)` `(test)`
  - an empty field yields `Number("") === 0`, so clearing the box sends the
    unix epoch rather than nothing `(test)`
- shows the server's echo in a `<code>`, or `"…"` before the first value
- explanatory copy names `shiny.datetime`, `datetime`, and `input.when()`
  inline in `<code>` elements
- no mount container in the page — the client appends its own `<div>` to
  `<body>`
