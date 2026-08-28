# examples/06-data-frame — behavior

A traditional `@render.data_frame` output living inside a React tree, driven by
a React slider. Shows that `ShinyOutput` needs no server-side placeholder.

Every leaf below is one checkable claim about this app. `[py]` / `[r]` / `[js]`
mark a claim that holds only in that language; `(test)` marks a claim pinned by
a unit test; `(verify)` marks a claim not yet checked against the code.

## Server (`app.py`, Express)

- output `greeting` (`reactive_output`) → `"Showing N rows"`
  - no singular special case: `N = 1` reads `"Showing 1 rows"`
- output `my_table` (`@render.data_frame`) → a pandas DataFrame with `N` rows
  and columns `Name` / `Value` / `Category`
  - `Name` is `"Item 1" … "Item N"`, 1-based
  - `Value` is `10, 20, … 10N`
  - `Category` is `"A"` on even `i`, `"B"` on odd `i` — so row 1 is `B`
- there is no `ui.output_data_frame("my_table")` anywhere; the element the
  binding attaches to is created by the client
- `set_react_page()` discovers the data-frame renderer's `HTMLDependency` and
  injects it into `<head>` — this is the behavior the example exists to
  demonstrate
- `[py]` only — this example has no R server

## Client (`www/ui.js`)

- renders `null` until `useShinyInitialized()` is true
- `useShinyInput("row_count", 5)` — `<input type="range">`, `min` 1, `max` 20,
  `id="row-count"`, default 100 ms debounce `(test)`
- `<ShinyOutput id="my_table" tagName="shiny-data-frame"/>` `(test)`
  - renders exactly the `<shiny-data-frame id="my_table">` element the binding
    expects, and runs `Shiny.bindAll` / `unbindAll` around it
  - no `className` is passed — the custom element carries the binding
- the greeting paragraph renders the raw `greeting` value (empty before the
  first value arrives)
- the slider's current value is echoed next to it as plain text
- no mount container in the page — the client appends its own `<div>` to
  `<body>`
